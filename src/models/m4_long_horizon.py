"""M4: Long Horizon Laps-Until-Pit Regressor (CatBoost)."""
import numpy as np
from typing import Dict, Any
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, TargetEncoder
from catboost import CatBoostRegressor

from src.models.base import BaseModelTrainer
from src.data.feature_engineering import FeatureEngineeringM4
from src.utils import evaluate_regression


class M4Trainer(BaseModelTrainer):
    """Long Horizon Laps-Until-Pit Regressor using CatBoost."""

    def __init__(self, config: Dict[str, Any], mlflow_tracking_uri: str = "file:./mlruns"):
        super().__init__("m4", config, mlflow_tracking_uri)

        # Feature lists from notebook (includes PitProbIn3 meta-feature)
        self.num_features = [
            "LapNumber", "Stint", "TyreLife", "CompoundCode", "IsSC", "IsVSC",
            "GridPosition", "FuelLoad", "TyreDegRate", "WindSpeed",
            "RaceProgress", "PitPressure", "ExpectedTyreLife", "TyreWearPct",
            "Rolling3LapTime", "Rolling5LapTime", "LapTimeDelta", "PositionGain",
            "RaceTime", "GapAhead", "GapBehind", "LapsToExpectedEnd", "PitProbIn3",  # ← Meta-feature from M3
        ]
        self.cat_features = ["EventName", "Team", "FreshTyre", "FinalStint", "IsLeader", "IsLast"]

    def create_pipeline(self, params: Dict[str, Any]) -> Pipeline:
        """Create M4 pipeline with FE + preprocessing + CatBoost."""
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
            "loss_function": "MAE",
            "eval_metric": "MAE",
            "iterations": 3000,
            "random_seed": 42,
            "verbose": 0,
        }

        return Pipeline([
            ("fe", FeatureEngineeringM4()),
            ("pre", preprocessing),
            ("model", CatBoostRegressor(**model_params)),
        ])

    def create_objective(self, X_train, y_train, X_valid, y_valid, groups_train=None):
        """Optuna objective for M4."""
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

    def train(self, X_train, y_train, use_log_target: bool = True, **kwargs):
        """
        Train M4 with optional log1p target transformation.

        Args:
            X_train: Training features
            y_train: Training target
            use_log_target: Apply log1p transform to target
            **kwargs: Additional fit arguments
        """
        if self.best_params is None:
            raise ValueError("Must run optimize_hyperparameters() before train()")

        print(f"\nTraining final {self.config['name']}...")
        self.pipeline = self.create_pipeline(self.best_params)

        if use_log_target:
            y_train_transformed = np.log1p(y_train)
            self.pipeline.fit(X_train, y_train_transformed, **kwargs)
            self.use_log_target = True
            print("✓ Training complete (with log1p target)")
        else:
            self.pipeline.fit(X_train, y_train, **kwargs)
            self.use_log_target = False
            print("✓ Training complete")

        return self

    def evaluate(self, X_test, y_test, dataset_name: str = "Test") -> Dict[str, float]:
        """Evaluate M4 on test set."""
        if self.pipeline is None:
            raise ValueError("Model not trained. Call train() first.")

        print(f"\n{'='*60}")
        print(f"Evaluating {self.config['name']} on {dataset_name}")
        print(f"{'='*60}")

        y_pred = self.pipeline.predict(X_test)

        # Reverse log1p if used during training
        if hasattr(self, 'use_log_target') and self.use_log_target:
            y_pred = np.expm1(y_pred)

        metrics = evaluate_regression(y_test, y_pred, dataset_name)

        return metrics
