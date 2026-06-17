"""M1: Lap Time Regressor (LightGBM)."""
import numpy as np
from typing import Dict, Any
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import TargetEncoder
from lightgbm import LGBMRegressor

from src.models.base import BaseModelTrainer
from src.data.feature_engineering import FeatureEngineeringM1
from src.utils import evaluate_regression


class M1Trainer(BaseModelTrainer):
    """Lap Time Regressor using LightGBM."""

    def __init__(self, config: Dict[str, Any], mlflow_tracking_uri: str = "file:./mlruns"):
        super().__init__("m1", config, mlflow_tracking_uri)

        # Feature lists from notebook
        self.num_features = [
            "LapNumber", "Stint", "TyreLife", "GridPosition",
            "AirTemp", "TrackTemp", "WindSpeed", "IsSC", "IsDRS",
            "TyreDegRate", "CompoundDeg", "Rolling3LapTime", "Rolling5LapTime",
            "LapTimeDelta", "LapTimeVsField",
            "Sector1TimeSec_Delta", "Sector2TimeSec_Delta", "Sector3TimeSec_Delta",
            "PrevLapTime", "Rainfall", "IsLast", "IsLeader", "GapAhead", "GapBehind",
            "FuelLoad", "TrackAirDelta", "TrackWind",
        ]
        self.cat_features = ["Compound", "Team", "Driver", "EventName"]

    def create_pipeline(self, params: Dict[str, Any]) -> Pipeline:
        """Create M1 pipeline with FE + preprocessing + LightGBM."""
        preprocessing = ColumnTransformer([
            ("num", Pipeline([
                ("imp", SimpleImputer(strategy="median")),
            ]), self.num_features),
            ("cat", Pipeline([
                ("imp", SimpleImputer(strategy="most_frequent")),
                ("enc", TargetEncoder(target_type="continuous", random_state=42, smooth=10.0)),
            ]), self.cat_features),
        ])

        return Pipeline([
            ("fe", FeatureEngineeringM1()),
            ("pre", preprocessing),
            ("model", LGBMRegressor(**params, random_state=42, n_jobs=-1, verbosity=-1)),
        ])

    def create_objective(self, X_train, y_train, X_valid, y_valid, groups_train=None):
        """Optuna objective for M1."""
        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 300, 2000),
                "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.15, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 15, 255),
                "max_depth": trial.suggest_int("max_depth", 3, 16),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-5, 10, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-5, 10, log=True),
            }

            pipe = self.create_pipeline(params)
            pipe.fit(X_train, y_train)

            from sklearn.metrics import root_mean_squared_error
            y_pred = pipe.predict(X_valid)
            return root_mean_squared_error(y_valid, y_pred)

        return objective

    def evaluate(self, X_test, y_test, dataset_name: str = "Test") -> Dict[str, float]:
        """Evaluate M1 on test set."""
        if self.pipeline is None:
            raise ValueError("Model not trained. Call train() first.")

        print(f"\n{'='*60}")
        print(f"Evaluating {self.config['name']} on {dataset_name}")
        print(f"{'='*60}")

        y_pred = self.pipeline.predict(X_test)
        metrics = evaluate_regression(y_test, y_pred, dataset_name)

        return metrics
