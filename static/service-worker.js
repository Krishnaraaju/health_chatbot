const CACHE_NAME = 'health-bot-v6';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/manifest.json',
    '/static/js/offline_engine.js',
    '/static/data/symptom_Description.csv',
    '/static/data/symptom_Description_Tamil.csv',
    '/static/data/symptom_Description_Hindi.csv',
    '/static/data/symptom_Description_Odia.csv',
    '/static/data/symptom_precaution.csv',
    '/static/data/symptom_precaution_Tamil.csv',
    '/static/data/symptom_precaution_Hindi.csv',
    '/static/data/symptom_precaution_Odia.csv',
    '/static/data/vaccination_schedule.json'
];

// Install Event
self.addEventListener('install', (event) => {
    // Force this SW to become the active one, skipping the waiting phase
    self.skipWaiting();

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
    // Take control of all pages immediately
    event.waitUntil(clients.claim());

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
