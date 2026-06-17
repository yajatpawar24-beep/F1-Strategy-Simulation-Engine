"""Prediction endpoints - single lap and batch predictions."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
import pandas as pd
from datetime import datetime

from api.models import RaceStateInput, PredictionOutput
from api.dependencies import get_predictor, get_strategic_predictor

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/single", response_model=PredictionOutput, summary="Single Lap Prediction")
async def predict_single_lap(
    state: RaceStateInput,
    predictor = Depends(get_predictor)
):
    """
    Predict race strategy for a single lap state.

    **Returns predictions from all 5 models:**
    - M1: Lap time (seconds)
    - M2: Pit probability (this lap)
    - M3: Pit-in-3 probability (within 3 laps)
    - M4: Long-horizon laps until pit
    - M5: Short-horizon laps until pit (if applicable)
    """
    try:
        race_state = state.dict()
        predictions = predictor.predict_single_lap(race_state)
        return PredictionOutput(**predictions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/batch", summary="Batch Predictions")
async def predict_batch(
    states: List[RaceStateInput],
    background_tasks: BackgroundTasks,
    predictor = Depends(get_predictor)
):
    """
    Predict race strategy for multiple lap states (batch processing).

    **Efficient for:**
    - Analyzing full race simulations
    - Historical data analysis
    - What-if scenario comparisons

    **Limits:** Max 1000 states per request
    """
    if len(states) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 states per batch")

    try:
        # Convert to DataFrame for efficient batch processing
        states_dict = [s.dict() for s in states]
        df = pd.DataFrame(states_dict)

        # Run batch prediction
        df_with_preds = predictor.predict_batch(df)

        # Convert back to list of dicts
        predictions = df_with_preds[[
            'pred_lap_time_sec', 'pred_pit_probability',
            'pred_will_pit_in_3', 'pred_laps_until_pit',
            'pred_laps_until_pit_short'
        ]].to_dict('records')

        return {
            "count": len(predictions),
            "predictions": predictions,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")


@router.post("/recommend", summary="Strategy Recommendation")
async def recommend_strategy(
    state: RaceStateInput,
    predictor = Depends(get_predictor)
):
    """
    Get human-readable strategy recommendation with predictions.

    **Returns:**
    - Strategic recommendation text (e.g., "⚠️ HIGH PIT RISK")
    - Full prediction breakdown
    - Confidence scores
    """
    try:
        race_state = state.dict()
        predictions = predictor.predict_single_lap(race_state)
        recommendation = predictor.recommend_strategy(race_state)

        return {
            "recommendation": recommendation,
            "predictions": predictions,
            "confidence": {
                "pit_risk": "high" if predictions["pit_probability"] > 0.7
                           else "medium" if predictions["pit_probability"] > 0.4
                           else "low",
                "pit_window_opening": predictions["will_pit_in_3"] > 0.6
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")


@router.post("/compare", summary="Compare Scenarios")
async def compare_scenarios(
    scenarios: List[RaceStateInput],
    predictor = Depends(get_predictor)
):
    """
    Compare multiple race scenarios (e.g., different tyre compounds).

    **Use cases:**
    - Compare SOFT vs MEDIUM vs HARD tyres
    - Analyze different weather conditions
    - Pit now vs pit later strategies
    """
    if len(scenarios) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 scenarios per comparison")

    try:
        results = []
        for idx, scenario in enumerate(scenarios):
            race_state = scenario.dict()
            predictions = predictor.predict_single_lap(race_state)
            recommendation = predictor.recommend_strategy(race_state)

            results.append({
                "scenario_id": idx,
                "compound": scenario.Compound,
                "tyre_life": scenario.TyreLife,
                "predictions": predictions,
                "recommendation": recommendation
            })

        # Find best scenario (lowest pit risk + longest tyre life)
        best_idx = min(range(len(results)),
                      key=lambda i: results[i]["predictions"]["pit_probability"])

        return {
            "scenarios": results,
            "best_scenario_id": best_idx,
            "comparison_timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@router.post("/strategic", summary="Strategic Prediction (ML + Physics)")
async def strategic_prediction(
    state: RaceStateInput,
    strategic_predictor = Depends(get_strategic_predictor)
):
    """
    🏆 **TOP-LEVEL STRATEGIC PREDICTION** (Recommended for production use)

    Combines ML predictions with physics-based tyre degradation and strategic logic.

    **Returns:**
    - Clear pit recommendations (🔴 CRITICAL, 🟠 HIGH PRIORITY, 🟡 IN WINDOW, 🟢 STAY OUT)
    - Tyre wear percentage (0-100%)
    - Pit urgency score (0-100)
    - Optimal pit lap
    - Should pit in next 3 laps (boolean)
    - Which model to use (M4 long vs M5 short horizon)
    - Time loss vs fresh tyres

    **Key Features:**
    - Uses SOFT/MEDIUM/HARD expected life curves
    - Accounts for optimal pit windows (75-95% tyre life)
    - Provides actionable recommendations, not just probabilities
    - Handles edge cases (critical wear, late race, etc.)

    **This is what you should use for real strategy decisions!**
    """
    try:
        race_state = state.dict()
        result = strategic_predictor.predict_strategy(race_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategic prediction error: {str(e)}")
