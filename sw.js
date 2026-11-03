// Service Worker - Electron Medical Algérie SAV (PWA Offline-First)
const CACHE_NAME = 'electron-sav-v1.7';

const PRECACHE_ASSETS = [
  './',
  'index.html',
  'login.html',
  'visite_controle.html',
  'feuille_inspection.html',
  'rapport_installation.html',
  'rapport_mise_en_service.html',
  'rapport_formation.html',
  'parametres_admin.html',
  'css/main.css',
  'js/features_v4.js',
  'js/features_v5.js',
  'js/features_v6_tournees.js',
  'js/algeria_wilayas.js',
  'js/auth.js',
  'js/api.js',
  'js/theme.js',
  'js/qrcode.min.js',
  'manifest.json',
  'assets/electron-medical-logo.png',
  'assets/icon-192.png',
  'assets/icon-512.png',
  'assets/icon-maskable-192.png',
  'assets/icon-maskable-512.png',
  'assets/apple-touch-icon.png',
  'assets/favicon-32.png',
  'assets/fujifilm-ep8000.png',
  'assets/fujifilm-endoscope.png',
  'assets/endoscopy-tower.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Mise en cache des ressources essentielles hors-ligne...');
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW] Pré-mise en cache partielle:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Nettoyage ancien cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Ignorer les requêtes non GET (POST, PUT, DELETE gérées par API client)
  if (req.method !== 'GET') return;

  // Requêtes API : Stratégie Réseau d'abord avec fallback Cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
          }
          return res;
        })
        .catch(() => {
          return caches.match(req);
        })
    );
    return;
  }

  // Requêtes Fichiers Statiques (HTML, CSS, JS, Images) : Stratégie Cache d'abord avec rafraîchissement Réseau
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) {
        // En arrière-plan, essayer de mettre à jour le cache
        fetch(req).then((networkRes) => {
          if (networkRes && networkRes.ok) {
            caches.open(CACHE_NAME).then((cache) => cache.put(req, networkRes));
          }
        }).catch(() => {});
        return cached;
      }

      return fetch(req).then((networkRes) => {
        if (networkRes && networkRes.ok) {
          const clone = networkRes.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
        }
        return networkRes;
      }).catch(() => {
        // Fallback page si HTML demandé hors-ligne
        if (req.headers.get('accept') && req.headers.get('accept').includes('text/html')) {
          return caches.match('index.html');
        }
      });
    })
  );
});

