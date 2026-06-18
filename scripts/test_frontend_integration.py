"""
Test frontend integration with API - 5 scenarios
"""
import requests
import json

API_URL = "http://localhost:8000"

print("=" * 80)
print("F1 STRATEGY ENGINE - FRONTEND INTEGRATION TEST")
print("=" * 80)

test_scenarios = [
    {
        "name": "VER - Fresh Medium Tyres - Monaco",
        "driver": "VER",
        "team": "Red Bull Racing",
        "event": "Monte Carlo",
        "lap": 10,
        "compound": "MEDIUM",
        "tyre_life": 8,
        "position": 1
    },
    {
        "name": "HAM - Worn Softs - Silverstone",
        "driver": "HAM",
        "team": "Mercedes",
        "event": "Silverstone",
        "lap": 25,
        "compound": "SOFT",
        "tyre_life": 18,
        "position": 3
    },
    {
        "name": "LEC - Critical Mediums - Monza",
        "driver": "LEC",
        "team": "Ferrari",
        "event": "Monza",
        "lap": 40,
        "compound": "MEDIUM",
        "tyre_life": 28,
        "position": 2
    },
    {
        "name": "NOR - Fresh Hards - Spa",
        "driver": "NOR",
        "team": "McLaren",
        "event": "Spa-Francorchamps",
        "lap": 30,
        "compound": "HARD",
        "tyre_life": 5,
        "position": 4
    },
    {
        "name": "ALO - Mid-stint Mediums - Singapore",
        "driver": "ALO",
        "team": "Aston Martin",
        "event": "Singapore",
        "lap": 20,
        "compound": "MEDIUM",
        "tyre_life": 15,
        "position": 5
    }
]

passed = 0
failed = 0

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\nTest {i}: {scenario['name']}")
    print("-" * 80)
    
    race_state = {
        "LapNumber": scenario["lap"],
        "Stint": 2,
        "TyreLife": scenario["tyre_life"],
        "Position": scenario["position"],
        "GridPosition": scenario["position"] + 1,
        "Compound": scenario["compound"],
        "CompoundCode": {"SOFT": 1, "MEDIUM": 2, "HARD": 3}[scenario["compound"]],
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
        "LapTimeDelta": 0.0,
        "PrevLapTime": 84.2,
        "LapTimeVsField": 0.0,
        "Sector1TimeSec_Delta": 0.0,
        "Sector2TimeSec_Delta": 0.0,
        "Sector3TimeSec_Delta": 0.0,
        "PositionGain": 1,
        "PrevFieldMedian": 84.5,
        "RaceTime": scenario["lap"] * 84.5,
        "GapAhead": 2.5,
        "GapBehind": 3.2,
        "IsLeader": 1 if scenario["position"] == 1 else 0,
        "IsLast": 0,
        "Team": scenario["team"],
        "Driver": scenario["driver"],
        "EventName": scenario["event"],
        "Year": 2024
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/predictions/strategic",
            json=race_state,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"  Lap Time: {result['lap_time_sec']:.2f}s")
            print(f"  Tyre Wear: {result['tyre_wear_pct']:.1f}%")
            print(f"  Pit Urgency: {result['pit_urgency']:.0f}/100")
            print(f"  Optimal Pit: Lap {result['optimal_pit_lap']}")
            print(f"  Model: {result['horizon_model']}")
            print(f"  Recommendation: {result['recommendation'][:80]}...")
            passed += 1
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            failed += 1
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        failed += 1

print("\n" + "=" * 80)
print(f"RESULTS: {passed}/{len(test_scenarios)} tests passed")
if failed == 0:
    print("✅ ALL TESTS PASSED - Frontend integration working perfectly!")
else:
    print(f"⚠️  {failed} test(s) failed - check API server and logs")
print("=" * 80)
