/**
 * Data Freshness Badge — #1030 cross-cutting UI component
 */
(function (global) {
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderFreshnessBadge(freshness) {
    if (!freshness) return '';
    const badge = freshness.badge || freshness;
    const state = badge.state || freshness.state || 'Live';
    const source = badge.source_name || freshness.source || 'unknown';
    const ts = badge.timestamp_iso || freshness.timestamp || '';
    const rel = badge.relative_supplement || freshness.relative_supplement || '';
    const css = badge.css_class || ('dfb-' + String(state).toLowerCase());
    const href = badge.provenance_href || '#';
    const label = badge.label || state;
    return (
      '<span class="data-freshness-badge ' + esc(css) + '" data-state="' + esc(state) + '" data-source="' + esc(source) + '" data-timestamp="' + esc(ts) + '">' +
      '<a class="dfb-link" href="' + esc(href) + '">' + esc(label) + '</a>' +
      '<span class="dfb-source">' + esc(source) + '</span>' +
      '<time class="dfb-time" datetime="' + esc(ts) + '">' + esc(ts) + '</time>' +
      (rel ? '<span class="dfb-relative">(' + esc(rel) + ')</span>' : '') +
      '</span>'
    );
  }

  function mountFreshnessBadges(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-freshness-json]').forEach(function (el) {
      try {
        const data = JSON.parse(el.getAttribute('data-freshness-json') || '{}');
        el.innerHTML = renderFreshnessBadge(data);
      } catch (e) {
        console.debug('freshness badge mount failed', e);
      }
    });
  }

  global.DataFreshnessBadge = {
    render: renderFreshnessBadge,
    mount: mountFreshnessBadges,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { mountFreshnessBadges(); });
  } else {
    mountFreshnessBadges();
  }
})(typeof window !== 'undefined' ? window : globalThis);
