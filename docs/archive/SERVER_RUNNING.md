# 🎉 F1 Strategy Engine - SERVER RUNNING!

## ✅ **SYSTEM STATUS: FULLY OPERATIONAL**

All 5 models trained and API server is running successfully!

---

## 🌐 **Access Your System:**

### **1. API Documentation (Interactive Swagger UI)**
```
http://localhost:8000/docs
```
- Test all endpoints interactively
- See request/response schemas
- Try predictions in real-time

### **2. Frontend UI**
```
http://localhost:8000/app/index.html
```
- Beautiful web interface
- Input race parameters
- Get real-time predictions
- Strategy recommendations

### **3. Alternative Docs (ReDoc)**
```
http://localhost:8000/redoc
```
- Clean alternative documentation

### **4. Health Check**
```
http://localhost:8000/health
```
- Returns: `{"status": "healthy", "models_loaded": 5}`

---

## 📊 **Available Endpoints:**

### **GET /**
Root endpoint with API info

### **GET /health**
Health check - confirms all 5 models are loaded

### **POST /predict**
Single lap prediction

**Example Request:**
```json
{
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
  "Team": "Red Bull Racing",
  "Driver": "VER",
  "EventName": "Monaco",
  "Year": 2024
}
```

**Example Response:**
```json
{
  "lap_time_sec": 87.85,
  "pit_probability": 0.0065,
  "will_pit_in_3": 0.0008,
  "laps_until_pit": 2.92,
  "laps_until_pit_short": 4.30
}
```

### **POST /recommend**
Get human-readable strategy recommendation

---

## 🧪 **Quick Tests:**

### **Test 1: Health Check**
```bash
curl http://localhost:8000/health
```

### **Test 2: Quick Prediction**
```bash
curl -X POST http://localhost:8000/predict \
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
    "Team": "Ferrari",
    "Driver": "LEC",
    "EventName": "Monza",
    "Year": 2024
  }'
```

---

## 🛠️ **Server Management:**

### **Stop Server:**
```bash
pkill -f "uvicorn api.main:app"
```

### **Restart Server:**
```bash
cd "/Users/yajatpawar/Desktop/F1 Strategy Simulation"
export MLFLOW_ALLOW_FILE_STORE=true
uvicorn api.main:app --reload --port 8000
```

### **View Logs:**
```bash
tail -f "/Users/yajatpawar/Desktop/F1 Strategy Simulation/api_server.log"
```

### **Check if Running:**
```bash
ps aux | grep uvicorn
# or
curl http://localhost:8000/health
```

---

## 📈 **View Training Results (MLflow):**

```bash
cd "/Users/yajatpawar/Desktop/F1 Strategy Simulation"
export MLFLOW_ALLOW_FILE_STORE=true
mlflow ui --port 5000
```

Then open: **http://localhost:5000**

---

## 🎨 **Frontend Usage:**

1. **Open** http://localhost:8000/app/index.html
2. **Fill in race parameters:**
   - Lap number, stint, tyre life
   - Position, compound, temperatures
   - Driver, team, event details
3. **Click "Predict Strategy"**
4. **View results:**
   - Lap time prediction
   - Pit probability
   - Pit-in-3 probability
   - Laps until pit
   - Strategy recommendation

---

## 📁 **Trained Models:**

All models saved in: `data/registry/`

| Model | Size | Purpose |
|-------|------|---------|
| m1_pipeline.pkl | 2.1 MB | Lap Time Prediction |
| m2_pipeline.pkl | 1.0 MB | Pit Lap Classification |
| m3_pipeline.pkl | 677 KB | Pit-in-3 Classification |
| m4_pipeline.pkl | 6.2 MB | Long Horizon Regression |
| m5_pipeline.pkl | 1.3 MB | Short Horizon Regression |

---

## 🐍 **Python Usage:**

```python
from src.inference.predictor import F1StrategyPredictor

# Initialize predictor
predictor = F1StrategyPredictor()

# Make prediction
result = predictor.predict_single_lap({
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
    "Team": "Red Bull Racing",
    "Driver": "VER",
    "EventName": "Monaco",
    "Year": 2024
})

print(result)
# {
#   "lap_time_sec": 87.85,
#   "pit_probability": 0.0065,
#   "will_pit_in_3": 0.0008,
#   "laps_until_pit": 2.92
# }

# Get recommendation
recommendation = predictor.recommend_strategy(race_state)
print(recommendation)
```

---

## 🎯 **Model Performance:**

| Model | Test Metric | Value |
|-------|------------|-------|
| M1 | Lap Time MAE | ~2.0 seconds |
| M2 | ROC-AUC | 0.9103 |
| M2 | F1 Score | 0.4883 |
| M3 | ROC-AUC | 0.8557 |
| M3 | F1 Score | 0.5589 |
| M4 | MAE | 5.76 laps |
| M4 | RMSE | 9.50 laps |
| M5 | MAE | 1.32 laps |
| M5 | RMSE | 1.87 laps |

---

## 🚀 **Next Steps:**

1. ✅ **Test the frontend** - Open http://localhost:8000/app/index.html
2. ✅ **Try different scenarios** - Vary tyre compounds, temperatures
3. ✅ **Explore Swagger docs** - http://localhost:8000/docs
4. ✅ **View MLflow experiments** - Run `mlflow ui`
5. ✅ **Batch predictions** - Run on historical races
6. ✅ **Customize frontend** - Add charts, visualizations
7. ✅ **Deploy to cloud** - AWS/GCP/Azure when ready

---

## 💡 **Tips:**

- **High pit probability** (>0.7) → Car likely pitting this lap
- **High pit-in-3** (>0.6) → Pit window opening soon
- **Low laps-until-pit** (<5) → Prepare pit stop
- **Compare M4 vs M5** → M5 more accurate for short horizon

---

**🏁 Your F1 Strategy Engine is LIVE and ready to predict!**

Server PID: Check with `ps aux | grep uvicorn`
Logs: `/Users/yajatpawar/Desktop/F1 Strategy Simulation/api_server.log`
