# 🚨 F1 Strategy Engine - Critical Validation Issues

**Date:** 2024-06-17  
**Test Run:** Deep validation with 6 comprehensive tests  
**Status:** ❌ CRITICAL ISSUES FOUND

---

## 🔴 CRITICAL ISSUE #1: Inverted Tyre Degradation Physics

### Problem
**Worn tyres are FASTER than fresh tyres** - completely opposite of real F1 physics.

### Evidence
Test: Same car, same conditions, only TyreLife varies:

| Tyre Age | Lap Time | Expected | Actual Result |
|----------|----------|----------|---------------|
| 3 laps (fresh) | 95.017s | Should be FASTEST | ❌ SLOWEST |
| 10 laps | 85.990s | Slightly slower | ❌ Much faster |
| 20 laps (worn) | 85.798s | Noticeably slower | ❌ Even faster |
| 30 laps (very worn) | 85.625s | Should be SLOWEST | ❌ FASTEST |

**Delta:** 30-lap tyres are **9.4 seconds FASTER** than 3-lap tyres (should be ~3-5s SLOWER)

### Real F1 Physics
- Fresh tyres: Grip is HIGH → Lap times FAST
- Worn tyres (20+ laps): Grip degrades → Lap times SLOW by 1-3 seconds
- Very worn (30+ laps): Dangerous territory → 3-5 seconds slower

### Root Cause Analysis

#### Hypothesis 1: Feature Engineering Bug
The `TyreLife` feature may be:
- Incorrectly scaled (negative correlation instead of positive)
- Interacting with `LapNumber` in unexpected ways
- Missing normalization causing model to learn inverted relationship

**Check:**
```python
# In src/data/feature_engineering.py
# Look for TyreLife transformations
# Verify no accidental negative signs
```

#### Hypothesis 2: Training Data Issue
The original dataset may have:
- `TyreLife` column with incorrect values
- Outliers causing model to learn wrong patterns
- Fresh tyres labeled as old, old tyres labeled as fresh

**Check:**
```python
import pandas as pd
df = pd.read_csv('data/processed/F1_Strategy_Prediction_Dataset.csv')

# Correlation check
print(df[['TyreLife', 'LapTimeSec']].corr())
# Should be POSITIVE correlation (more TyreLife → higher LapTimeSec)

# Distribution check
df.groupby(pd.cut(df['TyreLife'], bins=[0,5,10,20,30,50]))['LapTimeSec'].mean()
```

#### Hypothesis 3: Model Learned Wrong Pattern
LightGBM/CatBoost may have:
- Overfit to noise in training data
- Feature importance showing TyreLife with negative weight
- Learned that TyreLife is inversely related to performance

**Check:**
```python
import joblib
m1 = joblib.load('data/registry/m1_pipeline.pkl')

# Get feature importance
model = m1.named_steps['model']
feature_importance = model.feature_importances_
feature_names = m1.named_steps['preprocessor'].get_feature_names_out()

# Check TyreLife weight
for i, (name, imp) in enumerate(zip(feature_names, feature_importance)):
    if 'TyreLife' in name:
        print(f"{name}: {imp}")
```

---

## 🟡 CRITICAL ISSUE #2: Inverted Pit Probability

### Problem
**Pit probability DECREASES as tyres wear** - opposite of strategy logic.

### Evidence
| Tyre Age | Pit Probability | Expected | Actual Result |
|----------|-----------------|----------|---------------|
| 3 laps | 1.90% | Very low | ✅ Correct range |
| 10 laps | 2.22% | Low | ⚠️ Higher than fresh (good) |
| 20 laps | 1.45% | Rising | ❌ DROPS below 10 laps |
| 30 laps | 0.62% | High (>50%) | ❌ LOWEST value |

### Real F1 Strategy
- Fresh tyres (0-5 laps): ~1-2% pit probability
- Medium wear (10-15 laps): ~10-20% pit probability
- High wear (20-25 laps): ~50-70% pit probability
- Critical wear (30+ laps): ~80-95% pit probability

### Root Cause
Likely cascading effect from Issue #1:
1. M2 (Pit Lap Classifier) sees TyreLife as predictor
2. If TyreLife is inverted in M1, M2 learns: "high TyreLife = good performance = no pit needed"
3. This breaks the entire strategy chain M2→M3→M4→M5

---

## 🟠 ISSUE #3: Missing Features in Analytics Endpoints

### Problem
`/api/v1/analytics/tyre-comparison` fails with:

```
"columns are missing: {
    'Sector1TimeSec_Delta', 'Sector2TimeSec_Delta', 'Sector3TimeSec_Delta',
    'GapAhead', 'GapBehind', 'IsLeader', 'IsLast', 'LapTimeVsField'
}"
```

### Root Cause
Analytics endpoints build `race_state` dicts but don't include all required features.

### Fix Location
**File:** `api/routers/analytics.py`

**Lines 146-170:** Add missing fields to `race_state` dict in `compare_tyres()`:

```python
race_state = {
    # ... existing fields ...
    "LapTimeVsField": 0.0,          # ADD
    "Sector1TimeSec_Delta": 0.0,    # ADD
    "Sector2TimeSec_Delta": 0.0,    # ADD
    "Sector3TimeSec_Delta": 0.0,    # ADD
    "GapAhead": 2.0,                # ADD
    "GapBehind": 2.5,               # ADD
    "IsLeader": 0,                  # ADD
    "IsLast": 0,                    # ADD
    "Team": team,
    "Driver": driver,
    # ... etc
}
```

**Same fix needed in:**
- `simulate_race()` function (lines 44-68)
- `optimal_pit_window()` function (if exists)

---

## 🟢 WORKING CORRECTLY

### ✅ Test 4: Model Pipeline Integrity
- All 5 models load successfully
- Predictions return valid numeric ranges
- No crashes or exceptions
- Meta-feature pipeline (M2→M3→M4) executes

### ✅ Test 5: API Health
- FastAPI server running
- All endpoints respond
- CORS configured
- Documentation accessible at `/docs`

### ✅ Test 6: Race Simulation Structure
- Full race simulation completes
- Returns realistic data structure
- Pit stop logic triggers
- Lap-by-lap tracking works

---

## 📋 RECOMMENDED FIXES (Priority Order)

### 1. **CRITICAL** - Fix Tyre Degradation Physics

#### Option A: Check Training Data
```bash
python3 << 'EOF'
import pandas as pd
import numpy as np

df = pd.read_csv('data/processed/F1_Strategy_Prediction_Dataset.csv')

# Correlation matrix
print("=== TyreLife Correlations ===")
print(df[['TyreLife', 'LapTimeSec', 'IsPitLap']].corr())

# Should see:
# TyreLife vs LapTimeSec: POSITIVE (0.3 to 0.6)
# TyreLife vs IsPitLap: POSITIVE (0.4 to 0.7)

# Group analysis
print("\n=== Lap Time by Tyre Age ===")
print(df.groupby(pd.cut(df['TyreLife'], bins=[0,5,10,20,30,50]))['LapTimeSec'].agg(['mean', 'count']))

# Should show INCREASING lap times as TyreLife increases
EOF
```

#### Option B: Check Feature Engineering
```bash
# Review feature creation
grep -n "TyreLife" src/data/feature_engineering.py

# Look for transformations like:
# - TyreLife *= -1  ❌ BAD
# - 1 / TyreLife    ❌ BAD
# - TyreLife        ✅ GOOD
```

#### Option C: Inspect Model
```python
import joblib
import pandas as pd

m1 = joblib.load('data/registry/m1_pipeline.pkl')

# Get feature importances
model = m1.named_steps['model']
importances = model.feature_importances_
features = m1.named_steps['preprocessor'].get_feature_names_out()

# Check TyreLife
tyre_features = [(f, imp) for f, imp in zip(features, importances) if 'TyreLife' in f or 'Tyre' in f]
print("TyreLife features:")
for f, imp in tyre_features:
    print(f"  {f}: {imp}")

# SHAP analysis (if time)
import shap
explainer = shap.TreeExplainer(model)
# Check if TyreLife has negative SHAP values → indicates inverted relationship
```

### 2. **HIGH** - Fix Analytics Endpoints

**File:** `api/routers/analytics.py`

Add complete feature set to all `race_state` dicts:

```python
COMPLETE_RACE_STATE_TEMPLATE = {
    # Race progress
    "LapNumber": 0,
    "Stint": 1,
    "TyreLife": 0,
    
    # Position
    "Position": 5,
    "GridPosition": 5,
    "PositionGain": 0,
    "IsLeader": 0,
    "IsLast": 0,
    
    # Gaps
    "GapAhead": 2.0,
    "GapBehind": 2.5,
    
    # Tyre
    "Compound": "MEDIUM",
    "CompoundCode": 2,
    "FreshTyre": 0,
    
    # Weather
    "TrackTemp": 45.0,
    "AirTemp": 28.0,
    "WindSpeed": 2.5,
    "Rainfall": 0,
    
    # Flags
    "IsSC": 0,
    "IsVSC": 0,
    "IsDRS": 1,
    
    # Timing
    "Rolling3LapTime": 84.5,
    "Rolling5LapTime": 84.8,
    "LapTimeDelta": 0.0,
    "PrevLapTime": 84.2,
    "LapTimeVsField": 0.0,
    "Sector1TimeSec_Delta": 0.0,
    "Sector2TimeSec_Delta": 0.0,
    "Sector3TimeSec_Delta": 0.0,
    "PrevFieldMedian": 84.5,
    "RaceTime": 1690.0,
    
    # Identity
    "Team": "Red Bull Racing",
    "Driver": "VER",
    "EventName": "Monaco",
    "Year": 2024
}
```

Then use:
```python
race_state = COMPLETE_RACE_STATE_TEMPLATE.copy()
race_state.update({
    "LapNumber": lap_number,
    "TyreLife": tyre_life,
    "Compound": compound,
    # ... only override what changes
})
```

### 3. **MEDIUM** - Validate Compound Hierarchy

Once analytics endpoints work, verify:
- SOFT < MEDIUM < HARD lap times
- SOFT > MEDIUM > HARD pit probability
- Compound choice affects strategy realistically

### 4. **LOW** - Temperature Sensitivity

Test if temperature has realistic effects:
- Hot track (55°C) → faster degradation, slower laps
- Cool track (30°C) → slower degradation, faster laps (to a point)

---

## 🧪 REVALIDATION CHECKLIST

After fixes, re-run validation:

```bash
python3 /tmp/f1_validation_report.py
```

**Must pass:**
- [ ] Lap times increase with tyre wear (correlation > 0.3)
- [ ] Pit probability increases with tyre wear
- [ ] Compound hierarchy: SOFT fastest, HARD slowest
- [ ] Analytics endpoints return valid data
- [ ] Race simulation produces realistic total time (80-120 mins)
- [ ] Pit stops recommended at sensible laps (15-30 range)

---

## 📊 CURRENT STATUS SUMMARY

| Component | Status | Issue |
|-----------|--------|-------|
| Model Pipeline | ✅ Working | All 5 models load and execute |
| API Endpoints | ✅ Working | FastAPI server responds |
| Tyre Degradation | ❌ BROKEN | Inverted physics (worn = faster) |
| Pit Probability | ❌ BROKEN | Decreases with wear |
| Compound Comparison | ❌ BROKEN | Missing features error |
| Race Simulation | ⚠️ Partially | Completes but uses broken physics |
| Frontend | ✅ Working | UI loads, connects to API |

**Overall:** System is operational but predictions are **physically incorrect** due to inverted tyre degradation model.

---

## 🎯 NEXT STEPS

1. **Immediate:** Investigate training data correlation between `TyreLife` and `LapTimeSec`
2. **Short-term:** Fix analytics endpoints with complete feature set
3. **Medium-term:** Retrain models if data issue found
4. **Long-term:** Add validation tests to CI/CD pipeline

---

**Generated:** 2024-06-17  
**Validation Framework:** 6 comprehensive tests (2 failed critically, 1 failed feature check, 3 passed)
