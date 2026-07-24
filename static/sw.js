const CACHE = 'blackdark-v1';
const ASSETS = ['/', '/dashboard', '/static/manifest.json'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/oracle/')) return;
  event.respondWith(
    fetch(event.request)
      .then((res) => {
        if (res.ok && url.origin === self.location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy));
        }
        return res;
      })
      .catch(() => caches.match(event.request).then((r) => r || caches.match('/dashboard')))
  );
});
