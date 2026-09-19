const CACHE = 'geoshield-shell-v1';
const APP_SHELL = ['/', '/index.html', '/geoshield_logo.svg'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) return;

  event.respondWith(
    fetch(request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE).then((cache) => cache.put(request, copy)).catch(() => undefined);
        return response;
      })
      .catch(() => caches.match(request).then((cached) => cached || caches.match('/index.html')))
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      if (clients.length) return clients[0].focus();
      const target = event.notification?.data?.url || '/#/alerts';
      return self.clients.openWindow(target);
    })
  );
});


self.addEventListener('push', (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = { body: event.data ? event.data.text() : 'GeoShield alert received.' };
  }

  const title = payload.title || 'GeoShield Alert';
  const options = {
    body: payload.body || 'New early-warning alert received.',
    icon: '/geoshield_logo.svg',
    badge: '/geoshield_logo.svg',
    tag: payload.tag || 'geoshield-alert',
    renotify: true,
    requireInteraction: payload.risk_level === 'critical',
    data: {
      url: payload.url || '/#/alerts',
      district: payload.district || null,
      risk_level: payload.risk_level || null,
    },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});
