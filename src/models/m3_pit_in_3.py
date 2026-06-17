"""M3: Pit-in-3 Classifier (CatBoost with OOF)."""
import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, TargetEncoder
from catboost import CatBoostClassifier

from src.models.base import BaseModelTrainer, OOFMixin
from src.data.feature_engineering import FeatureEngineeringM3
from src.utils import evaluate_classification


class M3Trainer(BaseModelTrainer, OOFMixin):
    """Pit-in-3 Classifier using CatBoost with PitProb meta-feature."""

    def __init__(self, config: Dict[str, Any], mlflow_tracking_uri: str = "file:./mlruns"):
        super().__init__("m3", config, mlflow_tracking_uri)

        # Feature lists from notebook (includes PitProb meta-feature)
        self.num_features = [
            "LapNumber", "Stint", "TrackTemp", "TyreLife", "IsSC", "IsVSC",
            "GridPosition", "AirTemp", "WindSpeed", "PitProb",  # ← Meta-feature from M2
            "FuelLoad", "TyreDegRate", "RaceProgress", "PitPressure",
            "ExpectedTyreLife", "TyreWearPct",
            "Rolling3LapTime", "Rolling5LapTime", "LapTimeDelta", "PositionGain",
            "RaceTime", "GapAhead", "GapBehind",
        ]
        self.cat_features = [
            "Compound", "EventName", "Team", "Driver",
            "Rainfall", "FreshTyre", "FinalStint", "IsLeader", "IsLast",
        ]

    def create_pipeline(self, params: Dict[str, Any]) -> Pipeline:
        """Create M3 pipeline with FE + preprocessing + CatBoost."""
        preprocessing = ColumnTransformer([
            ("num", Pipeline([
                ("imp", SimpleImputer(strategy="median")),
                ("scl", StandardScaler()),
            ]), self.num_features),
            ("cat", Pipeline([
                ("imp", SimpleImputer(strategy="most_frequent")),
                ("enc", TargetEncoder(target_type="binary", random_state=42, smooth=10.0)),
            ]), self.cat_features),
        ])

        # Add fixed params for CatBoost
        model_params = {
            **params,
            "border_count": 128,
            "loss_function": "Logloss",
            "auto_class_weights": "Balanced",
            "eval_metric": "PRAUC",
            "random_state": 42,
            "verbose": 0,
        }

        return Pipeline([
            ("fe", FeatureEngineeringM3()),
            ("pre", preprocessing),
            ("model", CatBoostClassifier(**model_params)),
        ])

    def create_objective(self, X_train, y_train, X_valid, y_valid, groups_train=None):
        """Optuna objective for M3."""
        def objective(trial):
            params = {
                "iterations": trial.suggest_int("iterations", 400, 900),
                "depth": trial.suggest_int("depth", 5, 8),
                "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.10, log=True),
                "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 3.0, 10.0),
                "random_strength": trial.suggest_float("random_strength", 0.0, 3.0),
                "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 3.0),
            }

            pipe = self.create_pipeline(params)
            pipe.fit(X_train, y_train)

            from sklearn.metrics import roc_auc_score
            y_pred_proba = pipe.predict_proba(X_valid)[:, 1]
            return roc_auc_score(y_valid, y_pred_proba)

        return objective

    def optimize_hyperparameters(self, X_train, y_train, X_valid, y_valid,
                                 groups_train=None, n_trials: int = 50):
        """Override to maximize ROC-AUC."""
        return super().optimize_hyperparameters(
            X_train, y_train, X_valid, y_valid, groups_train, n_trials, direction="maximize"
        )

    def evaluate(self, X_test, y_test, dataset_name: str = "Test") -> Dict[str, float]:
        """Evaluate M3 on test set."""
        if self.pipeline is None:
            raise ValueError("Model not trained. Call train() first.")

        print(f"\n{'='*60}")
        print(f"Evaluating {self.config['name']} on {dataset_name}")
        print(f"{'='*60}")

        y_pred_proba = self.pipeline.predict_proba(X_test)[:, 1]
        metrics = evaluate_classification(y_test, y_pred_proba, threshold=0.5, dataset_name=dataset_name)

        return metrics
