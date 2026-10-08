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
    if (toggle.dataset.bdAskAiBound === '1') return;
    toggle.dataset.bdAskAiBound = '1';

    function setPanelOpen(open) {
      if (open) {
        panel.hidden = false;
        panel.removeAttribute('hidden');
        panel.style.removeProperty('display');
        panel.setAttribute('aria-hidden', 'false');
        toggle.setAttribute('aria-expanded', 'true');
        input.focus();
      } else {
        panel.hidden = true;
        panel.setAttribute('hidden', '');
        panel.style.display = 'none';
        panel.setAttribute('aria-hidden', 'true');
        toggle.setAttribute('aria-expanded', 'false');
        if (typeof toggle.focus === 'function') {
          toggle.focus({ preventScroll: true });
        }
      }
    }

    function closePanel() {
      setPanelOpen(false);
    }

    function openPanel() {
      setPanelOpen(true);
    }

    toggle.addEventListener('click', () => {
      if (panel.hidden) openPanel();
      else closePanel();
    });

    if (close) {
      close.addEventListener('click', (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        closePanel();
      });
      close.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          ev.stopPropagation();
          closePanel();
        }
      });
    }

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
