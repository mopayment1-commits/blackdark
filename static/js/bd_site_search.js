(function () {
  function esc(s) {
    return String(s ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;');
  }

  function wireSearch() {
    const input = document.getElementById('bdNavSearch');
    const panel = document.getElementById('bdNavSearchResults');
    if (!input || !panel) return;
    let timer = null;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (!q) {
        panel.hidden = true;
        panel.innerHTML = '';
        return;
      }
      timer = setTimeout(async () => {
        try {
          const res = await fetch('/api/public/site-search?q=' + encodeURIComponent(q));
          const data = await res.json();
          const rows = data.results || [];
          if (!rows.length) {
            panel.innerHTML = '<p class="bd-nav-search-empty">No matches</p>';
          } else {
            panel.innerHTML = rows
              .map((r) => `<a href="${esc(r.path)}">${esc(r.title)}</a>`)
              .join('');
          }
          panel.hidden = false;
        } catch (e) {
          panel.hidden = true;
        }
      }, 180);
    });
    document.addEventListener('click', (ev) => {
      if (!panel.contains(ev.target) && ev.target !== input) panel.hidden = true;
    });
    input.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') panel.hidden = true;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireSearch);
  } else {
    wireSearch();
  }
})();
