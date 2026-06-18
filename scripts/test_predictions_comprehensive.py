"""
Comprehensive prediction testing - 10 diverse scenarios
Tests the strategic prediction endpoint with various race conditions
"""
import requests
import json
from typing import Dict, List

API_URL = "http://localhost:8000"

# Test scenarios covering diverse conditions
TEST_SCENARIOS = [
    {
        "name": "Early Race - Fresh Softs - VER Monaco",
        "LapNumber": 5,
        "Stint": 1,
        "TyreLife": 3,
        "Position": 1,
        "GridPosition": 1,
        "Compound": "SOFT",
        "TrackTemp": 35.0,
        "AirTemp": 25.0,
        "Driver": "VER",
        "Team": "Red Bull Racing",
        "EventName": "Monte Carlo"
    },
    {
        "name": "Mid Race - Worn Mediums - HAM Silverstone",
        "LapNumber": 30,
        "Stint": 2,
        "TyreLife": 25,
        "Position": 3,
        "GridPosition": 2,
        "Compound": "MEDIUM",
        "TrackTemp": 42.0,
        "AirTemp": 28.0,
        "Driver": "HAM",
        "Team": "Mercedes",
        "EventName": "Silverstone"
    },
    {
        "name": "Late Race - Critical Hards - LEC Monza",
        "LapNumber": 48,
        "Stint": 2,
        "TyreLife": 38,
        "Position": 2,
        "GridPosition": 4,
        "Compound": "HARD",
        "TrackTemp": 48.0,
        "AirTemp": 32.0,
        "Driver": "LEC",
        "Team": "Ferrari",
        "EventName": "Monza"
    },
    {
        "name": "Early Stint - New Hards - NOR Spa",
        "LapNumber": 25,
        "Stint": 2,
        "TyreLife": 2,
        "Position": 4,
        "GridPosition": 3,
        "Compound": "HARD",
        "TrackTemp": 38.0,
        "AirTemp": 22.0,
        "Driver": "NOR",
        "Team": "McLaren",
        "EventName": "Spa-Francorchamps"
    },
    {
        "name": "Hot Conditions - Worn Softs - ALO Singapore",
        "LapNumber": 15,
        "Stint": 1,
        "TyreLife": 15,
        "Position": 6,
        "GridPosition": 8,
        "Compound": "SOFT",
        "TrackTemp": 52.0,
        "AirTemp": 35.0,
        "Driver": "ALO",
        "Team": "Aston Martin",
        "EventName": "Singapore"
    },
    {
        "name": "Back of Grid - Fresh Mediums - BOT Suzuka",
        "LapNumber": 10,
        "Stint": 1,
        "TyreLife": 8,
        "Position": 18,
        "GridPosition": 20,
        "Compound": "MEDIUM",
        "TrackTemp": 36.0,
        "AirTemp": 24.0,
        "Driver": "BOT",
        "Team": "Kick Sauber",
        "EventName": "Suzuka"
    },
    {
        "name": "Pit Window - Medium Wear - RUS Austin",
        "LapNumber": 22,
        "Stint": 1,
        "TyreLife": 20,
        "Position": 5,
        "GridPosition": 5,
        "Compound": "MEDIUM",
        "TrackTemp": 44.0,
        "AirTemp": 30.0,
        "Driver": "RUS",
        "Team": "Mercedes",
        "EventName": "Austin"
    },
    {
        "name": "Cold Track - Fresh Softs - PIA Melbourne",
        "LapNumber": 12,
        "Stint": 2,
        "TyreLife": 4,
        "Position": 7,
        "GridPosition": 6,
        "Compound": "SOFT",
        "TrackTemp": 28.0,
        "AirTemp": 18.0,
        "Driver": "PIA",
        "Team": "McLaren",
        "EventName": "Melbourne"
    },
    {
        "name": "Street Circuit - High Degradation - SAI Baku",
        "LapNumber": 35,
        "Stint": 2,
        "TyreLife": 28,
        "Position": 4,
        "GridPosition": 7,
        "Compound": "MEDIUM",
        "TrackTemp": 46.0,
        "AirTemp": 31.0,
        "Driver": "SAI",
        "Team": "Ferrari",
        "EventName": "Baku"
    },
    {
        "name": "High Speed - Late Race - PER Interlagos",
        "LapNumber": 60,
        "Stint": 3,
        "TyreLife": 18,
        "Position": 8,
        "GridPosition": 9,
        "Compound": "HARD",
        "TrackTemp": 40.0,
        "AirTemp": 26.0,
        "Driver": "PER",
        "Team": "Red Bull Racing",
        "EventName": "Interlagos"
    }
]

def create_full_race_state(scenario: Dict) -> Dict:
    """Create complete race state with all required features"""
    return {
        "LapNumber": scenario["LapNumber"],
        "Stint": scenario["Stint"],
        "TyreLife": scenario["TyreLife"],
        "Position": scenario["Position"],
        "GridPosition": scenario["GridPosition"],
        "Compound": scenario["Compound"],
        "CompoundCode": {"SOFT": 1, "MEDIUM": 2, "HARD": 3}[scenario["Compound"]],
        "FreshTyre": 0,
        "TrackTemp": scenario["TrackTemp"],
        "AirTemp": scenario["AirTemp"],
        "WindSpeed": 2.5,
        "Rainfall": 0,
        "IsSC": 0,
        "IsVSC": 0,
        "IsDRS": 1,
        "Rolling3LapTime": 84.5,
        "Rolling5LapTime": 84.8,
        "LapTimeDelta": 0.0,
        "PrevLapTime": 84.2,
        "LapTimeVsField": 0.0,
        "Sector1TimeSec_Delta": 0.0,
        "Sector2TimeSec_Delta": 0.0,
        "Sector3TimeSec_Delta": 0.0,
        "PositionGain": scenario["GridPosition"] - scenario["Position"],
        "PrevFieldMedian": 84.5,
        "RaceTime": scenario["LapNumber"] * 84.5,
        "GapAhead": 2.5,
        "GapBehind": 3.2,
        "IsLeader": 1 if scenario["Position"] == 1 else 0,
        "IsLast": 1 if scenario["Position"] == 20 else 0,
        "Team": scenario["Team"],
        "Driver": scenario["Driver"],
        "EventName": scenario["EventName"],
        "Year": 2024
    }

def test_prediction(scenario: Dict) -> Dict:
    """Run single prediction test"""
    race_state = create_full_race_state(scenario)

    try:
        response = requests.post(
            f"{API_URL}/api/v1/predictions/strategic",
            json=race_state,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "status": "SUCCESS",
                "name": scenario["name"],
                "input": {
                    "driver": scenario["Driver"],
                    "track": scenario["EventName"],
                    "lap": scenario["LapNumber"],
                    "compound": scenario["Compound"],
                    "tyre_life": scenario["TyreLife"],
                    "position": scenario["Position"]
                },
                "output": {
                    "lap_time": f"{result['lap_time_sec']:.2f}s",
                    "tyre_wear": f"{result['tyre_wear_pct']:.1f}%",
                    "pit_urgency": result['pit_urgency'],
                    "optimal_pit_lap": result['optimal_pit_lap'],
                    "should_pit_in_3": result['should_pit_in_3'],
                    "degradation_rate": result['degradation_rate'],
                    "horizon_model": result['horizon_model'],
                    "recommendation": result['recommendation']
                }
            }
        else:
            return {
                "status": "FAILED",
                "name": scenario["name"],
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except Exception as e:
        return {
            "status": "ERROR",
            "name": scenario["name"],
            "error": str(e)
        }

def analyze_results(results: List[Dict]):
    """Analyze test results and generate report"""
    print("\n" + "="*80)
    print("F1 STRATEGY ENGINE - COMPREHENSIVE PREDICTION TEST REPORT")
    print("="*80 + "\n")

    success_count = sum(1 for r in results if r["status"] == "SUCCESS")

    print(f"SUMMARY: {success_count}/{len(results)} tests passed\n")

    # Check for issues
    issues = []

    for i, result in enumerate(results, 1):
        print(f"\nTest {i}: {result['name']}")
        print("-" * 80)

        if result["status"] != "SUCCESS":
            print(f"❌ FAILED: {result['error']}")
            issues.append(f"Test {i} failed: {result['error']}")
            continue

        inp = result["input"]
        out = result["output"]

        print(f"✅ SUCCESS")
        print(f"\nInput:")
        print(f"  Driver: {inp['driver']} | Track: {inp['track']}")
        print(f"  Lap {inp['lap']} | {inp['compound']} tyres ({inp['tyre_life']} laps old) | P{inp['position']}")

        print(f"\nOutput:")
        print(f"  Lap Time: {out['lap_time']}")
        print(f"  Tyre Wear: {out['tyre_wear']} | Urgency: {out['pit_urgency']}/100")
        print(f"  Optimal Pit: Lap {out['optimal_pit_lap']} | Pit in 3 laps: {out['should_pit_in_3']}")
        print(f"  Degradation: {out['degradation_rate']} | Model: {out['horizon_model']}")
        print(f"  Recommendation: {out['recommendation']}")

        # Validation checks
        tyre_wear = float(out['tyre_wear'].rstrip('%'))
        urgency = out['pit_urgency']

        # Check tyre wear logic
        expected_life = {"SOFT": 20, "MEDIUM": 30, "HARD": 40}[inp['compound']]
        expected_wear = (inp['tyre_life'] / expected_life) * 100

        if abs(tyre_wear - expected_wear) > 5:
            warning = f"⚠️  Tyre wear {tyre_wear}% doesn't match expected {expected_wear:.1f}%"
            print(f"\n{warning}")
            issues.append(f"Test {i}: {warning}")

        # Check urgency-horizon alignment
        if urgency >= 80 and out['horizon_model'] != 'M5_SHORT':
            warning = f"⚠️  High urgency ({urgency}) should use M5_SHORT, got {out['horizon_model']}"
            print(f"\n{warning}")
            issues.append(f"Test {i}: {warning}")

        if urgency < 80 and out['horizon_model'] != 'M4_LONG':
            warning = f"⚠️  Low urgency ({urgency}) should use M4_LONG, got {out['horizon_model']}"
            print(f"\n{warning}")
            issues.append(f"Test {i}: {warning}")

        # Check should_pit_in_3 alignment
        if urgency >= 80 and not out['should_pit_in_3']:
            warning = f"⚠️  Critical urgency ({urgency}) should trigger pit in 3 laps"
            print(f"\n{warning}")
            issues.append(f"Test {i}: {warning}")

    # Final report
    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    print(f"\nTests Passed: {success_count}/{len(results)}")

    if issues:
        print(f"\n⚠️  Issues Found ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        print("\n❌ TESTING FAILED - Issues need investigation")
    else:
        print("\n✅ ALL TESTS PASSED - System working as expected!")
        print("\nKey Validations:")
        print("  ✓ All predictions returned successfully")
        print("  ✓ Tyre wear calculations match physics model")
        print("  ✓ Urgency-based horizon selection working")
        print("  ✓ Pit recommendations aligned with urgency")

    return success_count == len(results) and len(issues) == 0

if __name__ == "__main__":
    print("Starting comprehensive prediction tests...")
    print(f"Testing {len(TEST_SCENARIOS)} diverse scenarios\n")

    results = []
    for scenario in TEST_SCENARIOS:
        result = test_prediction(scenario)
        results.append(result)

    all_passed = analyze_results(results)

    exit(0 if all_passed else 1)
