"""Batch inference utilities."""
import pandas as pd
from pathlib import Path
from src.inference.predictor import F1StrategyPredictor


def predict_race_batch(csv_path: str, output_path: str, registry_path: str = "data/registry"):
    """
    Run inference on entire race CSV and save predictions.

    Args:
        csv_path: Path to input CSV with race data
        output_path: Path to save predictions
        registry_path: Path to model registry
    """
    print(f"Loading race data from {csv_path}...")
    df = pd.read_csv(csv_path)

    print(f"Loaded {len(df)} laps")

    # Initialize predictor
    predictor = F1StrategyPredictor(registry_path)

    # Run batch predictions
    df_with_preds = predictor.predict_batch(df)

    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_with_preds.to_csv(output_path, index=False)

    print(f"✅ Saved predictions to {output_path}")
    print(f"\nPrediction Summary:")
    print(f"  Average predicted lap time: {df_with_preds['pred_lap_time_sec'].mean():.2f}s")
    print(f"  Average pit probability: {df_with_preds['pred_pit_probability'].mean():.3f}")
    print(f"  Average laps until pit: {df_with_preds['pred_laps_until_pit'].mean():.1f}")

    return df_with_preds
