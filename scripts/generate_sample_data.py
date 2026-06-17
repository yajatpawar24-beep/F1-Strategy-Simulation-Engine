"""Generate sample F1 dataset for testing (if you don't have real data yet)."""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

def generate_sample_f1_data(n_races=10, laps_per_race=50, drivers_per_race=20):
    """
    Generate synthetic F1 race data for testing the pipeline.

    Args:
        n_races: Number of races to generate
        laps_per_race: Laps per race
        drivers_per_race: Drivers per race

    Returns:
        DataFrame with synthetic F1 data
    """
    print(f"Generating synthetic F1 dataset...")
    print(f"  Races: {n_races}")
    print(f"  Laps per race: {laps_per_race}")
    print(f"  Drivers per race: {drivers_per_race}")

    teams = [
        "Red Bull Racing", "Ferrari", "Mercedes", "McLaren", "Aston Martin",
        "Alpine", "Williams", "AlphaTauri", "Alfa Romeo", "Haas"
    ]

    drivers = [
        "Max Verstappen", "Sergio Perez", "Charles Leclerc", "Carlos Sainz",
        "Lewis Hamilton", "George Russell", "Lando Norris", "Oscar Piastri",
        "Fernando Alonso", "Lance Stroll", "Pierre Gasly", "Esteban Ocon",
        "Alex Albon", "Logan Sargeant", "Yuki Tsunoda", "Daniel Ricciardo",
        "Valtteri Bottas", "Zhou Guanyu", "Kevin Magnussen", "Nico Hulkenberg"
    ]

    events = [
        "Bahrain Grand Prix", "Saudi Arabian Grand Prix", "Australian Grand Prix",
        "Japanese Grand Prix", "Chinese Grand Prix", "Miami Grand Prix",
        "Monaco Grand Prix", "Spanish Grand Prix", "Canadian Grand Prix",
        "Austrian Grand Prix"
    ]

    compounds = ["SOFT", "MEDIUM", "HARD"]

    data = []

    for year in [2022, 2023, 2024]:
        for race_idx in range(n_races):
            event = events[race_idx % len(events)]

            # Random race conditions
            track_temp = np.random.uniform(30, 50)
            air_temp = np.random.uniform(20, 35)
            wind_speed = np.random.uniform(0, 5)
            rainfall = np.random.choice([0, 1], p=[0.9, 0.1])

            for driver_idx in range(drivers_per_race):
                driver = drivers[driver_idx]
                team = teams[driver_idx // 2]
                grid_position = driver_idx + 1

                # Simulate race
                current_position = grid_position
                stint = 1
                tyre_life = 0
                compound = np.random.choice(compounds)

                for lap in range(1, laps_per_race + 1):
                    # Pit stop logic
                    if tyre_life > 20 + np.random.randint(-5, 5):
                        is_pit_lap = 1
                        stint += 1
                        tyre_life = 0
                        compound = np.random.choice(compounds)
                    else:
                        is_pit_lap = 0

                    # Lap time (base + tyre deg + position effect)
                    base_lap_time = 80 + np.random.normal(0, 2)
                    tyre_deg = tyre_life * 0.05
                    position_effect = (current_position - 1) * 0.1
                    lap_time_sec = base_lap_time + tyre_deg + position_effect + np.random.normal(0, 0.5)

                    # Sector times (approximately 1/3 each)
                    sector1 = lap_time_sec / 3 + np.random.normal(0, 0.3)
                    sector2 = lap_time_sec / 3 + np.random.normal(0, 0.3)
                    sector3 = lap_time_sec / 3 + np.random.normal(0, 0.3)

                    # Safety car (rare)
                    is_sc = 1 if np.random.random() < 0.05 else 0

                    # DRS (available if not in top position and not SC)
                    is_drs = 1 if current_position > 1 and is_sc == 0 else 0

                    # Compound code
                    compound_code = {"SOFT": 1, "MEDIUM": 2, "HARD": 3}[compound]

                    # Calculate laps until next pit
                    expected_tyre_life = {"SOFT": 18, "MEDIUM": 28, "HARD": 38}[compound]
                    laps_until_next_pit = max(1, expected_tyre_life - tyre_life + np.random.randint(-3, 3))

                    data.append({
                        "Year": year,
                        "RoundNumber": race_idx + 1,
                        "EventName": event,
                        "Driver": driver,
                        "DriverNumber": driver_idx + 1,
                        "Team": team,
                        "LapNumber": lap,
                        "Stint": stint,
                        "Position": current_position,
                        "GridPosition": grid_position,
                        "LapTimeSec": lap_time_sec,
                        "Sector1TimeSec": sector1,
                        "Sector2TimeSec": sector2,
                        "Sector3TimeSec": sector3,
                        "Compound": compound,
                        "CompoundCode": compound_code,
                        "TyreLife": tyre_life,
                        "FreshTyre": 1 if tyre_life == 0 else 0,
                        "TrackTemp": track_temp,
                        "AirTemp": air_temp,
                        "WindSpeed": wind_speed,
                        "Rainfall": rainfall,
                        "IsSC": is_sc,
                        "IsVSC": 0,
                        "IsDRS": is_drs,
                        "IsPersonalBest": 0,
                        "IsPitLap": is_pit_lap,
                        "LapsUntilNextPit": laps_until_next_pit,
                    })

                    tyre_life += 1

                    # Small position changes
                    if np.random.random() < 0.1:
                        current_position = max(1, min(drivers_per_race,
                                                    current_position + np.random.choice([-1, 1])))

    df = pd.DataFrame(data)
    print(f"\n✓ Generated {len(df)} laps")
    print(f"  Shape: {df.shape}")
    return df


def main():
    output_path = Path(__file__).parent.parent / "data" / "raw" / "f1_strategy_final_dataset.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_sample_f1_data(n_races=10, laps_per_race=50, drivers_per_race=20)
    df.to_csv(output_path, index=False)

    print(f"\n✅ Sample dataset saved to: {output_path}")
    print(f"\nColumn summary:")
    print(df.info())
    print(f"\nFirst few rows:")
    print(df.head(3))


if __name__ == "__main__":
    main()
