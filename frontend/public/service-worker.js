const CACHE_VERSION = 'v4';
const CACHE_NAME = `cognispace-${CACHE_VERSION}`;
const STATIC_CACHE = `cognispace-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `cognispace-dynamic-${CACHE_VERSION}`;

// Assets to cache immediately on install (only truly static assets)
const STATIC_ASSETS = [
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/offline.html',
  '/notification-sound.mp3'
];

// API routes that should use network-first strategy
const API_ROUTES = ['/api/'];

// JS/CSS files should always use network-first to get latest bundles
const BUNDLE_PATTERNS = ['.js', '.css', '.chunk.'];

// Install event - cache only truly static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install - Version:', CACHE_VERSION);
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting()) // Immediately activate new SW
  );
});

// Activate event - clean up ALL old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activate - Version:', CACHE_VERSION);
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => {
            // Delete any cache that doesn't match current version
            return !name.includes(CACHE_VERSION);
          })
          .map((name) => {
            console.log('[ServiceWorker] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => {
      console.log('[ServiceWorker] Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension and other non-http(s) requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // API requests - Network first
  if (API_ROUTES.some(route => url.pathname.startsWith(route))) {
    event.respondWith(networkFirst(request));
    return;
  }

  // JS/CSS bundles - ALWAYS network first to get latest code
  if (BUNDLE_PATTERNS.some(pattern => url.pathname.includes(pattern))) {
    event.respondWith(networkFirst(request));
    return;
  }

  // index.html - ALWAYS network first (critical for SPA routing)
  if (url.pathname === '/' || url.pathname === '/index.html' || !url.pathname.includes('.')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Other static assets (images, icons) - Cache first
  event.respondWith(cacheFirst(request));
});

// Cache-first strategy (only for truly static assets like images)
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Return offline page if available
    const offlineResponse = await caches.match('/offline.html');
    if (offlineResponse) {
      return offlineResponse;
    }
    
    return new Response('Offline - Please check your connection', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({ 'Content-Type': 'text/plain' })
    });
  }
}

// Network-first strategy (for API, JS/CSS, and HTML)
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request, {
      cache: 'no-store' // Bypass browser cache for fresh content
    });
    
    // Cache successful GET responses (but network is always tried first)
    if (networkResponse.ok && request.method === 'GET') {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // For HTML navigation requests, return offline page
    if (request.headers.get('accept')?.includes('text/html')) {
      const offlineResponse = await caches.match('/offline.html');
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    
    return new Response(JSON.stringify({ error: 'Offline' }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({ 'Content-Type': 'application/json' })
    });
  }
}

// Listen for messages from the app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[ServiceWorker] Skip waiting requested');
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    console.log('[ServiceWorker] Clear cache requested');
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((name) => caches.delete(name))
        );
      })
    );
  }
});

// Handle push notifications
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body || 'New notification from COGNISPACE',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    tag: data.tag || 'cognispace-notification',
    renotify: true,
    requireInteraction: data.requireInteraction || false,
    silent: data.silent || false,
    data: {
      url: data.url || '/',
      playSound: data.playSound !== false,
      notificationId: data.notificationId
    },
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'COGNISPACE', options)
      .then(() => {
        // Update badge count
        if (data.badgeCount !== undefined && navigator.setAppBadge) {
          navigator.setAppBadge(data.badgeCount);
        }
        
        // Notify all clients to play sound if enabled
        if (data.playSound !== false) {
          self.clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((windowClients) => {
              windowClients.forEach((client) => {
                client.postMessage({
                  type: 'PLAY_NOTIFICATION_SOUND',
                  notificationId: data.notificationId
                });
              });
            });
        }
      })
  );
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';
  
  // Clear badge on click
  if (navigator.clearAppBadge) {
    navigator.clearAppBadge();
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        for (const client of windowClients) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.postMessage({ type: 'NOTIFICATION_CLICKED', url });
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-appointments') {
    event.waitUntil(syncAppointments());
  }
});

async function syncAppointments() {
  console.log('[ServiceWorker] Syncing appointments...');
}
