#!/usr/bin/env python3
"""
Fix TyreLife column in F1 dataset.

PROBLEM: TyreLife currently stores the TOTAL STINT LENGTH (constant per stint)
SOLUTION: Recalculate as LAP-BY-LAP COUNTER (1, 2, 3, ... within each stint)

This is critical for tyre degradation physics to work correctly.
"""
import pandas as pd
import numpy as np
from pathlib import Path

def fix_tyre_life(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalculate TyreLife as lap-by-lap counter within each stint.

    Logic:
    - Group by (Year, EventName, Driver, Stint)
    - Sort by LapNumber within each group
    - TyreLife = 1, 2, 3, 4, ... for each lap in the stint

    Args:
        df: Dataset with broken TyreLife

    Returns:
        Dataset with corrected TyreLife
    """
    print("🔧 Fixing TyreLife column...")
    print()

    # Show before state
    print("BEFORE (sample):")
    sample = df[df['Driver'] == 'VER'].head(20)
    print(sample[['LapNumber', 'Stint', 'TyreLife', 'Compound', 'LapTimeSec']].to_string(index=False))
    print()

    # Make a copy
    df = df.copy()

    # Sort by race progression
    df = df.sort_values(['Year', 'EventName', 'Driver', 'LapNumber'])

    # Method 1: Use cumcount within each stint
    # This creates 0, 1, 2, 3... so we add 1
    df['TyreLife_Fixed'] = (
        df.groupby(['Year', 'EventName', 'Driver', 'Stint'])
        .cumcount() + 1
    )

    # Replace old TyreLife
    df['TyreLife_Original'] = df['TyreLife']
    df['TyreLife'] = df['TyreLife_Fixed']

    # Show after state
    print("AFTER (same sample):")
    sample_after = df[df['Driver'] == 'VER'].head(20)
    print(sample_after[['LapNumber', 'Stint', 'TyreLife', 'Compound', 'LapTimeSec']].to_string(index=False))
    print()

    # Validate the fix
    print("VALIDATION:")
    print("-"*80)

    # Check 1: TyreLife starts at 1 for each stint
    first_laps = df.groupby(['Year', 'EventName', 'Driver', 'Stint']).first()
    if (first_laps['TyreLife'] == 1).all():
        print("✅ All stints start with TyreLife=1")
    else:
        print("❌ Some stints don't start at 1")
        print(first_laps[first_laps['TyreLife'] != 1]['TyreLife'].head())

    # Check 2: TyreLife increments by 1 each lap
    df['TyreLife_Diff'] = df.groupby(['Year', 'EventName', 'Driver', 'Stint'])['TyreLife'].diff()
    # First lap in each stint will be NaN, others should be 1
    valid_diffs = df['TyreLife_Diff'].dropna()
    if (valid_diffs == 1).all():
        print("✅ TyreLife increments by 1 each lap")
    else:
        print("⚠️  Some laps have unexpected TyreLife jumps")
        print(df[df['TyreLife_Diff'] != 1][['Driver', 'LapNumber', 'Stint', 'TyreLife', 'TyreLife_Diff']].head(10))

    # Check 3: New correlation
    corr = df[['TyreLife', 'LapTimeSec']].corr().loc['TyreLife', 'LapTimeSec']
    print(f"\nNew TyreLife vs LapTimeSec correlation: {corr:.4f}")
    if corr > 0:
        print(f"✅ POSITIVE correlation ({corr:.4f}) - worn tyres ARE slower (correct!)")
    else:
        print(f"❌ Still NEGATIVE ({corr:.4f}) - something else is wrong")

    # Check 4: Lap times by tyre age
    print("\nLap times by tyre age (after fix):")
    bins = [0, 5, 10, 20, 30, 50]
    labels = ['0-5 laps', '6-10 laps', '11-20 laps', '21-30 laps', '30+ laps']
    df['TyreAge_Bin'] = pd.cut(df['TyreLife'], bins=bins, labels=labels)
    tyre_stats = df.groupby('TyreAge_Bin', observed=True)['LapTimeSec'].agg(['mean', 'count'])
    print(tyre_stats)

    # Drop temporary columns
    df = df.drop(columns=['TyreLife_Diff', 'TyreAge_Bin', 'TyreLife_Fixed'])

    print()
    print("="*80)
    print("✅ TyreLife FIX COMPLETE")
    print("="*80)

    return df


def main():
    """Main execution."""
    print("="*80)
    print("🏎️  F1 DATASET - TYRELIFE CORRECTION SCRIPT")
    print("="*80)
    print()

    # Paths
    input_path = Path('data/processed/F1_Strategy_Prediction_Dataset.csv')
    backup_path = Path('data/processed/F1_Strategy_Prediction_Dataset_BACKUP_BROKEN.csv')
    output_path = Path('data/processed/F1_Strategy_Prediction_Dataset.csv')

    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        print("\nTrying raw data path...")
        input_path = Path('data/raw/f1_strategy_final_dataset.csv')
        if not input_path.exists():
            print(f"❌ Raw file also not found: {input_path}")
            return

    print(f"📂 Loading: {input_path}")
    df = pd.read_csv(input_path)
    print(f"   Shape: {df.shape}")
    print()

    # Create backup
    print(f"💾 Creating backup: {backup_path}")
    df.to_csv(backup_path, index=False)
    print(f"   Backup saved!")
    print()

    # Fix TyreLife
    df_fixed = fix_tyre_life(df)

    # Save corrected dataset
    print()
    print(f"💾 Saving corrected dataset: {output_path}")
    df_fixed.to_csv(output_path, index=False)
    print(f"   Saved! ({df_fixed.shape[0]} rows, {df_fixed.shape[1]} columns)")
    print()

    # Summary statistics
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Original file backed up to: {backup_path}")
    print(f"Corrected file saved to: {output_path}")
    print()
    print("NEXT STEPS:")
    print("  1. Verify the correlation is now POSITIVE")
    print("  2. Retrain all models with corrected data:")
    print()
    print("     python scripts/train_pipeline.py")
    print()
    print("  3. Re-run validation tests:")
    print()
    print("     python /tmp/f1_validation_report.py")
    print()
    print("="*80)


if __name__ == "__main__":
    main()
