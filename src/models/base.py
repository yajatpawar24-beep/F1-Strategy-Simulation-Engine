"""Base model trainer with Optuna and MLflow integration."""
import mlflow
import optuna
import joblib
import numpy as np
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupKFold


class BaseModelTrainer(ABC):
    """
    Abstract base class for all F1 strategy models.

    Handles:
    - MLflow experiment tracking
    - Optuna hyperparameter optimization
    - Model persistence with joblib
    - Common training workflows
    """

    def __init__(self, model_name: str, config: Dict[str, Any], mlflow_tracking_uri: str = "file:./mlruns"):
        """
        Initialize trainer.

        Args:
            model_name: Model identifier (m1, m2, etc.)
            config: Model configuration from YAML
            mlflow_tracking_uri: MLflow tracking URI
        """
        self.model_name = model_name
        self.config = config
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.pipeline = None
        self.best_params = None
        self.study = None

    def setup_mlflow(self, experiment_name: str = "F1_Strategy_Engine"):
        """Initialize MLflow experiment."""
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)

    @abstractmethod
    def create_pipeline(self, params: Dict[str, Any]) -> Pipeline:
        """
        Create sklearn pipeline with feature engineering + preprocessing + model.

        Args:
            params: Hyperparameters for the model

        Returns:
            Complete sklearn Pipeline
        """
        pass

    @abstractmethod
    def create_objective(self, X_train, y_train, X_valid, y_valid, groups_train=None):
        """
        Create Optuna objective function.

        Args:
            X_train: Training features
            y_train: Training target
            X_valid: Validation features
            y_valid: Validation target
            groups_train: Optional groups for GroupKFold CV

        Returns:
            Objective function for Optuna
        """
        pass

    def optimize_hyperparameters(
        self,
        X_train,
        y_train,
        X_valid,
        y_valid,
        groups_train=None,
        n_trials: int = 50,
        direction: str = "minimize"
    ) -> Dict[str, Any]:
        """
        Run Optuna hyperparameter search.

        Args:
            X_train: Training features
            y_train: Training target
            X_valid: Validation features
            y_valid: Validation target
            groups_train: Optional groups for CV
            n_trials: Number of Optuna trials
            direction: "minimize" or "maximize"

        Returns:
            Best hyperparameters
        """
        print(f"\n{'='*60}")
        print(f"Optimizing {self.config['name']}")
        print(f"{'='*60}")

        objective = self.create_objective(X_train, y_train, X_valid, y_valid, groups_train)

        optuna.logging.set_verbosity(optuna.logging.WARNING)
        self.study = optuna.create_study(
            direction=direction,
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        self.study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

        self.best_params = self.study.best_params

        print(f"\nBest Value: {self.study.best_value:.4f}")
        print(f"Best Params: {self.best_params}")

        return self.best_params

    def train(self, X_train, y_train, **kwargs) -> 'BaseModelTrainer':
        """
        Train final model with best hyperparameters.

        Args:
            X_train: Training features
            y_train: Training target
            **kwargs: Additional arguments (e.g., sample_weight)

        Returns:
            Self for chaining
        """
        if self.best_params is None:
            raise ValueError("Must run optimize_hyperparameters() before train()")

        print(f"\nTraining final {self.config['name']}...")
        self.pipeline = self.create_pipeline(self.best_params)
        self.pipeline.fit(X_train, y_train, **kwargs)
        print("✓ Training complete")

        return self

    @abstractmethod
    def evaluate(self, X_test, y_test, dataset_name: str = "Test") -> Dict[str, float]:
        """
        Evaluate model on test set.

        Args:
            X_test: Test features
            y_test: Test target
            dataset_name: Name for logging

        Returns:
            Dictionary of metrics
        """
        pass

    def save(self, path: str):
        """
        Save model pipeline to disk.

        Args:
            path: Output path for .pkl file
        """
        if self.pipeline is None:
            raise ValueError("No trained pipeline to save. Call train() first.")

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path, compress=3)
        print(f"✓ Model saved to {path}")

    def load(self, path: str):
        """
        Load model pipeline from disk.

        Args:
            path: Path to .pkl file
        """
        self.pipeline = joblib.load(path)
        print(f"✓ Model loaded from {path}")

    def log_to_mlflow(self, metrics: Dict[str, float], params: Optional[Dict[str, Any]] = None):
        """
        Log metrics and params to MLflow.

        Args:
            metrics: Dictionary of metric names and values
            params: Optional hyperparameters to log
        """
        with mlflow.start_run(run_name=self.config['name']):
            mlflow.set_tag("model", self.model_name)
            mlflow.set_tag("algorithm", self.config['algorithm'])

            if params:
                mlflow.log_params(params)

            mlflow.log_metrics(metrics)

            print(f"✓ Logged to MLflow: {metrics}")


class OOFMixin:
    """Mixin for models that generate out-of-fold predictions (M2, M3)."""

    def generate_oof_predictions(
        self,
        X_train,
        y_train,
        groups_train,
        n_splits: int = 5,
        return_proba: bool = True
    ) -> np.ndarray:
        """
        Generate out-of-fold predictions using GroupKFold.

        Args:
            X_train: Training features
            y_train: Training target
            groups_train: Race-level groups
            n_splits: Number of CV folds
            return_proba: Return probabilities (for classifiers)

        Returns:
            OOF predictions aligned with X_train index
        """
        if self.best_params is None:
            raise ValueError("Must run optimize_hyperparameters() before OOF generation")

        print(f"\nGenerating OOF predictions for {self.config['name']}...")

        gkf = GroupKFold(n_splits=n_splits)
        oof_preds = np.zeros(len(X_train))

        for fold, (tr_idx, val_idx) in enumerate(gkf.split(X_train, y_train, groups_train)):
            X_tr = X_train.iloc[tr_idx]
            y_tr = y_train.iloc[tr_idx]
            X_val = X_train.iloc[val_idx]

            fold_pipeline = self.create_pipeline(self.best_params)
            fold_pipeline.fit(X_tr, y_tr)

            if return_proba:
                oof_preds[val_idx] = fold_pipeline.predict_proba(X_val)[:, 1]
            else:
                oof_preds[val_idx] = fold_pipeline.predict(X_val)

            print(f"  Fold {fold+1}/{n_splits} complete")

        print("✓ OOF predictions generated")
        return oof_preds
