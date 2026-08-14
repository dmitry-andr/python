async function initRag() {
  const btn = document.getElementById('init-rag-btn');
  if (!btn) return;

  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = 'Initializing...';

  try {
    const res = await fetch('/admin/init-rag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force: true }),
    });
    const data = await res.json();
    alert('RAG init: ' + (data.message || JSON.stringify(data)));
    await updateRagStatus();
  } catch (err) {
    alert('RAG init failed: ' + err);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

async function updateRagStatus() {
  const statusEl = document.getElementById('rag-status');
  if (!statusEl) return;

  try {
    const res = await fetch('/admin/rag-status');
    if (!res.ok) throw new Error('Status request failed');
    const data = await res.json();
    statusEl.textContent = data.initialized ? 'RAG: initialized' : 'RAG: not initialized';
    statusEl.style.color = data.initialized ? 'green' : 'orange';
  } catch (err) {
    statusEl.textContent = 'RAG: unknown';
    statusEl.style.color = 'gray';
  }
}

window.addEventListener('load', () => {
  updateRagStatus();
});
