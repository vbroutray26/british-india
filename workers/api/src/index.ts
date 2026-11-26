import { MAX_BODY_BYTES, parseCorrection } from './corrections';

export interface Env {
  ALLOWED_ORIGIN: string;
  CORRECTIONS?: KVNamespace;
  TURNSTILE_SECRET?: string;
}

const json = (data: unknown, status = 200, origin = '*') =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'access-control-allow-origin': origin, vary: 'origin' },
  });

async function turnstileOk(token: string, secret: string, ip: string | null): Promise<boolean> {
  const form = new FormData();
  form.append('secret', secret);
  form.append('response', token);
  if (ip) form.append('remoteip', ip);
  const r = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: form });
  return ((await r.json()) as { success?: boolean }).success === true;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const origin = env.ALLOWED_ORIGIN;
    if (req.method === 'OPTIONS') {
      return new Response(null, { headers: { 'access-control-allow-origin': origin, 'access-control-allow-methods': 'POST', 'access-control-allow-headers': 'content-type' } });
    }
    if (url.pathname === '/health') return json({ ok: true }, 200, origin);
    if (url.pathname !== '/corrections' || req.method !== 'POST') return json({ error: 'not found' }, 404, origin);

    const raw = await req.text();
    if (raw.length > MAX_BODY_BYTES) return json({ error: 'payload too large' }, 413, origin);
    let body: Record<string, unknown>;
    try { body = JSON.parse(raw); } catch { return json({ error: 'invalid json' }, 400, origin); }

    const parsed = parseCorrection(body);
    if (parsed.ok === 'spam') return json({ ok: true }, 200, origin); // silent reject
    if (!parsed.ok) return json({ error: parsed.error }, parsed.status, origin);

    if (env.TURNSTILE_SECRET) {
      const ok = await turnstileOk(String(body['cf-turnstile-response'] ?? ''), env.TURNSTILE_SECRET, req.headers.get('cf-connecting-ip'));
      if (!ok) return json({ ok: true }, 200, origin); // silent reject (AC-CORR-03)
    }

    const id = `corr_${new Date().toISOString().slice(0, 10)}_${crypto.randomUUID().slice(0, 8)}`;
    // Private store; owner email notification is added in M3 (FR-CORR-03) [verify email service].
    await env.CORRECTIONS?.put(id, JSON.stringify({ ...parsed.value, received: new Date().toISOString() }), { expirationTtl: 60 * 60 * 24 * 180 });
    return json({ ok: true, id, respond_within_days: 7 }, 200, origin);
  },
} satisfies ExportedHandler<Env>;
