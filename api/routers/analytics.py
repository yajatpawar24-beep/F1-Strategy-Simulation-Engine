"""Analytics endpoints - race analysis, driver comparisons, what-if scenarios."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import pandas as pd
from datetime import datetime

from api.dependencies import get_predictor

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/race-simulation", summary="Full Race Simulation")
async def simulate_race(
    driver: str,
    team: str,
    event_name: str,
    total_laps: int,
    initial_compound: str = "MEDIUM",
    track_temp: float = 45.0,
    predictor = Depends(get_predictor)
):
    """
    Simulate an entire race with dynamic strategy decisions.

    **Features:**
    - Lap-by-lap predictions
    - Automatic pit stop suggestions
    - Tyre degradation tracking
    - Strategy optimization

    **Example:** Simulate Monaco GP (78 laps) with MEDIUM tyres
    """
    if total_laps > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 laps per simulation")

    try:
        simulation_results = []
        current_compound = initial_compound
        current_tyre_life = 0
        stint = 1
        pit_stops = []

        for lap in range(1, total_laps + 1):
            # Build COMPLETE race state with ALL required features
            race_state = {
                # Race progress
                "LapNumber": lap,
                "Stint": stint,
                "TyreLife": current_tyre_life,

                # Position
                "Position": 5,
                "GridPosition": 5,
                "PositionGain": 0,
                "IsLeader": 0,
                "IsLast": 0,

                # Gaps (required by enrich_dataset)
                "GapAhead": 2.0,
                "GapBehind": 2.5,

                # Tyre
                "Compound": current_compound,
                "CompoundCode": {"SOFT": 1, "MEDIUM": 2, "HARD": 3}.get(current_compound, 2),
                "FreshTyre": 1 if current_tyre_life == 0 else 0,

                # Weather
                "TrackTemp": track_temp,
                "AirTemp": 28.0,
                "WindSpeed": 2.5,
                "Rainfall": 0,

                # Flags
                "IsSC": 0,
                "IsVSC": 0,
                "IsDRS": 1,

                # Rolling/Lag timing features (required)
                "Rolling3LapTime": 84.5,
                "Rolling5LapTime": 84.8,
                "LapTimeDelta": 0.0,
                "PrevLapTime": 84.2,
                "LapTimeVsField": 0.0,
                "PrevFieldMedian": 84.5,
                "RaceTime": lap * 84.5,

                # Sector deltas (required)
                "Sector1TimeSec_Delta": 0.0,
                "Sector2TimeSec_Delta": 0.0,
                "Sector3TimeSec_Delta": 0.0,

                # Identity
                "Team": team,
                "Driver": driver,
                "EventName": event_name,
                "Year": 2024
            }

            # Get prediction
            pred = predictor.predict_single_lap(race_state)

            # Decision: Should pit?
            should_pit = (pred["pit_probability"] > 0.7 or
                         pred["laps_until_pit"] < 2 or
                         current_tyre_life > 25)

            simulation_results.append({
                "lap": lap,
                "stint": stint,
                "tyre_life": current_tyre_life,
                "compound": current_compound,
                "predicted_lap_time": pred["lap_time_sec"],
                "pit_probability": pred["pit_probability"],
                "should_pit": should_pit
            })

            # Simulate pit stop
            if should_pit and lap < total_laps - 5:
                pit_stops.append({
                    "lap": lap,
                    "compound_change": f"{current_compound} → MEDIUM",
                    "reason": "High degradation" if current_tyre_life > 25 else "Model recommendation"
                })
                current_compound = "MEDIUM"  # Simplified
                current_tyre_life = 0
                stint += 1
            else:
                current_tyre_life += 1

        # Calculate summary
        total_time = sum(r["predicted_lap_time"] for r in simulation_results)

        return {
            "driver": driver,
            "team": team,
            "event": event_name,
            "total_laps": total_laps,
            "total_time_sec": round(total_time, 2),
            "total_time_seconds": round(total_time, 2),
            "total_time_formatted": f"{int(total_time // 60)}:{int(total_time % 60):02d}",
            "pit_stops": len(pit_stops),
            "pit_stop_laps": pit_stops,
            "avg_lap_time": round(total_time / total_laps, 2),
            "simulation_results": simulation_results[:10],
            "full_results_count": len(simulation_results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.post("/tyre-comparison", summary="Compare Tyre Compounds")
async def compare_tyres(
    lap_number: int,
    tyre_life: int,
    position: int,
    track_temp: float,
    driver: str,
    team: str,
    event_name: str,
    predictor = Depends(get_predictor)
):
    """
    Compare performance predictions across different tyre compounds.

    **Compares:** SOFT vs MEDIUM vs HARD
    **Useful for:** Pit strategy decisions
    """
    try:
        compounds = ["SOFT", "MEDIUM", "HARD"]
        compound_codes = {"SOFT": 1, "MEDIUM": 2, "HARD": 3}

        results = []
        for compound in compounds:
            # Build COMPLETE race state with ALL required features
            race_state = {
                # Race progress
                "LapNumber": lap_number,
                "Stint": 2,
                "TyreLife": tyre_life,

                # Position
                "Position": position,
                "GridPosition": position,
                "PositionGain": 0,
                "IsLeader": 1 if position == 1 else 0,
                "IsLast": 0,

                # Gaps
                "GapAhead": 2.0,
                "GapBehind": 2.5,

                # Tyre
                "Compound": compound,
                "CompoundCode": compound_codes[compound],
                "FreshTyre": 0,

                # Weather
                "TrackTemp": track_temp,
                "AirTemp": 28.0,
                "WindSpeed": 2.5,
                "Rainfall": 0,

                # Flags
                "IsSC": 0,
                "IsVSC": 0,
                "IsDRS": 1,

                # Rolling/Lag timing features
                "Rolling3LapTime": 84.5,
                "Rolling5LapTime": 84.8,
                "LapTimeDelta": 0.0,
                "PrevLapTime": 84.2,
                "LapTimeVsField": 0.0,
                "PrevFieldMedian": 84.5,
                "RaceTime": lap_number * 84.5,

                # Sector deltas
                "Sector1TimeSec_Delta": 0.0,
                "Sector2TimeSec_Delta": 0.0,
                "Sector3TimeSec_Delta": 0.0,

                # Identity
                "Team": team,
                "Driver": driver,
                "EventName": event_name,
                "Year": 2024
            }

            pred = predictor.predict_single_lap(race_state)

            results.append({
                "compound": compound,
                "predicted_lap_time": pred["lap_time_sec"],
                "pit_probability": pred["pit_probability"],
                "laps_until_pit": pred["laps_until_pit"],
                "degradation_rate": "High" if compound == "SOFT" else "Medium" if compound == "MEDIUM" else "Low"
            })

        # Find fastest compound
        fastest = min(results, key=lambda x: x["predicted_lap_time"])

        return {
            "comparison": results,
            "recommended_compound": fastest["compound"],
            "time_delta_to_soft": {
                comp["compound"]: round(comp["predicted_lap_time"] - results[0]["predicted_lap_time"], 3)
                for comp in results
            },
            "analysis": "Fastest compound: " + fastest["compound"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@router.get("/driver-insights", summary="Driver Performance Insights")
async def driver_insights(driver: str):
    """
    Get historical insights for a specific driver.

    **Note:** This endpoint requires historical data to be loaded.
    Currently returns mock data. Implement with actual driver statistics.
    """
    # Mock implementation - replace with actual data when available
    insights = {
        "driver": driver,
        "avg_pit_stops_per_race": 2.3,
        "avg_stint_length": 22.5,
        "preferred_compound": "MEDIUM",
        "tyre_management_score": 8.2,
        "consistency_rating": "High",
        "note": "Mock data - implement with actual historical analysis"
    }

    return insights


@router.post("/optimal-pit-window", summary="Find Optimal Pit Window")
async def optimal_pit_window(
    current_lap: int,
    tyre_life: int,
    current_compound: str,
    target_compound: str,
    remaining_laps: int,
    position: int,
    driver: str,
    team: str,
    event_name: str,
    predictor = Depends(get_predictor)
):
    """
    Calculate the optimal pit stop window.

    **Analyzes:**
    - Current tyre degradation
    - Traffic situation
    - Weather forecast
    - Predicted lap times

    **Returns:** Best lap to pit (next 10 laps)
    """
    try:
        window_analysis = []

        for lap_offset in range(0, min(10, remaining_laps)):
            future_lap = current_lap + lap_offset
            future_tyre_life = tyre_life + lap_offset

            # Build COMPLETE race state with ALL required features
            race_state = {
                # Race progress
                "LapNumber": future_lap,
                "Stint": 2,
                "TyreLife": future_tyre_life,

                # Position
                "Position": position,
                "GridPosition": position,
                "PositionGain": 0,
                "IsLeader": 1 if position == 1 else 0,
                "IsLast": 0,

                # Gaps
                "GapAhead": 2.0,
                "GapBehind": 2.5,

                # Tyre
                "Compound": current_compound,
                "CompoundCode": {"SOFT": 1, "MEDIUM": 2, "HARD": 3}.get(current_compound, 2),
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

                # Rolling/Lag timing features
                "Rolling3LapTime": 84.5,
                "Rolling5LapTime": 84.8,
                "LapTimeDelta": 0.0,
                "PrevLapTime": 84.2,
                "LapTimeVsField": 0.0,
                "PrevFieldMedian": 84.5,
                "RaceTime": future_lap * 84.5,

                # Sector deltas
                "Sector1TimeSec_Delta": 0.0,
                "Sector2TimeSec_Delta": 0.0,
                "Sector3TimeSec_Delta": 0.0,

                # Identity
                "Team": team,
                "Driver": driver,
                "EventName": event_name,
                "Year": 2024
            }

            pred = predictor.predict_single_lap(race_state)

            # Score: lower is better (combines lap time loss + pit risk)
            score = pred["lap_time_sec"] + (pred["pit_probability"] * 10)

            window_analysis.append({
                "lap": future_lap,
                "tyre_life_at_pit": future_tyre_life,
                "predicted_lap_time": pred["lap_time_sec"],
                "pit_risk": pred["pit_probability"],
                "optimality_score": score
            })

        # Find optimal lap (lowest score)
        optimal = min(window_analysis, key=lambda x: x["optimality_score"])

        return {
            "current_lap": current_lap,
            "recommended_lap": optimal["lap"],
            "laps_to_wait": optimal["lap"] - current_lap,
            "compound_change": f"{current_compound} → {target_compound}",
            "window_scores": window_analysis,
            "confidence": "high" if optimal["pit_risk"] > 0.5 else "medium"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pit window error: {str(e)}")
