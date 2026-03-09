const API_URL = 'http://127.0.0.1:5000/api';

// State
let myGlobe;
let satData = [];

// Initialize Globe
function initGlobe() {
    myGlobe = Globe()
        (document.getElementById('globeViz'))
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
        .pointOfView({ altitude: 2.5 })
        
        // Satellite Points configuration
        .pointsData([])
        .pointColor(() => '#3b82f6')
        .pointAltitude('alt')
        .pointRadius(0.02)
        .pointsMerge(true)
        
        // Arcs configuration (for conjunctions)
        .arcsData([])
        .arcColor('color')
        .arcDashLength(0.4)
        .arcDashGap(0.2)
        .arcDashAnimateTime(1500)
        .arcAltitudeAutoScale(0.3)
        .arcStroke(0.5);
        
    // Add auto-rotation
    myGlobe.controls().autoRotate = true;
    myGlobe.controls().autoRotateSpeed = 0.5;
}

// Fetch initial satellites to render cloud
async function loadSatellites(group, limit) {
    try {
        const response = await fetch(`${API_URL}/satellites?group=${group}&limit=${limit}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            satData = data.satellites;
            myGlobe.pointsData(satData);
        }
    } catch (err) {
        console.error("Failed to load initial satellites", err);
    }
}

// Run Collision Detection
async function initScan() {
    const group = document.getElementById('group-select').value;
    const duration = document.getElementById('duration-input').value;
    const threshold = document.getElementById('threshold-input').value;
    const limit = document.getElementById('limit-input').value;
    
    // UI Loading state
    document.getElementById('alerts-container').innerHTML = '';
    document.getElementById('loader').classList.remove('hidden');
    document.getElementById('threat-count').textContent = '...';
    document.getElementById('run-btn').classList.add('loading');
    
    // Clear previous arcs
    myGlobe.arcsData([]);
    
    try {
        const response = await fetch(`${API_URL}/detect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group, duration, threshold, limit })
        });
        
        const data = await response.json();
        
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('run-btn').classList.remove('loading');
        
        if (data.status === 'success') {
            renderAlerts(data.conjunctions, data.start_time);
            visualizeConjunctions(data.conjunctions);
        } else {
            showError(data.message);
        }
        
    } catch (err) {
        document.getElementById('loader').classList.add('hidden');
        showError("Failed to connect to simulation engine.");
        console.error(err);
    }
}

function renderAlerts(conjunctions, startTime) {
    const container = document.getElementById('alerts-container');
    document.getElementById('threat-count').textContent = conjunctions.length;
    
    if (conjunctions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>Status: GREEN<br>No close approaches detected under limit.</p>
            </div>`;
        return;
    }
    
    container.innerHTML = '';
    
    conjunctions.forEach(c => {
        const isCritical = c.distance_km < 5.0; // Critical threshold
        const timeStr = c.time.split(' ')[1]; // Extract just the time part HH:MM:SS
        
        const card = document.createElement('div');
        card.className = `alert-card ${isCritical ? 'critical' : 'warning'}`;
        card.innerHTML = `
            <div class="alert-header">
                <span class="alert-time">${timeStr} UTC</span>
                <span>APPROACH ALERT</span>
            </div>
            <div class="sat-pair">
                <span class="sat-name">${c.sat1}</span>
                <span class="sat-divider">◄►</span>
                <span class="sat-name">${c.sat2}</span>
            </div>
            <div class="alert-metrics">
                <span>Est. Min Range:</span>
                <span class="distance">${c.distance_km.toFixed(2)} km</span>
            </div>
        `;
        
        // Add click listener to focus globe
        card.addEventListener('click', () => focusGlobeOnPair(c.sat1, c.sat2));
        
        container.appendChild(card);
    });
}

function visualizeConjunctions(conjunctions) {
    // To draw arcs, we need the initial lat/lon of both satellites.
    // In a full system, the backend would return exact collision lat/lon.
    // For this prototype, we'll draw an arc between their INITIAL positions to show link.
    const arcs = [];
    
    conjunctions.forEach(c => {
        const sat1 = satData.find(s => s.name === c.sat1);
        const sat2 = satData.find(s => s.name === c.sat2);
        
        if (sat1 && sat2) {
            arcs.push({
                startLat: sat1.lat,
                startLng: sat1.lng,
                endLat: sat2.lat,
                endLng: sat2.lng,
                color: c.distance_km < 5.0 ? ['rgba(239, 68, 68, 0.8)', 'rgba(239, 68, 68, 0.1)'] : ['rgba(245, 158, 11, 0.8)', 'rgba(245, 158, 11, 0.1)'],
                name: `${c.sat1} x ${c.sat2}`
            });
        }
    });
    
    myGlobe.arcsData(arcs);
}

function focusGlobeOnPair(sat1Name, sat2Name) {
    const s1 = satData.find(s => s.name === sat1Name);
    if(s1) {
        myGlobe.pointOfView({ lat: s1.lat, lng: s1.lng, altitude: 1.5 }, 1000);
        myGlobe.controls().autoRotate = false;
        
        // Resume rotation after 5s
        setTimeout(() => {
            myGlobe.controls().autoRotate = true;
        }, 5000);
    }
}

function showError(msg) {
    const container = document.getElementById('alerts-container');
    container.innerHTML = `
        <div class="empty-state" style="border-color: var(--accent-red);">
            <p style="color: var(--accent-red);">System Error:<br>${msg}</p>
        </div>`;
}

// Mount
document.addEventListener('DOMContentLoaded', () => {
    initGlobe();
    
    // Load initial background data
    loadSatellites('starlink', 500);
    
    // Bind listeners
    document.getElementById('run-btn').addEventListener('click', initScan);
    
    // Handle window resize for globe
    window.addEventListener('resize', () => {
        myGlobe.width(window.innerWidth).height(window.innerHeight);
    });
});
