(function () {
  function collectPageContext() {
    const ctx = { path: location.pathname };
    const action = document.getElementById('lpAction');
    const sym = document.getElementById('lpSym');
    const sentence = document.getElementById('lpSentence');
    if (action || sym) {
      ctx.trust_pulse = {
        action: action ? action.textContent.trim() : '',
        symbol: sym ? sym.textContent.trim().split(/\s/)[0] : '',
        sentence: sentence ? sentence.textContent.trim() : '',
      };
    }
    const seal = document.getElementById('sealCertificateHash');
    if (seal && seal.textContent.trim()) ctx.seal_hash = seal.textContent.trim();
    return ctx;
  }

  function appendMsg(box, role, text) {
    const p = document.createElement('p');
    p.className = 'bd-ask-msg bd-ask-' + role;
    p.textContent = text;
    box.appendChild(p);
    box.scrollTop = box.scrollHeight;
  }

  function wireAssistant() {
    const toggle = document.getElementById('bdAskAiToggle');
    const panel = document.getElementById('bdAskAiPanel');
    const close = document.getElementById('bdAskAiClose');
    const form = document.getElementById('bdAskAiForm');
    const input = document.getElementById('bdAskAiInput');
    const log = document.getElementById('bdAskAiLog');
    if (!toggle || !panel || !form || !input || !log) return;

    toggle.addEventListener('click', () => {
      const open = !panel.hidden;
      panel.hidden = open;
      toggle.setAttribute('aria-expanded', open ? 'false' : 'true');
      if (!open) input.focus();
    });
    close?.addEventListener('click', () => {
      panel.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
    });

    form.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      appendMsg(log, 'user', message);
      input.value = '';
      try {
        const res = await fetch('/api/public/site-assistant', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, page_context: collectPageContext() }),
        });
        const data = await res.json();
        appendMsg(log, 'bot', data.reply || 'Unavailable right now.');
      } catch (e) {
        appendMsg(log, 'bot', 'Unavailable right now.');
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireAssistant);
  } else {
    wireAssistant();
  }
})();
