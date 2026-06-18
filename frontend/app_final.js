// F1 Strategy Engine - Final Version with Visuals
const API_URL = 'http://localhost:8000';

// Driver-to-Team mapping with numbers
const DRIVER_DATA = {
    'VER': { team: 'Red Bull Racing', number: 33, fullName: 'MAX VERSTAPPEN', color: 0x0600ef },
    'PER': { team: 'Red Bull Racing', number: 11, fullName: 'SERGIO PEREZ', color: 0x0600ef },
    'HAM': { team: 'Mercedes', number: 44, fullName: 'LEWIS HAMILTON', color: 0x00D2BE },
    'RUS': { team: 'Mercedes', number: 63, fullName: 'GEORGE RUSSELL', color: 0x00D2BE },
    'LEC': { team: 'Ferrari', number: 16, fullName: 'CHARLES LECLERC', color: 0xDC0000 },
    'SAI': { team: 'Ferrari', number: 55, fullName: 'CARLOS SAINZ', color: 0xDC0000 },
    'NOR': { team: 'McLaren', number: 4, fullName: 'LANDO NORRIS', color: 0xFF8700 },
    'PIA': { team: 'McLaren', number: 81, fullName: 'OSCAR PIASTRI', color: 0xFF8700 },
    'ALO': { team: 'Aston Martin', number: 14, fullName: 'FERNANDO ALONSO', color: 0x006F62 },
    'STR': { team: 'Aston Martin', number: 18, fullName: 'LANCE STROLL', color: 0x006F62 }
};

// Team colors for carousel
const TEAM_COLORS = {
    'Red Bull Racing': '#0600ef',
    'Mercedes': '#00D2BE',
    'Ferrari': '#DC0000',
    'McLaren': '#FF8700',
    'Aston Martin': '#006F62',
    'Alpine': '#0090FF'
};

let carScene, carCamera, carRenderer, carGroup;

// Initialize 3D Car
function init3DCar(teamColor = 0x0600ef) {
    const container = document.getElementById('carContainer');
    container.innerHTML = '';
    
    const width = container.clientWidth;
    const height = 200;

    carScene = new THREE.Scene();
    carCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    carCamera.position.set(4, 3, 4);
    carCamera.lookAt(0, 0, 0);

    carRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    carRenderer.setSize(width, height);
    container.appendChild(carRenderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    carScene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 7.5);
    carScene.add(directionalLight);

    carGroup = new THREE.Group();
    carScene.add(carGroup);

    // F1 Car Body
    const bodyGeom = new THREE.BoxGeometry(2.5, 0.3, 0.8);
    const bodyMat = new THREE.MeshPhongMaterial({ color: teamColor });
    const body = new THREE.Mesh(bodyGeom, bodyMat);
    carGroup.add(body);

    // Nose
    const noseGeom = new THREE.BoxGeometry(1, 0.15, 0.4);
    const nose = new THREE.Mesh(noseGeom, bodyMat);
    nose.position.x = 1.7;
    carGroup.add(nose);

    // Front Wing
    const wingGeom = new THREE.BoxGeometry(0.2, 0.05, 1.8);
    const wingMat = new THREE.MeshPhongMaterial({ color: 0x15151e });
    const frontWing = new THREE.Mesh(wingGeom, wingMat);
    frontWing.position.x = 2.2;
    carGroup.add(frontWing);

    // Rear Wing
    const rearWing = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.4, 1.2), wingMat);
    rearWing.position.x = -1.1;
    rearWing.position.y = 0.3;
    carGroup.add(rearWing);

    // Wheels
    const wheelGeom = new THREE.CylinderGeometry(0.35, 0.35, 0.3, 32);
    const wheelMat = new THREE.MeshPhongMaterial({ color: 0x333333 });
    const positions = [
        [1.2, -0.1, 0.6], [1.2, -0.1, -0.6],
        [-0.8, -0.1, 0.7], [-0.8, -0.1, -0.7]
    ];
    positions.forEach(pos => {
        const wheel = new THREE.Mesh(wheelGeom, wheelMat);
        wheel.rotation.x = Math.PI / 2;
        wheel.position.set(...pos);
        carGroup.add(wheel);
    });

    animate3DCar();
}

function animate3DCar() {
    requestAnimationFrame(animate3DCar);
    if (carGroup) {
        carGroup.rotation.y += 0.005;
    }
    if (carRenderer && carScene && carCamera) {
        carRenderer.render(carScene, carCamera);
    }
}

// Update driver display
function updateDriverDisplay(driverCode) {
    const data = DRIVER_DATA[driverCode] || DRIVER_DATA['VER'];
    document.getElementById('driverName').textContent = data.fullName;
    document.getElementById('driverNumber').textContent = `#${data.number}`;
    document.getElementById('driverTeam').textContent = data.team;
    
    // Update 3D car color
    init3DCar(data.color);
}

// Initialize team cars carousel
function initTeamCarsCarousel() {
    const container = document.getElementById('teamCarsCarousel');
    const teams = [
        { name: 'Red Bull Racing', color: '#0600ef' },
        { name: 'Mercedes', color: '#00D2BE' },
        { name: 'Ferrari', color: '#DC0000' },
        { name: 'McLaren', color: '#FF8700' },
        { name: 'Aston Martin', color: '#006F62' },
        { name: 'Alpine', color: '#0090FF' }
    ];

    teams.forEach(team => {
        const card = document.createElement('div');
        card.className = 'team-car-card';
        card.innerHTML = `
            <div class="team-car-mini" style="background: linear-gradient(135deg, ${team.color} 0%, ${team.color}CC 100%);"></div>
            <p class="text-xs font-bold text-gray-900 text-center">${team.name}</p>
        `;
        container.appendChild(card);
    });
}

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

// Driver Selection
document.getElementById('driver').addEventListener('change', (e) => {
    const driver = e.target.value;
    const data = DRIVER_DATA[driver];
    document.getElementById('team').value = data.team;
    updateDriverDisplay(driver);
});

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
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        document.getElementById('predLapTime').textContent = `${result.lap_time_sec.toFixed(2)}s`;
        
        const tyreWear = result.tyre_wear_pct.toFixed(1);
        document.getElementById('predTyreWear').textContent = `${tyreWear}%`;
        
        const tyreWearBar = document.getElementById('predTyreWearBar');
        tyreWearBar.style.width = `${tyreWear}%`;
        tyreWearBar.className = `progress-bar-fill h-4 rounded-full ${result.pit_urgency >= 80 ? 'high' : result.pit_urgency >= 60 ? 'medium' : 'low'}`;
        
        document.getElementById('predPitUrgency').textContent = `${result.pit_urgency.toFixed(0)}/100`;
        document.getElementById('predOptimalPit').textContent = `Lap ${result.optimal_pit_lap}`;
        document.getElementById('predRecommendation').textContent = result.recommendation;

    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Initialize on page load
window.addEventListener('load', () => {
    init3DCar();
    initTeamCarsCarousel();
    updateDriverDisplay('VER');
    console.log('F1 Strategy Engine - Final Version Loaded');
});
