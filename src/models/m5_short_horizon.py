"""M5: Short Horizon Laps-Until-Pit Regressor (CatBoost with sample weights)."""
import numpy as np
from typing import Dict, Any
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, TargetEncoder
from catboost import CatBoostRegressor

from src.models.base import BaseModelTrainer
from src.data.feature_engineering import FeatureEngineeringM4  # Reuse M4 FE
from src.utils import evaluate_regression


class M5Trainer(BaseModelTrainer):
    """Short Horizon Laps-Until-Pit Regressor (≤10 laps) with sample weighting."""

    def __init__(self, config: Dict[str, Any], mlflow_tracking_uri: str = "file:./mlruns"):
        super().__init__("m5", config, mlflow_tracking_uri)

        # Same features as M4
        self.num_features = [
            "LapNumber", "Stint", "TyreLife", "CompoundCode", "IsSC", "IsVSC",
            "GridPosition", "FuelLoad", "TyreDegRate", "WindSpeed",
            "RaceProgress", "PitPressure", "ExpectedTyreLife", "TyreWearPct",
            "Rolling3LapTime", "Rolling5LapTime", "LapTimeDelta", "PositionGain",
            "RaceTime", "GapAhead", "GapBehind", "LapsToExpectedEnd", "PitProbIn3",
        ]
        self.cat_features = ["EventName", "Team", "FreshTyre", "FinalStint", "IsLeader", "IsLast"]

    def create_pipeline(self, params: Dict[str, Any]) -> Pipeline:
        """Create M5 pipeline with FE + preprocessing + CatBoost."""
        preprocessing = ColumnTransformer([
            ("num", Pipeline([
                ("imp", SimpleImputer(strategy="median")),
                ("scl", StandardScaler()),
            ]), self.num_features),
            ("cat", Pipeline([
                ("imp", SimpleImputer(strategy="most_frequent")),
                ("enc", TargetEncoder(target_type="continuous", random_state=42, smooth=10.0)),
            ]), self.cat_features),
        ])

        # Add fixed params for CatBoost
        model_params = {
            **params,
            "loss_function": "RMSE",
            "eval_metric": "RMSE",
            "iterations": 2500,
            "random_seed": 42,
            "verbose": 0,
        }

        return Pipeline([
            ("fe", FeatureEngineeringM4()),  # Reuse M4 feature engineering
            ("pre", preprocessing),
            ("model", CatBoostRegressor(**model_params)),
        ])

    def create_objective(self, X_train, y_train, X_valid, y_valid, groups_train=None):
        """Optuna objective for M5."""
        def objective(trial):
            params = {
                "depth": trial.suggest_int("depth", 4, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
                "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 30.0, log=True),
                "random_strength": trial.suggest_float("random_strength", 0.0, 10.0),
                "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 10.0),
                "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 5, 100),
                "grow_policy": trial.suggest_categorical("grow_policy", ["SymmetricTree", "Depthwise"]),
            }

            pipe = self.create_pipeline(params)
            pipe.fit(X_train, y_train)

            from sklearn.metrics import mean_absolute_error
            y_pred = pipe.predict(X_valid)
            return mean_absolute_error(y_valid, y_pred)

        return objective

    def train(self, X_train, y_train, apply_sample_weights: bool = True, **kwargs):
        """
        Train M5 with optional 3× sample weights for critical window (≤3 laps).

        Args:
            X_train: Training features
            y_train: Training target
            apply_sample_weights: Apply 3× weight to laps ≤3
            **kwargs: Additional fit arguments
        """
        if self.best_params is None:
            raise ValueError("Must run optimize_hyperparameters() before train()")

        print(f"\nTraining final {self.config['name']}...")
        self.pipeline = self.create_pipeline(self.best_params)

        if apply_sample_weights:
            # 3× weight for critical pit window (≤3 laps)
            weights = np.where(y_train <= 3, 3.0, 1.0)
            self.pipeline.fit(X_train, y_train, model__sample_weight=weights, **kwargs)
            print(f"✓ Training complete (with 3× weights for ≤3 laps: {(y_train <= 3).sum()} samples)")
        else:
            self.pipeline.fit(X_train, y_train, **kwargs)
            print("✓ Training complete")

        return self

    def evaluate(self, X_test, y_test, dataset_name: str = "Test") -> Dict[str, float]:
        """Evaluate M5 on test set."""
        if self.pipeline is None:
            raise ValueError("Model not trained. Call train() first.")

        print(f"\n{'='*60}")
        print(f"Evaluating {self.config['name']} on {dataset_name}")
        print(f"{'='*60}")

        y_pred = self.pipeline.predict(X_test)
        metrics = evaluate_regression(y_test, y_pred, dataset_name)

        # Additional breakdown by lap bucket
        print("\n── Error by lap bucket ──")
        from src.utils import compute_error_buckets
        bucket_mae = compute_error_buckets(
            y_test.values, y_pred,
            bins=[0, 3, 10],
            labels=["1-3 laps", "4-10 laps"]
        )
        print(bucket_mae)

        return metrics
