# 🧪 F1 Strategy Engine API - Testing Guide

## 🚀 Quick Start - 3 Ways to Test

---

## **Method 1: Browser (Easiest) - Interactive Swagger UI**

### **Step 1: Open Swagger Docs**
```
http://localhost:8000/docs
```

### **Step 2: Try Any Endpoint**

1. Click on any endpoint (green POST/GET buttons)
2. Click **"Try it out"**
3. Fill in the example data (or use defaults)
4. Click **"Execute"**
5. See the response instantly!

### **Recommended to Try First:**
- `GET /api/v1/models/info` - See all model details
- `GET /api/v1/models/performance` - View test metrics
- `POST /api/v1/predictions/single` - Make a prediction

---

## **Method 2: Command Line (curl)**

### **Test 1: Health Check** ✅
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "models_loaded": 5,
  "api_version": "2.0.0"
}
```

---

### **Test 2: Model Information** 📊
```bash
curl http://localhost:8000/api/v1/models/info | python3 -m json.tool
```

**What you'll see:**
- All 5 models details
- File sizes
- Performance expectations
- Meta-feature pipeline

---

### **Test 3: Model Performance Metrics** 📈
```bash
curl http://localhost:8000/api/v1/models/performance | python3 -m json.tool
```

**What you'll see:**
- Test set results (2024 data)
- ROC-AUC scores
- MAE/RMSE metrics
- Model interpretations

---

### **Test 4: Single Lap Prediction** 🔮
```bash
curl -X POST http://localhost:8000/api/v1/predictions/single \
  -H "Content-Type: application/json" \
  -d '{
    "LapNumber": 20,
    "Stint": 2,
    "TyreLife": 12,
    "Position": 5,
    "GridPosition": 7,
    "Compound": "MEDIUM",
    "CompoundCode": 2,
    "FreshTyre": 0,
    "TrackTemp": 45.0,
    "AirTemp": 28.0,
    "WindSpeed": 2.5,
    "Rainfall": 0,
    "IsSC": 0,
    "IsVSC": 0,
    "IsDRS": 1,
    "Rolling3LapTime": 84.5,
    "Rolling5LapTime": 84.8,
    "LapTimeDelta": -0.3,
    "PrevLapTime": 84.2,
    "LapTimeVsField": 0.0,
    "Sector1TimeSec_Delta": 0.0,
    "Sector2TimeSec_Delta": 0.0,
    "Sector3TimeSec_Delta": 0.0,
    "PositionGain": 2,
    "PrevFieldMedian": 84.5,
    "RaceTime": 1690.0,
    "GapAhead": 2.5,
    "GapBehind": 3.2,
    "IsLeader": 0,
    "IsLast": 0,
    "Team": "Red Bull Racing",
    "Driver": "VER",
    "EventName": "Monaco",
    "Year": 2024
  }' | python3 -m json.tool
```

**Expected Response:**
```json
{
  "lap_time_sec": 87.85,
  "pit_probability": 0.0065,
  "will_pit_in_3": 0.0008,
  "laps_until_pit": 2.92,
  "laps_until_pit_short": 4.30
}
```

---

### **Test 5: Strategy Recommendation** 💡
```bash
curl -X POST http://localhost:8000/api/v1/predictions/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "LapNumber": 30,
    "Stint": 2,
    "TyreLife": 25,
    "Position": 3,
    "GridPosition": 5,
    "Compound": "SOFT",
    "CompoundCode": 1,
    "FreshTyre": 0,
    "TrackTemp": 50.0,
    "AirTemp": 30.0,
    "WindSpeed": 3.0,
    "Rainfall": 0,
    "IsSC": 0,
    "IsVSC": 0,
    "IsDRS": 1,
    "Rolling3LapTime": 83.2,
    "Rolling5LapTime": 83.5,
    "LapTimeDelta": 0.5,
    "PrevLapTime": 83.8,
    "LapTimeVsField": 0.3,
    "Sector1TimeSec_Delta": 0.0,
    "Sector2TimeSec_Delta": 0.0,
    "Sector3TimeSec_Delta": 0.0,
    "PositionGain": 2,
    "PrevFieldMedian": 83.5,
    "RaceTime": 2500.0,
    "GapAhead": 1.2,
    "GapBehind": 2.8,
    "IsLeader": 0,
    "IsLast": 0,
    "Team": "Ferrari",
    "Driver": "LEC",
    "EventName": "Monza",
    "Year": 2024
  }' | python3 -m json.tool
```

---

### **Test 6: Tyre Comparison** 🏁 (NEW!)
```bash
curl -X POST http://localhost:8000/api/v1/analytics/tyre-comparison \
  -H "Content-Type: application/json" \
  -d '{
    "lap_number": 20,
    "tyre_life": 15,
    "position": 5,
    "track_temp": 45.0,
    "driver": "VER",
    "team": "Red Bull Racing",
    "event_name": "Silverstone"
  }' | python3 -m json.tool
```

**What you'll see:**
- SOFT vs MEDIUM vs HARD comparison
- Predicted lap times for each
- Recommended compound
- Time deltas

---

### **Test 7: Race Simulation** 🏎️ (NEW!)
```bash
curl -X POST http://localhost:8000/api/v1/analytics/race-simulation \
  -H "Content-Type: application/json" \
  -d '{
    "driver": "VER",
    "team": "Red Bull Racing",
    "event_name": "Monaco",
    "total_laps": 50,
    "initial_compound": "MEDIUM",
    "track_temp": 45.0
  }' | python3 -m json.tool
```

**What you'll see:**
- Full race simulation
- Automatic pit stop decisions
- Total race time
- Pit stop strategy
- Lap-by-lap breakdown

---

### **Test 8: Optimal Pit Window** 🎯 (NEW!)
```bash
curl -X POST http://localhost:8000/api/v1/analytics/optimal-pit-window \
  -H "Content-Type: application/json" \
  -d '{
    "current_lap": 20,
    "tyre_life": 18,
    "current_compound": "SOFT",
    "target_compound": "MEDIUM",
    "remaining_laps": 30,
    "position": 3,
    "driver": "LEC",
    "team": "Ferrari",
    "event_name": "Monza"
  }' | python3 -m json.tool
```

**What you'll see:**
- Recommended pit lap
- Laps to wait
- Optimality scores for next 10 laps
- Confidence level

---

## **Method 3: Python Script**

### **Create test script:**

```python
# test_api.py
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_model_info():
    """Test model info endpoint"""
    print("📊 Testing Model Info...")
    response = requests.get(f"{BASE_URL}/api/v1/models/info")
    data = response.json()
    print(f"Total Models: {data['total_models']}")
    for model_id, info in data['models'].items():
        print(f"  {model_id}: {info['name']} - {info.get('file_size_mb', 'N/A')}MB")
    print()

def test_prediction():
    """Test single prediction"""
    print("🔮 Testing Single Prediction...")
    
    race_state = {
        "LapNumber": 20,
        "Stint": 2,
        "TyreLife": 12,
        "Position": 5,
        "GridPosition": 7,
        "Compound": "MEDIUM",
        "CompoundCode": 2,
        "FreshTyre": 0,
        "TrackTemp": 45.0,
        "AirTemp": 28.0,
        "WindSpeed": 2.5,
        "Rainfall": 0,
        "IsSC": 0,
        "IsVSC": 0,
        "IsDRS": 1,
        "Rolling3LapTime": 84.5,
        "Rolling5LapTime": 84.8,
        "LapTimeDelta": -0.3,
        "PrevLapTime": 84.2,
        "LapTimeVsField": 0.0,
        "Sector1TimeSec_Delta": 0.0,
        "Sector2TimeSec_Delta": 0.0,
        "Sector3TimeSec_Delta": 0.0,
        "PositionGain": 2,
        "PrevFieldMedian": 84.5,
        "RaceTime": 1690.0,
        "GapAhead": 2.5,
        "GapBehind": 3.2,
        "IsLeader": 0,
        "IsLast": 0,
        "Team": "Red Bull Racing",
        "Driver": "VER",
        "EventName": "Monaco",
        "Year": 2024
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/predictions/single",
        json=race_state
    )
    
    pred = response.json()
    print(f"Lap Time: {pred['lap_time_sec']:.2f}s")
    print(f"Pit Probability: {pred['pit_probability']*100:.2f}%")
    print(f"Laps Until Pit: {pred['laps_until_pit']:.1f}")
    print()

def test_tyre_comparison():
    """Test tyre comparison"""
    print("🏁 Testing Tyre Comparison...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/analytics/tyre-comparison",
        json={
            "lap_number": 20,
            "tyre_life": 15,
            "position": 5,
            "track_temp": 45.0,
            "driver": "VER",
            "team": "Red Bull Racing",
            "event_name": "Silverstone"
        }
    )
    
    data = response.json()
    print(f"Recommended: {data['recommended_compound']}")
    print("\nComparison:")
    for comp in data['comparison']:
        print(f"  {comp['compound']}: {comp['predicted_lap_time']:.2f}s")
    print()

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("F1 STRATEGY ENGINE API - TEST SUITE")
    print("="*60)
    print()
    
    try:
        test_health()
        test_model_info()
        test_prediction()
        test_tyre_comparison()
        
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    run_all_tests()
```

### **Run the test:**
```bash
python3 test_api.py
```

---

## **Method 4: Frontend Testing**

### **Open the Web UI:**
```
http://localhost:8000/app/index.html
```

### **Test Flow:**
1. Fill in race parameters (lap number, tyre life, etc.)
2. Click "🔮 Predict Strategy"
3. View predictions with visual progress bars
4. Try different scenarios (change compound, temperature, etc.)

---

## 📋 **Checklist: What to Test**

### **Basic Functionality:**
- [ ] Health check returns `models_loaded: 5`
- [ ] Model info shows all 5 models
- [ ] Performance metrics display correctly
- [ ] Single prediction works

### **New Features:**
- [ ] Batch prediction (multiple states)
- [ ] Tyre comparison (SOFT vs MEDIUM vs HARD)
- [ ] Race simulation (50 laps)
- [ ] Optimal pit window calculation
- [ ] Strategy recommendations

### **Edge Cases:**
- [ ] High tyre life (>30 laps)
- [ ] Low tyre life (<5 laps)
- [ ] Different weather (rain, high temp)
- [ ] Safety car scenarios
- [ ] Different compounds

---

## 🐛 **Troubleshooting**

### **Issue: "Connection refused"**
**Solution:**
```bash
# Check if server is running
ps aux | grep uvicorn

# If not running, start it
cd "/Users/yajatpawar/Desktop/F1 Strategy Simulation"
export MLFLOW_ALLOW_FILE_STORE=true
uvicorn api.main_v2:app --reload --port 8000
```

### **Issue: "Models not loaded" (503 error)**
**Solution:**
```bash
# Check if models exist
ls -lh data/registry/*.pkl

# Restart server
pkill -f uvicorn
uvicorn api.main_v2:app --reload --port 8000
```

### **Issue: "Invalid request" (422 error)**
**Cause:** Missing required fields

**Solution:** Use Swagger UI (`/docs`) to see exact schema requirements

---

## ⚡ **Quick Test Commands**

Copy-paste these for instant testing:

### **1. Quick Health:**
```bash
curl http://localhost:8000/health
```

### **2. Quick Info:**
```bash
curl http://localhost:8000/api/v1/models/info | python3 -m json.tool | head -30
```

### **3. Quick Prediction:**
```bash
curl -X POST http://localhost:8000/api/v1/predictions/single \
  -H "Content-Type: application/json" \
  -d '{"LapNumber":20,"Stint":2,"TyreLife":12,"Position":5,"GridPosition":7,"Compound":"MEDIUM","CompoundCode":2,"FreshTyre":0,"TrackTemp":45.0,"AirTemp":28.0,"WindSpeed":2.5,"Rainfall":0,"IsSC":0,"IsVSC":0,"IsDRS":1,"Rolling3LapTime":84.5,"Rolling5LapTime":84.8,"LapTimeDelta":-0.3,"PrevLapTime":84.2,"LapTimeVsField":0.0,"Sector1TimeSec_Delta":0.0,"Sector2TimeSec_Delta":0.0,"Sector3TimeSec_Delta":0.0,"PositionGain":2,"PrevFieldMedian":84.5,"RaceTime":1690.0,"GapAhead":2.5,"GapBehind":3.2,"IsLeader":0,"IsLast":0,"Team":"Red Bull Racing","Driver":"VER","EventName":"Monaco","Year":2024}'
```

---

## 📊 **Expected Results Summary**

| Test | Expected Result |
|------|----------------|
| Health | `models_loaded: 5` |
| Model Info | 5 models with file sizes |
| Performance | Test metrics for all models |
| Prediction | Lap time + probabilities + laps until pit |
| Tyre Compare | SOFT/MEDIUM/HARD comparison |
| Race Sim | Full race with pit stops |
| Pit Window | Optimal lap recommendation |

---

## 🎯 **Recommended Testing Order**

1. **Health** - Verify server is running
2. **Model Info** - Confirm all models loaded
3. **Performance** - Check metrics
4. **Single Prediction** - Basic functionality
5. **Tyre Comparison** - Test new analytics
6. **Race Simulation** - Test complex feature
7. **Frontend** - Visual testing

---

**✅ Ready to test!** Start with: **http://localhost:8000/docs**
