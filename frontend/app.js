// F1 Strategy Engine - Frontend JavaScript
const API_URL = 'http://localhost:8000';

document.getElementById('predictionForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Show loading, hide results/error
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    // Collect form data
    const formData = {
        LapNumber: parseInt(document.getElementById('LapNumber').value),
        Stint: parseInt(document.getElementById('Stint').value),
        TyreLife: parseInt(document.getElementById('TyreLife').value),
        Position: parseInt(document.getElementById('Position').value),
        GridPosition: parseInt(document.getElementById('GridPosition').value),
        Compound: document.getElementById('Compound').value,
        CompoundCode: parseInt(document.getElementById('CompoundCode').value),
        FreshTyre: parseInt(document.getElementById('FreshTyre').value),
        TrackTemp: parseFloat(document.getElementById('TrackTemp').value),
        AirTemp: parseFloat(document.getElementById('AirTemp').value),
        WindSpeed: parseFloat(document.getElementById('WindSpeed').value),
        Rainfall: parseInt(document.getElementById('Rainfall').value),
        IsSC: parseInt(document.getElementById('IsSC').value),
        IsVSC: 0,
        IsDRS: parseInt(document.getElementById('IsDRS').value),
        Team: document.getElementById('Team').value,
        Driver: document.getElementById('Driver').value,
        EventName: document.getElementById('EventName').value,
        Year: parseInt(document.getElementById('Year').value),

        // Optional rolling features (set defaults)
        Rolling3LapTime: 84.5,
        Rolling5LapTime: 84.8,
        LapTimeDelta: 0.0,
        PrevLapTime: 84.2,
        LapTimeVsField: 0.0,
        Sector1TimeSec_Delta: 0.0,
        Sector2TimeSec_Delta: 0.0,
        Sector3TimeSec_Delta: 0.0,
        PositionGain: formData.GridPosition - formData.Position,
        PrevFieldMedian: 84.5,
        RaceTime: formData.LapNumber * 84.5,
        GapAhead: 999.0,
        GapBehind: 999.0,
        IsLeader: formData.Position === 1 ? 1 : 0,
        IsLast: formData.Position === 20 ? 1 : 0
    };

    try {
        // Call prediction endpoint
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const predictions = await response.json();

        // Display results
        displayResults(predictions);

    } catch (error) {
        console.error('Prediction error:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = `Error: ${error.message}. Make sure the API server is running (uvicorn api.main:app --port 8000)`;
    }
});

function displayResults(predictions) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'grid';

    // Lap Time
    document.getElementById('lapTime').textContent =
        `${predictions.lap_time_sec.toFixed(2)}s`;

    // Pit Probability
    const pitProb = (predictions.pit_probability * 100).toFixed(1);
    document.getElementById('pitProb').textContent = `${pitProb}%`;
    document.getElementById('pitProbBar').style.width = `${pitProb}%`;
    document.getElementById('pitProbBar').className =
        'progress-fill ' + getProbabilityColor(predictions.pit_probability);

    // Pit in 3
    const pitIn3 = (predictions.will_pit_in_3 * 100).toFixed(1);
    document.getElementById('pitIn3').textContent = `${pitIn3}%`;
    document.getElementById('pitIn3Bar').style.width = `${pitIn3}%`;
    document.getElementById('pitIn3Bar').className =
        'progress-fill ' + getProbabilityColor(predictions.will_pit_in_3);

    // Laps Until Pit
    const lapsUntil = predictions.laps_until_pit.toFixed(1);
    document.getElementById('lapsUntil').textContent = `${lapsUntil} laps`;

    // Recommendation
    const recommendation = generateRecommendation(predictions);
    document.getElementById('recommendation').textContent = recommendation;
}

function getProbabilityColor(prob) {
    if (prob > 0.7) return 'high';
    if (prob > 0.4) return 'medium';
    return 'low';
}

function generateRecommendation(pred) {
    if (pred.pit_probability > 0.7) {
        return "⚠️ HIGH PIT RISK - Consider pitting this lap or next";
    } else if (pred.will_pit_in_3 > 0.6) {
        return `⏱️ PIT WINDOW OPENING - Expected in ${pred.laps_until_pit.toFixed(1)} laps`;
    } else if (pred.laps_until_pit < 5) {
        return `🔧 PREPARE PIT STOP - Within ${pred.laps_until_pit.toFixed(1)} laps`;
    } else if (pred.laps_until_pit < 10) {
        return `📊 MONITOR TYRES - Pit expected in ${pred.laps_until_pit.toFixed(1)} laps`;
    } else {
        return `✅ STAY OUT - ${pred.laps_until_pit.toFixed(1)} laps of tyre life remaining`;
    }
}

// Update compound code when compound changes
document.getElementById('Compound').addEventListener('change', (e) => {
    const compoundMap = {
        'SOFT': 1,
        'MEDIUM': 2,
        'HARD': 3,
        'INTERMEDIATE': 4,
        'WET': 5
    };
    document.getElementById('CompoundCode').value = compoundMap[e.target.value] || 2;
});
