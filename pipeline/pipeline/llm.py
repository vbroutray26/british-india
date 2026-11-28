"""LLMClient: one interface for every model provider (spec §8.7, §9.3, §9.4; D-04).

- Providers are adapters behind `LLMClient._complete(system, user) -> str`. Gemini first (owner's choice,
  2026-11-27); others can be added without touching callers.
- `Runner` adds what every call needs: a cache keyed by sha256(system + user + prompt_version + model), so no
  call is ever paid for twice; a daily budget per provider that stops at 90% of the known limit; and backoff
  with jitter on 429/503, then resume.
- Keys come from the environment or pipeline/.env (gitignored). They are never logged or written anywhere.
- Only gazetteer text is sent: no personal data (§9.2).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import random
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from pipeline.util import CONFIG_DIR, INTERIM_DIR, REPO_ROOT, log, read_yaml, sha256_text

LG = log("LLM")
STOP_AT = 0.9  # stop at 90% of a provider's known daily limit (§9.4)


class MissingKey(RuntimeError):
    pass


class RateLimited(RuntimeError):
    """429 or 503: back off and try again."""


class BudgetExhausted(RuntimeError):
    """The day's allowance is (nearly) spent: pause until it resets (§9.4)."""


class LLMClient:
    provider = "base"
    model = ""

    def _complete(self, system: str, user: str) -> str:  # pragma: no cover - adapters implement it
        raise NotImplementedError


def _key_from(env_name: str, env_file: Path | None) -> str | None:
    if os.environ.get(env_name):
        return os.environ[env_name]
    if env_file and env_file.exists():
        for line in env_file.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == env_name and v.strip():
                return v.strip().strip('"').strip("'")
    return None


class GeminiClient(LLMClient):
    """Google Gemini API (generateContent), temperature 0, JSON output."""

    provider = "gemini"
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, model: str, env_file: Path | None = REPO_ROOT / "pipeline" / ".env", timeout: float = 240):
        key = _key_from("GEMINI_API_KEY", env_file)
        if not key:
            raise MissingKey("GEMINI_API_KEY is not set (environment or pipeline/.env)")
        self._key = key
        self.model = model
        self.timeout = timeout

    def _complete(self, system: str, user: str) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        req = urllib.request.Request(self.URL.format(model=self.model), data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": self._key})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code == 429 and b"PerDay" in body:  # the day's free quota is spent: retrying cannot help
                raise BudgetExhausted(f"{self.model}: daily quota spent (HTTP 429); resumes after the reset") from None
            if e.code in (429, 500, 503, 504):
                raise RateLimited(f"HTTP {e.code}") from None
            raise RuntimeError(f"Gemini HTTP {e.code}: {body[:300]!r}") from None
        except (TimeoutError, urllib.error.URLError, ConnectionError) as e:  # transient: back off and retry
            raise RateLimited(f"{type(e).__name__}: {e}") from None
        parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)


class Budget:
    """Per-provider daily request counters in quota.json (§9.4)."""

    def __init__(self, path: Path, limits: dict[str, int]):
        self.path = path
        self.limits = limits

    def _load(self) -> dict:
        today = dt.date.today().isoformat()
        d = json.loads(self.path.read_text()) if self.path.exists() else {}
        return d if d.get("date") == today else {"date": today, "used": {}}

    def check(self, provider: str) -> None:
        used = self._load()["used"].get(provider, 0)
        limit = self.limits.get(provider, self.limits.get(provider.split(":")[0]))
        if limit is not None and used >= STOP_AT * limit:
            raise BudgetExhausted(f"{provider}: {used} of {limit} requests used today; resumes tomorrow")

    def spend(self, provider: str) -> None:
        d = self._load()
        d["used"][provider] = d["used"].get(provider, 0) + 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(d, indent=1))


class Runner:
    def __init__(self, client: LLMClient, cache_dir: Path, budget: Budget, retries: int = 6,
                 sleep: Callable[[float], None] = time.sleep, min_interval: float = 0.0):
        self.client, self.cache_dir, self.budget = client, cache_dir, budget
        self.retries, self.sleep, self.min_interval = retries, sleep, min_interval
        self._last = 0.0

    def key(self, system: str, user: str, prompt_version: str) -> str:
        return sha256_text(system, user, prompt_version, self.client.model)

    @property
    def budget_key(self) -> str:
        return f"{self.client.provider}:{self.client.model}"

    def complete(self, system: str, user: str, prompt_version: str) -> str:
        path = self.cache_dir / f"{self.key(system, user, prompt_version)}.json"
        if path.exists():
            return json.loads(path.read_text())["response"]
        for attempt in range(self.retries + 1):
            self.budget.check(self.budget_key)
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                self.sleep(wait)
            self._last = time.monotonic()
            try:
                self.budget.spend(self.budget_key)
                out = self.client._complete(system, user)
                break
            except RateLimited as e:
                if attempt == self.retries:
                    raise
                delay = min(60.0, 2 ** attempt) * (0.5 + random.random())  # backoff with jitter (§9.4)
                LG.warning("%s: %s; retrying in %.1fs", self.client.provider, e, delay)
                self.sleep(delay)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"provider": self.client.provider, "model": self.client.model,
                                    "prompt_version": prompt_version, "response": out}, ensure_ascii=False))
        return out


def configured_runner(model: str | None = None) -> Runner:
    """The provider and model in config/llm.yaml (or `model`), with that model's limits."""
    cfg = read_yaml(CONFIG_DIR / "llm.yaml")
    p = cfg["provider"]
    if p != "gemini":
        raise ValueError(f"unknown provider {p}")
    model = model or cfg[p]["model"]
    lim = cfg[p]["limits"].get(model, cfg[p]["limits"]["default"])
    d = INTERIM_DIR / "llm"
    return Runner(GeminiClient(model=model), cache_dir=d / "cache",
                  budget=Budget(d / "quota.json", {f"{p}:{model}": lim["requests_per_day"]}),
                  min_interval=60.0 / lim["requests_per_minute"])
