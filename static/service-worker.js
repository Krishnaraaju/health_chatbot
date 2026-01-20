const CACHE_NAME = 'health-bot-v7';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/css/landing.css',
    '/static/favicon_1.svg',
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

// Fetch Event - Network First for HTML (to see Alerts), Cache First for Assets
self.addEventListener('fetch', (event) => {
    // 1. Navigation Requests (HTML Pages): Network First
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
    }
    // 2a. Chat Requests: NETWORK ONLY -> Fail Hard (triggers client offline engine)
    else if (event.request.url.includes('/get_response')) {
        event.respondWith(
            fetch(event.request)
        );
    }
    // 2b. API Alerts: NETWORK ONLY -> Fail Soft (Silent JSON)
    else if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(JSON.stringify([]), {
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
    }
    // 3. Asset Requests (CSS, JS, CSVs): Cache First
    else {
        event.respondWith(
            caches.match(event.request).then((response) => {
                return response || fetch(event.request);
            })
        );
    }
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
