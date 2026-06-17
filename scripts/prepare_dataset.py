"""Transform raw F1 dataset to expected format."""
import pandas as pd
import numpy as np
from pathlib import Path

def transform_dataset(input_path, output_path):
    """
    Transform downloaded F1 dataset to match expected column names.

    Expected columns by our pipeline:
    Year, RoundNumber, EventName, Driver, DriverNumber, Team, LapNumber, Stint,
    Position, GridPosition, LapTimeSec, Sector1TimeSec, Sector2TimeSec, Sector3TimeSec,
    Compound, CompoundCode, TyreLife, FreshTyre, TrackTemp, AirTemp, WindSpeed, Rainfall,
    IsSC, IsVSC, IsDRS, IsPersonalBest, IsPitLap, LapsUntilNextPit
    """
    print("Loading raw dataset...")
    df = pd.read_csv(input_path)
    print(f"  Raw shape: {df.shape}")

    # Column mapping
    df_transformed = pd.DataFrame()

    # Basic info
    df_transformed['Year'] = df['year']
    df_transformed['RoundNumber'] = df['round']
    df_transformed['EventName'] = df['circuit']
    df_transformed['Driver'] = df['name_acronym'].fillna('UNKNOWN_DRIVER')
    df_transformed['DriverNumber'] = df['driver_number']
    df_transformed['Team'] = df['team_name'].fillna('UNKNOWN_TEAM')

    # Lap info
    df_transformed['LapNumber'] = df['lap_number']
    df_transformed['Stint'] = df['stint_number'].fillna(1).astype(int)
    df_transformed['Position'] = df['finish_position'].fillna(10).astype(int)  # Approximate
    df_transformed['GridPosition'] = df['grid'].fillna(10).astype(int)

    # Lap times (convert to seconds if needed)
    df_transformed['LapTimeSec'] = df['lap_duration'].fillna(df['lap_duration'].median())
    df_transformed['Sector1TimeSec'] = df['sector_1'].fillna(df['sector_1'].median())
    df_transformed['Sector2TimeSec'] = df['sector_2'].fillna(df['sector_2'].median())
    df_transformed['Sector3TimeSec'] = df['sector_3'].fillna(df['sector_3'].median())

    # Tyre info
    df_transformed['Compound'] = df['compound'].fillna('MEDIUM')
    compound_map = {'SOFT': 1, 'MEDIUM': 2, 'HARD': 3, 'INTERMEDIATE': 4, 'WET': 5}
    df_transformed['CompoundCode'] = df['compound'].fillna('MEDIUM').map(compound_map).fillna(2).astype(int)
    df_transformed['TyreLife'] = df['tyre_life'].fillna(1).astype(int)
    df_transformed['FreshTyre'] = (df['tyre_life'] == 1).astype(int)

    # Weather
    df_transformed['TrackTemp'] = df['track_temp'].fillna(df['track_temp'].median())
    df_transformed['AirTemp'] = df['air_temp'].fillna(df['air_temp'].median())
    df_transformed['WindSpeed'] = 2.0  # Default (not in source)
    df_transformed['Rainfall'] = df['rainfall'].fillna(0).astype(int)

    # Race control
    df_transformed['IsSC'] = 0  # Safety car (not in source)
    df_transformed['IsVSC'] = 0  # Virtual SC (not in source)
    df_transformed['IsDRS'] = (df_transformed['Position'] > 1).astype(int)
    df_transformed['IsPersonalBest'] = 0

    # Pit info
    df_transformed['IsPitLap'] = df['pitted'].fillna(0).astype(int)

    # Calculate LapsUntilNextPit (simplified - needs proper calculation)
    print("Calculating LapsUntilNextPit...")
    df_transformed['LapsUntilNextPit'] = 20  # Placeholder

    # Proper calculation by group
    for (year, event, driver), group in df_transformed.groupby(['Year', 'EventName', 'Driver']):
        indices = group.index
        pit_laps = group[group['IsPitLap'] == 1].index.tolist()

        for idx in indices:
            lap_num = group.loc[idx, 'LapNumber']
            # Find next pit lap
            future_pits = [p for p in pit_laps if group.loc[p, 'LapNumber'] > lap_num]
            if future_pits:
                next_pit_idx = future_pits[0]
                next_pit_lap = group.loc[next_pit_idx, 'LapNumber']
                laps_until = int(next_pit_lap - lap_num)
            else:
                laps_until = 30  # Default if no more pits

            df_transformed.loc[idx, 'LapsUntilNextPit'] = laps_until

    # Remove rows with too many NaNs
    print("Cleaning dataset...")
    df_transformed = df_transformed.dropna(subset=['LapTimeSec', 'Sector1TimeSec'])

    print(f"  Transformed shape: {df_transformed.shape}")
    print(f"  Columns: {list(df_transformed.columns)}")

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_transformed.to_csv(output_path, index=False)
    print(f"\n✅ Dataset saved to: {output_path}")

    return df_transformed


def main():
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "raw" / "f1_strategy_final_dataset.csv"
    output_path = project_root / "data" / "raw" / "f1_strategy_final_dataset.csv"

    df = transform_dataset(input_path, output_path)

    print("\n" + "="*60)
    print("DATASET SUMMARY")
    print("="*60)
    print(df.info())
    print("\nFirst 3 rows:")
    print(df.head(3))


if __name__ == "__main__":
    main()
