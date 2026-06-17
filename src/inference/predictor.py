"""Unified prediction interface for F1 Strategy Engine."""
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Union


class F1StrategyPredictor:
    """
    Unified predictor for all 5 models with meta-feature chaining.

    Loads all trained models and orchestrates predictions:
    M1 (lap time) + M2 (pit prob) → M3 (pit-in-3) → M4/M5 (laps-until-pit)
    """

    def __init__(self, registry_path: str = "data/registry"):
        """
        Initialize predictor with all models.

        Args:
            registry_path: Path to model registry directory
        """
        self.registry_path = Path(registry_path)

        print("Loading F1 Strategy Engine models...")
        self.m1 = joblib.load(self.registry_path / "m1_pipeline.pkl")
        self.m2 = joblib.load(self.registry_path / "m2_pipeline.pkl")
        self.m3 = joblib.load(self.registry_path / "m3_pipeline.pkl")
        self.m4 = joblib.load(self.registry_path / "m4_pipeline.pkl")
        self.m5 = joblib.load(self.registry_path / "m5_pipeline.pkl")
        print("✓ All 5 models loaded")

    def predict_single_lap(self, race_state: Union[Dict, pd.Series]) -> Dict[str, float]:
        """
        Predict strategy for a single lap state.

        Args:
            race_state: Dictionary or Series with race features:
                Required: LapNumber, Stint, TyreLife, TrackTemp, Position,
                         GridPosition, Compound, Team, Driver, EventName, etc.

        Returns:
            Dictionary with predictions:
            {
                "lap_time_sec": float,          # M1: predicted lap time
                "pit_probability": float,       # M2: probability of pitting this lap
                "will_pit_in_3": float,         # M3: probability of pitting within 3 laps
                "laps_until_pit": float,        # M4: estimated laps until next pit
                "laps_until_pit_short": float   # M5: short-horizon estimate (if ≤10)
            }
        """
        # Convert to DataFrame
        if isinstance(race_state, dict):
            X = pd.DataFrame([race_state])
        elif isinstance(race_state, pd.Series):
            X = race_state.to_frame().T
        else:
            raise ValueError("race_state must be dict or pd.Series")

        # M1: Lap Time Prediction
        lap_time = self.m1.predict(X)[0]

        # M2: Pit Probability
        pit_prob = self.m2.predict_proba(X)[0, 1]

        # M3: Pit-in-3 Probability (uses PitProb meta-feature)
        X_m3 = X.copy()
        X_m3["PitProb"] = pit_prob
        pit_in_3_prob = self.m3.predict_proba(X_m3)[0, 1]

        # M4: Long Horizon Laps-Until-Pit (uses PitProbIn3 meta-feature)
        X_m4 = X.copy()
        X_m4["PitProbIn3"] = pit_in_3_prob
        laps_until_long = self.m4.predict(X_m4)[0]

        # M5: Short Horizon (only if relevant)
        laps_until_short = None
        if race_state.get("LapNumber", 0) >= 10:
            X_m5 = X.copy()
            X_m5["PitProbIn3"] = pit_in_3_prob
            laps_until_short = self.m5.predict(X_m5)[0]

        return {
            "lap_time_sec": float(lap_time),
            "pit_probability": float(pit_prob),
            "will_pit_in_3": float(pit_in_3_prob),
            "laps_until_pit": float(laps_until_long),
            "laps_until_pit_short": float(laps_until_short) if laps_until_short is not None else None
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict strategy for multiple lap states.

        Args:
            df: DataFrame with race features (one row per lap)

        Returns:
            Original DataFrame with added prediction columns
        """
        print(f"Running batch predictions on {len(df)} laps...")

        # M1: Lap Times
        df["pred_lap_time_sec"] = self.m1.predict(df)

        # M2: Pit Probabilities
        df["pred_pit_probability"] = self.m2.predict_proba(df)[:, 1]

        # M3: Pit-in-3 (uses M2 predictions)
        df_m3 = df.copy()
        df_m3["PitProb"] = df["pred_pit_probability"]
        df["pred_will_pit_in_3"] = self.m3.predict_proba(df_m3)[:, 1]

        # M4: Long Horizon (uses M3 predictions)
        df_m4 = df.copy()
        df_m4["PitProbIn3"] = df["pred_will_pit_in_3"]
        df["pred_laps_until_pit"] = self.m4.predict(df_m4)

        # M5: Short Horizon (only for eligible rows)
        df["pred_laps_until_pit_short"] = np.nan
        mask_m5 = df["LapNumber"] >= 10
        if mask_m5.sum() > 0:
            df_m5 = df[mask_m5].copy()
            df_m5["PitProbIn3"] = df.loc[mask_m5, "pred_will_pit_in_3"]
            df.loc[mask_m5, "pred_laps_until_pit_short"] = self.m5.predict(df_m5)

        print("✓ Batch predictions complete")
        return df

    def recommend_strategy(self, race_state: Union[Dict, pd.Series]) -> str:
        """
        Generate human-readable strategy recommendation.

        Args:
            race_state: Current race state

        Returns:
            Strategy recommendation string
        """
        pred = self.predict_single_lap(race_state)

        # Decision logic
        if pred["pit_probability"] > 0.7:
            return "⚠️ HIGH PIT RISK - Consider pitting this lap or next"
        elif pred["will_pit_in_3"] > 0.6:
            return f"⏱️ PIT WINDOW OPENING - Expected in {pred['laps_until_pit']:.1f} laps"
        elif pred["laps_until_pit"] < 5:
            return f"🔧 PREPARE PIT STOP - Within {pred['laps_until_pit']:.1f} laps"
        elif pred["laps_until_pit"] < 10:
            return f"📊 MONITOR TYRES - Pit expected in {pred['laps_until_pit']:.1f} laps"
        else:
            return f"✅ STAY OUT - {pred['laps_until_pit']:.1f} laps of tyre life remaining"
