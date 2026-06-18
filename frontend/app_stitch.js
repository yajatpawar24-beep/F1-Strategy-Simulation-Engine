// F1 Strategy Engine v2.0 - Frontend JavaScript
const API_URL = 'http://localhost:8000';

// Driver-to-Team mapping (from 2024 data)
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
    'STR': 'Aston Martin',
    'GAS': 'Alpine',
    'OCO': 'Alpine',
    'DOO': 'Alpine',
    'ALB': 'Williams',
    'SAR': 'Williams',
    'COL': 'Williams',
    'BOT': 'Kick Sauber',
    'ZHO': 'Kick Sauber',
    'MAG': 'Haas F1 Team',
    'HUL': 'Haas F1 Team',
    'BEA': 'Haas F1 Team',
    'TSU': 'RB',
    'RIC': 'RB',
    'LAW': 'RB',
    'DEV': 'AlphaTauri'
};

// Tab Navigation
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Add active to clicked
        btn.classList.add('active');
        const tabId = btn.dataset.tab;
        document.getElementById(tabId).classList.add('active');
    });
});

// Loading overlay
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

// ============================================================================
// TAB 1: SINGLE PREDICTION
// ============================================================================

async function predictStrategy() {
    showLoading();

    const compoundMap = {'SOFT': 1, 'MEDIUM': 2, 'HARD': 3};
    const compound = document.getElementById('compound').value;

    const raceState = {
        LapNumber: parseInt(document.getElementById('lapNumber').value),
        Stint: parseInt(document.getElementById('stint').value),
        TyreLife: parseInt(document.getElementById('tyreLife').value),
        Position: parseInt(document.getElementById('position').value),
        GridPosition: parseInt(document.getElementById('gridPosition').value),
        Compound: compound,
        CompoundCode: compoundMap[compound],
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
        PositionGain: parseInt(document.getElementById('gridPosition').value) -
                     parseInt(document.getElementById('position').value),
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
        // Get STRATEGIC prediction (top-level system)
        const response = await fetch(`${API_URL}/api/v1/predictions/strategic`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(raceState)
        });
        const result = await response.json();

        // Display lap time
        document.getElementById('predLapTime').textContent =
            `${result.lap_time_sec.toFixed(2)}s`;

        // Display tyre wear with urgency-based coloring
        const tyreWear = result.tyre_wear_pct.toFixed(0);
        document.getElementById('predPitProb').textContent = `${tyreWear}%`;
        document.getElementById('predPitProbBar').style.width = `${tyreWear}%`;
        document.getElementById('predPitProbBar').className =
            'progress-fill ' + getUrgencyColorClass(result.pit_urgency);

        // Display pit urgency
        const pitUrgency = result.pit_urgency.toFixed(0);
        document.getElementById('predPitIn3').textContent = `${pitUrgency}/100`;
        document.getElementById('predPitIn3Bar').style.width = `${pitUrgency}%`;
        document.getElementById('predPitIn3Bar').className =
            'progress-fill ' + getUrgencyColorClass(result.pit_urgency);

        // Display optimal pit lap and time loss
        const lapsUntil = result.optimal_pit_lap - raceState.LapNumber;
        document.getElementById('predLapsUntil').textContent =
            `Lap ${result.optimal_pit_lap} (${lapsUntil} laps)`;

        // Display strategic recommendation with emoji
        document.getElementById('predRecommendation').textContent =
            result.recommendation;

        // Add extra strategic info
        const extraInfo = `
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; font-size: 0.9rem;">
                    <div><strong>Degradation:</strong> ${result.degradation_rate}</div>
                    <div><strong>Time Loss:</strong> +${result.time_loss_vs_fresh}s/lap</div>
                    <div><strong>Pit in 3 laps:</strong> ${result.should_pit_in_3 ? '✅ YES' : '❌ NO'}</div>
                    <div><strong>Model:</strong> ${result.horizon_model}</div>
                </div>
            </div>
        `;

        // Append extra info to recommendation card
        const recCard = document.getElementById('predRecommendation').parentElement;
        const existingExtra = recCard.querySelector('.extra-info');
        if (existingExtra) existingExtra.remove();

        const extraDiv = document.createElement('div');
        extraDiv.className = 'extra-info';
        extraDiv.innerHTML = extraInfo;
        recCard.appendChild(extraDiv);

    } catch (error) {
        alert('Prediction error: ' + error.message);
    } finally {
        hideLoading();
    }
}

function getColorClass(prob) {
    if (prob > 0.7) return 'high';
    if (prob > 0.4) return 'medium';
    return 'low';
}

function getUrgencyColorClass(urgency) {
    if (urgency >= 80) return 'high';      // Critical (red)
    if (urgency >= 60) return 'medium';    // In window (yellow)
    return 'low';                           // Stay out (green)
}

// ============================================================================
// TAB 2: RACE SIMULATION
// ============================================================================

async function simulateRace() {
    showLoading();

    const params = {
        driver: document.getElementById('simDriver').value,
        team: document.getElementById('simTeam').value,
        event_name: document.getElementById('simEvent').value,
        total_laps: parseInt(document.getElementById('simLaps').value),
        initial_compound: document.getElementById('simCompound').value,
        track_temp: parseFloat(document.getElementById('simTrackTemp').value)
    };

    try {
        const response = await fetch(`${API_URL}/api/v1/analytics/race-simulation`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        const data = await response.json();

        // Display results
        let html = `
            <div class="sim-summary">
                <div class="stat">
                    <div class="stat-label">Total Time</div>
                    <div class="stat-value">${data.total_time_formatted}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Avg Lap Time</div>
                    <div class="stat-value">${data.avg_lap_time.toFixed(2)}s</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Pit Stops</div>
                    <div class="stat-value">${data.pit_stops}</div>
                </div>
            </div>
        `;

        if (data.pit_stop_laps && data.pit_stop_laps.length > 0) {
            html += '<h4>Pit Stop Strategy:</h4><ul class="pit-stops">';
            data.pit_stop_laps.forEach(pit => {
                html += `<li>Lap ${pit.lap}: ${pit.compound_change} - ${pit.reason}</li>`;
            });
            html += '</ul>';
        }

        html += `<p class="info-text">Simulated ${data.total_laps} laps for ${data.driver} (${data.team})</p>`;

        document.getElementById('simResults').innerHTML = html;

    } catch (error) {
        document.getElementById('simResults').innerHTML =
            `<p class="error">Simulation error: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

// ============================================================================
// TAB 3: TYRE COMPARISON
// ============================================================================

async function compareTyres() {
    showLoading();

    const params = {
        lap_number: parseInt(document.getElementById('compLap').value),
        tyre_life: parseInt(document.getElementById('compTyreLife').value),
        position: parseInt(document.getElementById('compPosition').value),
        track_temp: parseFloat(document.getElementById('compTrackTemp').value),
        driver: document.getElementById('compDriver').value,
        team: document.getElementById('compTeam').value,
        event_name: document.getElementById('compEvent').value
    };

    try {
        const response = await fetch(`${API_URL}/api/v1/analytics/tyre-comparison`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        const data = await response.json();

        // Display results
        let html = `
            <div class="comparison-summary">
                <h4>🏆 Recommended: ${data.recommended_compound}</h4>
                <p>${data.analysis}</p>
            </div>
            <div class="comparison-table">
                <table>
                    <thead>
                        <tr>
                            <th>Compound</th>
                            <th>Lap Time</th>
                            <th>Pit Probability</th>
                            <th>Laps Until Pit</th>
                            <th>Delta vs SOFT</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.comparison.forEach(comp => {
            const delta = data.time_delta_to_soft[comp.compound];
            const deltaStr = delta > 0 ? `+${delta.toFixed(3)}s` : `${delta.toFixed(3)}s`;
            const rowClass = comp.compound === data.recommended_compound ? 'highlight' : '';

            html += `
                <tr class="${rowClass}">
                    <td><strong>${comp.compound}</strong></td>
                    <td>${comp.predicted_lap_time.toFixed(2)}s</td>
                    <td>${(comp.pit_probability * 100).toFixed(1)}%</td>
                    <td>${comp.laps_until_pit.toFixed(1)}</td>
                    <td>${deltaStr}</td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';

        document.getElementById('compResults').innerHTML = html;

    } catch (error) {
        document.getElementById('compResults').innerHTML =
            `<p class="error">Comparison error: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

// ============================================================================
// TAB 4: MODEL INFO & PERFORMANCE
// ============================================================================

async function loadModelInfo() {
    showLoading();

    try {
        const response = await fetch(`${API_URL}/api/v1/models/info`);
        const data = await response.json();

        let html = '<div class="model-grid">';

        Object.entries(data.models).forEach(([id, info]) => {
            html += `
                <div class="model-card">
                    <h4>${info.name}</h4>
                    <p><strong>Algorithm:</strong> ${info.algorithm}</p>
                    <p><strong>Purpose:</strong> ${info.purpose}</p>
                    <p><strong>File Size:</strong> ${info.file_size_mb} MB</p>
                    ${info.expected_roc_auc ? `<p><strong>ROC-AUC:</strong> ${info.expected_roc_auc}</p>` : ''}
                    ${info.expected_mae ? `<p><strong>MAE:</strong> ${info.expected_mae}</p>` : ''}
                    ${info.generates_meta_feature ? `<p class="meta">🔗 Generates: ${info.generates_meta_feature}</p>` : ''}
                    ${info.uses_meta_feature ? `<p class="meta">⬅️ Uses: ${info.uses_meta_feature}</p>` : ''}
                </div>
            `;
        });

        html += '</div>';
        html += `<p class="info-text">Meta-Feature Pipeline: ${data.meta_feature_pipeline}</p>`;

        document.getElementById('modelInfo').innerHTML = html;

    } catch (error) {
        document.getElementById('modelInfo').innerHTML =
            `<p class="error">Error loading model info: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

async function loadPerformance() {
    showLoading();

    try {
        const response = await fetch(`${API_URL}/api/v1/models/performance`);
        const data = await response.json();

        let html = `
            <div class="perf-summary">
                <p><strong>Test Year:</strong> ${data.test_year}</p>
                <p><strong>Test Samples:</strong> ${data.test_samples.toLocaleString()}</p>
            </div>
            <div class="perf-grid">
        `;

        // M1
        html += `
            <div class="perf-card">
                <h4>M1: Lap Time</h4>
                <p>MAE: ${data.metrics.m1_lap_time.mae_seconds}s</p>
                <p>RMSE: ${data.metrics.m1_lap_time.rmse_seconds}s</p>
                <p class="interpretation">${data.metrics.m1_lap_time.interpretation}</p>
            </div>
        `;

        // M2
        html += `
            <div class="perf-card">
                <h4>M2: Pit Lap</h4>
                <p>ROC-AUC: ${data.metrics.m2_pit_lap.roc_auc.toFixed(4)}</p>
                <p>F1 Score: ${data.metrics.m2_pit_lap.f1_score.toFixed(4)}</p>
                <p class="interpretation">${data.metrics.m2_pit_lap.interpretation}</p>
            </div>
        `;

        // M3
        html += `
            <div class="perf-card">
                <h4>M3: Pit-in-3</h4>
                <p>ROC-AUC: ${data.metrics.m3_pit_in_3.roc_auc.toFixed(4)}</p>
                <p>F1 Score: ${data.metrics.m3_pit_in_3.f1_score.toFixed(4)}</p>
                <p class="interpretation">${data.metrics.m3_pit_in_3.interpretation}</p>
            </div>
        `;

        // M4
        html += `
            <div class="perf-card">
                <h4>M4: Long Horizon</h4>
                <p>MAE: ${data.metrics.m4_long_horizon.mae_laps.toFixed(2)} laps</p>
                <p>RMSE: ${data.metrics.m4_long_horizon.rmse_laps.toFixed(2)} laps</p>
                <p class="interpretation">${data.metrics.m4_long_horizon.interpretation}</p>
            </div>
        `;

        // M5
        html += `
            <div class="perf-card">
                <h4>M5: Short Horizon</h4>
                <p>MAE: ${data.metrics.m5_short_horizon.mae_laps.toFixed(2)} laps</p>
                <p>RMSE: ${data.metrics.m5_short_horizon.rmse_laps.toFixed(2)} laps</p>
                <p class="interpretation">${data.metrics.m5_short_horizon.interpretation}</p>
            </div>
        `;

        html += '</div>';

        document.getElementById('modelPerformance').innerHTML = html;

    } catch (error) {
        document.getElementById('modelPerformance').innerHTML =
            `<p class="error">Error loading performance: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

// Driver change handlers - auto-update team
document.addEventListener('DOMContentLoaded', () => {
    // Tab 1: Predict
    const driverSelect = document.getElementById('driver');
    const teamInput = document.getElementById('team');

    driverSelect.addEventListener('change', (e) => {
        const driver = e.target.value;
        teamInput.value = DRIVER_TEAMS[driver] || 'UNKNOWN';
    });

    // Tab 2: Race Simulation
    const simDriverSelect = document.getElementById('simDriver');
    const simTeamInput = document.getElementById('simTeam');

    simDriverSelect.addEventListener('change', (e) => {
        const driver = e.target.value;
        simTeamInput.value = DRIVER_TEAMS[driver] || 'UNKNOWN';
    });

    // Tab 3: Comparison
    const compDriverSelect = document.getElementById('compDriver');
    const compTeamInput = document.getElementById('compTeam');

    compDriverSelect.addEventListener('change', (e) => {
        const driver = e.target.value;
        compTeamInput.value = DRIVER_TEAMS[driver] || 'UNKNOWN';
    });

    console.log('F1 Strategy Engine v2.0 loaded - Driver/Team sync enabled');
});
