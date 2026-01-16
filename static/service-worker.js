const CACHE_NAME = 'health-bot-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/manifest.json',
    '/static/js/offline_engine.js',
    '/static/data/symptom_Description.csv',
    '/static/data/symptom_precaution.csv',
    '/static/data/vaccination_schedule.json',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Install Event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('Opened cache');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// Fetch Event
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            // Return cached version or fetch from network
            return response || fetch(event.request).catch(() => {
                // Fallback logic could go here
                return new Response("Offline functionality limited to cached resources.");
            });
        })
    );
});

// Activate Event (Cleanup old caches)
self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
