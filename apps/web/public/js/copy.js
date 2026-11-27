// Copy buttons for citations (FR-TEXT-05). Progressive enhancement: the citation is plain text on the
// page; this script (external, so the strict CSP allows it) reveals a button that copies it.
document.querySelectorAll('button[data-copy]').forEach((btn) => {
  const target = document.querySelector(btn.getAttribute('data-copy'));
  if (!target || !navigator.clipboard) return;
  const label = btn.textContent;
  const status = document.querySelector(btn.getAttribute('data-status'));
  btn.hidden = false;
  btn.addEventListener('click', async () => {
    await navigator.clipboard.writeText(target.textContent.trim());
    btn.textContent = btn.getAttribute('data-done');
    if (status) status.textContent = btn.getAttribute('data-done');
    setTimeout(() => { btn.textContent = label; if (status) status.textContent = ''; }, 2500);
  });
});
