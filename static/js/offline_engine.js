/**
 * OfflineHealthEngine
 * Handles client-side data loading and fuzzy searching for offline functionality.
 */
class OfflineHealthEngine {
    constructor() {
        this.diseases = {}; // { "malaria": { desc: "...", precautions: [] } }
        this.vaccines = [];
        this.isReady = false;
        this.init();
    }

    async init() {
        try {
            console.log("OfflineEngine: Loading data...");
            const [descData, precData, vacData] = await Promise.all([
                this.fetchCSV('/static/data/symptom_Description.csv'),
                this.fetchCSV('/static/data/symptom_precaution.csv'),
                this.fetchJSON('/static/data/vaccination_schedule.json')
            ]);

            this.processData(descData, precData);
            this.vaccines = vacData || [];
            this.isReady = true;
            console.log(`OfflineEngine: Ready with ${Object.keys(this.diseases).length} diseases and ${this.vaccines.length} vaccine schedules.`);
        } catch (e) {
            console.error("OfflineEngine: Failed to load data", e);
        }
    }

    async fetchCSV(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.text();
        } catch (e) {
            console.warn(`OfflineEngine: Could not fetch ${url}`, e);
            return "";
        }
    }

    async fetchJSON(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (e) {
            console.warn(`OfflineEngine: Could not fetch ${url}`, e);
            return null;
        }
    }

    // Simple CSV Parser (Assumes standard format)
    parseCSVLine(line) {
        // Handle quoted fields
        const matches = [];
        let inQuote = false;
        let start = 0;

        for (let i = 0; i < line.length; i++) {
            if (line[i] === '"') {
                inQuote = !inQuote;
            } else if (line[i] === ',' && !inQuote) {
                matches.push(line.substring(start, i).replace(/^"|"$/g, '').trim());
                start = i + 1;
            }
        }
        matches.push(line.substring(start).replace(/^"|"$/g, '').trim());
        return matches;
    }

    processData(descRaw, precRaw) {
        // 1. Process Descriptions
        const descLines = descRaw.split('\n');
        for (let i = 1; i < descLines.length; i++) { // Skip header
            if (!descLines[i].trim()) continue;
            const cols = this.parseCSVLine(descLines[i]);
            if (cols.length >= 2) {
                const name = cols[0].toLowerCase().trim();
                const desc = cols[1];
                if (!this.diseases[name]) this.diseases[name] = { desc: "No description.", precautions: [] };
                this.diseases[name].desc = desc;
            }
        }

        // 2. Process Precautions
        const precLines = precRaw.split('\n');
        for (let i = 1; i < precLines.length; i++) {
            if (!precLines[i].trim()) continue;
            const cols = this.parseCSVLine(precLines[i]);
            if (cols.length >= 2) {
                const name = cols[0].toLowerCase().trim();
                const precs = cols.slice(1).filter(p => p); // Get all remaining cols
                if (!this.diseases[name]) this.diseases[name] = { desc: "No description.", precautions: [] };
                this.diseases[name].precautions = precs;
            }
        }
    }

    findTopic(query) {
        if (!this.isReady) return null;
        query = query.toLowerCase().trim();

        // 1. Aliases (Partial list)
        const aliases = {
            "sugar": "diabetes",
            "bp": "hypertension",
            "flu": "influenza",
            "chickenpox": "chicken pox"
        };
        for (const [key, val] of Object.entries(aliases)) {
            if (query.includes(key)) query = query.replace(key, val);
        }

        // 2. Exact/Substring Search
        let bestMatch = null;
        const keys = Object.keys(this.diseases);

        // Exact match
        if (this.diseases[query]) bestMatch = query;
        else {
            // Substring search
            for (const k of keys) {
                if (query.includes(k) || k.includes(query)) {
                    // Simple length heuristic: don't match very short strings incorrectly
                    if (k.length > 3) {
                        bestMatch = k;
                        break;
                    }
                }
            }
        }

        if (bestMatch) {
            const info = this.diseases[bestMatch];
            return {
                topic: bestMatch,
                description: info.desc,
                precautions: info.precautions
            };
        }
        return null;
    }

    getVaccineSchedule() {
        return this.vaccines;
    }

    // Main Entry Point
    getResponse(query) {
        if (!this.isReady) return "<i>Offline database is loading... please wait.</i>";

        query = query.toLowerCase();

        // Vaccination
        if (query.includes("vaccin") || query.includes("immuniz") || query.includes("schedule")) {
            let html = "<div class='diagnosis-card' style='border-left-color: #6c5ce7;'><div class='diagnosis-title' style='color:#6c5ce7;'>💉 Universal Immunization Schedule (Offline Mode)</div><table style='width:100%; font-size:0.9rem; border-collapse: collapse;'><tr><th style='text-align:left; border-bottom:1px solid #ccc;'>Age</th><th style='text-align:left; border-bottom:1px solid #ccc;'>Vaccines</th></tr>";
            if (this.vaccines.length > 0) {
                this.vaccines.forEach(v => {
                    html += `<tr><td style='padding:5px 0; border-bottom:1px solid #eee;'>${v.age}</td><td style='padding:5px 0; border-bottom:1px solid #eee;'>${v.vaccines.join(', ')}</td></tr>`;
                });
            } else {
                html += "<tr><td colspan='2'>No data available.</td></tr>";
            }
            html += "</table></div>";
            return html;
        }

        // Disease Info
        const info = this.findTopic(query);
        if (info) {
            let html = `
            <div class='diagnosis-card' style='border-left-color: #0984E3;'>
                <div class='diagnosis-title' style='color:#0984E3;'>ℹ️ Information: ${info.topic} (Offline)</div>
                <p>${info.description}</p>
                <div class='section-title'>Health Safety Awareness</div>
                <ul class='precautions-list'>
                    ${info.precautions.map(p => `<li>${p}</li>`).join('')}
                </ul>
            </div>
            <div style='margin-top:10px; padding:10px; background:#e0e0e0; border-radius:5px; font-size:0.75rem; color:#555;'>
                 📡 <b>Offline Mode:</b> This information is served from your device's storage.
            </div>
            `;
            return html;
        }

        return "⚠️ <b>You are offline.</b><br>I can provide information on specific diseases (e.g., 'Malaria') and Vaccinations from my local database.<br>For AI explanations, please connect to the internet.";
    }
}

// Export instance
window.offlineEngine = new OfflineHealthEngine();
