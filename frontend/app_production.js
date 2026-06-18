// F1 Strategy Engine - Production Frontend
const API_URL = 'http://localhost:8000';

// Driver-to-Team mapping
const DRIVER_TEAMS = {
    'VER': 'Red Bull Racing', 'PER': 'Red Bull Racing',
    'HAM': 'Mercedes', 'RUS': 'Mercedes',
    'LEC': 'Ferrari', 'SAI': 'Ferrari',
    'NOR': 'McLaren', 'PIA': 'McLaren',
    'ALO': 'Aston Martin', 'STR': 'Aston Martin',
    'GAS': 'Alpine', 'OCO': 'Alpine',
    'ALB': 'Williams', 'SAR': 'Williams',
    'BOT': 'Kick Sauber', 'ZHO': 'Kick Sauber',
    'MAG': 'Haas F1 Team', 'HUL': 'Haas F1 Team',
    'TSU': 'RB', 'RIC': 'RB', 'LAW': 'RB'
};

// Tab Navigation
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('tab-active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        
        btn.classList.add('tab-active');
        document.getElementById(btn.dataset.tab).classList.remove('hidden');
    });
});

// Tyre Compound Selection
document.querySelectorAll('.tyre-pill').forEach(pill => {
    pill.addEventListener('click', () => {
        document.querySelectorAll('.tyre-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        document.getElementById('compound').value = pill.dataset.compound;
    });
});

// Driver Selection - Auto-update Team
document.getElementById('driver').addEventListener('change', (e) => {
    const driver = e.target.value;
    document.getElementById('team').value = DRIVER_TEAMS[driver] || 'UNKNOWN';
});

// Loading Overlay
function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

// Main Prediction Function
async function predictStrategy() {
    showLoading();

    const compoundMap = {'SOFT': 1, 'MEDIUM': 2, 'HARD': 3};
    const compound = document.getElementById('compound').value;

    const raceState = {
        LapNumber: parseInt(document.getElementById('lapNumber').value),
        Stint: 2,
        TyreLife: parseInt(document.getElementById('tyreLife').value),
        Position: parseInt(document.getElementById('position').value),
        GridPosition: parseInt(document.getElementById('position').value) + 2,
        Compound: compound,
        CompoundCode: compoundMap[compound],
        FreshTyre: 0,
        TrackTemp: parseFloat(document.getElementById('trackTemp').value),
        AirTemp: 28.0,
        WindSpeed: 2.5,
        Rainfall: 0,
        IsSC: 0,
        IsVSC: 0,
        IsDRS: 1,
        Rolling3LapTime: 84.5,
        Rolling5LapTime: 84.8,
        LapTimeDelta: 0.0,
        PrevLapTime: 84.2,
        LapTimeVsField: 0.0,
        Sector1TimeSec_Delta: 0.0,
        Sector2TimeSec_Delta: 0.0,
        Sector3TimeSec_Delta: 0.0,
        PositionGain: 2,
        PrevFieldMedian: 84.5,
        RaceTime: parseInt(document.getElementById('lapNumber').value) * 84.5,
        GapAhead: 2.5,
        GapBehind: 3.2,
        IsLeader: 0,
        IsLast: 0,
        Team: document.getElementById('team').value,
        Driver: document.getElementById('driver').value,
        EventName: document.getElementById('eventName').value,
        Year: 2024
    };

    try {
        const response = await fetch(`${API_URL}/api/v1/predictions/strategic`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(raceState)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        // Display results
        document.getElementById('predLapTime').textContent = `${result.lap_time_sec.toFixed(2)}s`;
        
        const tyreWear = result.tyre_wear_pct.toFixed(1);
        document.getElementById('predTyreWear').textContent = `${tyreWear}%`;
        
        const tyreWearBar = document.getElementById('predTyreWearBar');
        tyreWearBar.style.width = `${tyreWear}%`;
        tyreWearBar.className = `progress-bar-fill h-4 rounded-full transition-all duration-500 ${getUrgencyClass(result.pit_urgency)}`;
        
        document.getElementById('predPitUrgency').textContent = `${result.pit_urgency.toFixed(0)}/100`;
        
        const lapsUntil = result.optimal_pit_lap - raceState.LapNumber;
        document.getElementById('predOptimalPit').textContent = `Lap ${result.optimal_pit_lap}`;
        
        document.getElementById('predRecommendation').textContent = result.recommendation;

    } catch (error) {
        console.error('Prediction error:', error);
        alert(`Prediction failed: ${error.message}\n\nMake sure the API server is running at ${API_URL}`);
    } finally {
        hideLoading();
    }
}

function getUrgencyClass(urgency) {
    if (urgency >= 80) return 'high';
    if (urgency >= 60) return 'medium';
    return 'low';
}

// Initialize
console.log('F1 Strategy Engine loaded - Production version');
