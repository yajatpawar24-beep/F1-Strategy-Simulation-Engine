// F1 Strategy Engine - API Integration
const API_URL = 'http://localhost:8000';

// Driver-Team Mapping
const DRIVER_TEAMS = {
    'VER': 'Red Bull Racing',
    'PER': 'Red Bull Racing',
    'HAM': 'Mercedes',
    'RUS': 'Mercedes',
    'LEC': 'Ferrari',
    'SAI': 'Ferrari',
    'NOR': 'McLaren',
    'PIA': 'McLaren',
    'ALO': 'Aston Martin',
    'STR': 'Aston Martin'
};

// Tyre compound mapping for API
const COMPOUND_MAP = {
    'SOFT': 1,
    'MEDIUM': 2,
    'HARD': 3
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    console.log('🏎️  F1 Strategy Engine - Ready');
});

function initializeEventListeners() {
    // Driver selection auto-updates team
    const driverSelect = document.getElementById('driver');
    const teamInput = document.getElementById('team');

    driverSelect.addEventListener('change', (e) => {
        const driver = e.target.value;
        teamInput.value = DRIVER_TEAMS[driver] || 'Unknown Team';
    });

    // Tyre compound selector
    const tyreButtons = document.querySelectorAll('.tyre-btn');
    const compoundInput = document.getElementById('compound');

    tyreButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            tyreButtons.forEach(b => b.classList.remove('tyre-btn-active'));
            // Add active class to clicked button
            btn.classList.add('tyre-btn-active');
            // Update hidden input
            compoundInput.value = btn.dataset.compound;
        });
    });

    // Tyre life slider
    const tyreLifeSlider = document.getElementById('tyreLife');
    const tyreLifeDisplay = document.getElementById('tyreLifeDisplay');

    tyreLifeSlider.addEventListener('input', (e) => {
        tyreLifeDisplay.textContent = `${e.target.value} LAPS`;
    });

    // Form submission
    const form = document.getElementById('strategyForm');
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        predictStrategy();
    });
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

async function predictStrategy() {
    showLoading();

    try {
        // Gather form data
        const compound = document.getElementById('compound').value;
        const raceState = {
            LapNumber: parseInt(document.getElementById('lapNumber').value),
            Stint: 2,
            TyreLife: parseInt(document.getElementById('tyreLife').value),
            Position: parseInt(document.getElementById('position').value),
            GridPosition: parseInt(document.getElementById('position').value) + 2,
            Compound: compound,
            CompoundCode: COMPOUND_MAP[compound],
            FreshTyre: 0,
            TrackTemp: parseFloat(document.getElementById('trackTemp').value),
            AirTemp: parseFloat(document.getElementById('airTemp').value),
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

        // Make API call
        const response = await fetch(`${API_URL}/api/v1/predictions/strategic`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(raceState)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        // Update UI with results
        updateResults(result);

        console.log('✅ Prediction successful:', result);

    } catch (error) {
        console.error('❌ Prediction error:', error);
        alert(`Prediction failed: ${error.message}\n\nMake sure the API server is running at ${API_URL}`);
    } finally {
        hideLoading();
    }
}

function updateResults(result) {
    // Lap Time
    const lapTimeElement = document.getElementById('predLapTime');
    lapTimeElement.querySelector('.value-main').textContent = result.lap_time_sec.toFixed(3);

    // Tyre Wear
    const tyreWearElement = document.getElementById('predTyreWear');
    tyreWearElement.querySelector('.value-main').textContent = result.tyre_wear_pct.toFixed(1);

    const tyreWearBar = document.getElementById('predTyreWearBar');
    tyreWearBar.style.width = `${Math.min(result.tyre_wear_pct, 100)}%`;

    // Pit Urgency
    const pitUrgencyElement = document.getElementById('predPitUrgency');
    pitUrgencyElement.querySelector('.value-main').textContent = Math.round(result.pit_urgency);

    // Optimal Pit Lap
    const optimalPitElement = document.getElementById('predOptimalPit');
    optimalPitElement.querySelector('.value-main').textContent = result.optimal_pit_lap;

    // Recommendation
    const recommendationElement = document.getElementById('predRecommendation');
    recommendationElement.innerHTML = `<p>${result.recommendation}</p>`;

    // Add animation
    document.querySelectorAll('.result-card, .recommendation-card').forEach((card, index) => {
        card.style.animation = 'none';
        setTimeout(() => {
            card.style.animation = `fadeIn ${400 + (index * 50)}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        }, 10);
    });
}
