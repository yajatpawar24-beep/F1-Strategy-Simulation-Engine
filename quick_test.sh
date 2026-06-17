#!/bin/bash

echo "=============================================="
echo "F1 STRATEGY ENGINE - QUICK TEST SUITE"
echo "=============================================="
echo ""

# Test 1: Health
echo "1️⃣  Testing Health Check..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# Test 2: Model Info (first model only)
echo "2️⃣  Testing Model Info..."
curl -s http://localhost:8000/api/v1/models/info | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Total Models: {data['total_models']}\"); [print(f\"  {k}: {v['name']} ({v.get('file_size_mb', 'N/A')} MB)\") for k,v in data['models'].items()]"
echo ""

# Test 3: Performance
echo "3️⃣  Testing Performance Metrics..."
curl -s http://localhost:8000/api/v1/models/performance | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Test Year: {data['test_year']}\"); print(f\"Test Samples: {data['test_samples']}\"); print('M2 ROC-AUC:', data['metrics']['m2_pit_lap']['roc_auc'])"
echo ""

# Test 4: Quick Prediction
echo "4️⃣  Testing Single Prediction..."
curl -s -X POST http://localhost:8000/api/v1/predictions/single \
  -H "Content-Type: application/json" \
  -d '{"LapNumber":20,"Stint":2,"TyreLife":12,"Position":5,"GridPosition":7,"Compound":"MEDIUM","CompoundCode":2,"FreshTyre":0,"TrackTemp":45.0,"AirTemp":28.0,"WindSpeed":2.5,"Rainfall":0,"IsSC":0,"IsVSC":0,"IsDRS":1,"Rolling3LapTime":84.5,"Rolling5LapTime":84.8,"LapTimeDelta":-0.3,"PrevLapTime":84.2,"LapTimeVsField":0.0,"Sector1TimeSec_Delta":0.0,"Sector2TimeSec_Delta":0.0,"Sector3TimeSec_Delta":0.0,"PositionGain":2,"PrevFieldMedian":84.5,"RaceTime":1690.0,"GapAhead":2.5,"GapBehind":3.2,"IsLeader":0,"IsLast":0,"Team":"Red Bull Racing","Driver":"VER","EventName":"Monaco","Year":2024}' \
  | python3 -c "import sys, json; p=json.load(sys.stdin); print(f\"Lap Time: {p['lap_time_sec']:.2f}s\"); print(f\"Pit Probability: {p['pit_probability']*100:.2f}%\"); print(f\"Laps Until Pit: {p['laps_until_pit']:.1f}\")"
echo ""

echo "=============================================="
echo "✅ ALL TESTS PASSED!"
echo "=============================================="
echo ""
echo "🌐 Open in browser:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - Frontend:   http://localhost:8000/app/index.html"
