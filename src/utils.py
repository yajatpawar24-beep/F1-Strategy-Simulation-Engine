"""Utility functions for model evaluation and visualization."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
)
from typing import Tuple


def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray, dataset_name: str = "Test") -> dict:
    """
    Evaluate regression model and print metrics.

    Args:
        y_true: True values
        y_pred: Predicted values
        dataset_name: Name of dataset (for printing)

    Returns:
        Dictionary of metrics
    """
    rmse = root_mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    print(f"{dataset_name} RMSE : {rmse:.3f}")
    print(f"{dataset_name} MAE  : {mae:.3f}")
    print(f"{dataset_name} R²   : {r2:.3f}")

    return {"rmse": rmse, "mae": mae, "r2": r2}


def evaluate_classification(y_true: np.ndarray, y_pred_proba: np.ndarray,
                           threshold: float = 0.5, dataset_name: str = "Test") -> dict:
    """
    Evaluate binary classification model and print metrics.

    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities (for positive class)
        threshold: Classification threshold
        dataset_name: Name of dataset (for printing)

    Returns:
        Dictionary of metrics
    """
    y_pred = (y_pred_proba >= threshold).astype(int)

    roc_auc = roc_auc_score(y_true, y_pred_proba)
    pr_auc = average_precision_score(y_true, y_pred_proba)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    print(f"{dataset_name} ROC-AUC   : {roc_auc:.4f}")
    print(f"{dataset_name} PR-AUC    : {pr_auc:.4f}")
    print(f"{dataset_name} Precision : {precision:.4f}")
    print(f"{dataset_name} Recall    : {recall:.4f}")
    print(f"{dataset_name} F1        : {f1:.4f}")

    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


def plot_residuals(y_true: np.ndarray, y_pred: np.ndarray, save_path: str = None):
    """
    Plot residual distribution.

    Args:
        y_true: True values
        y_pred: Predicted values
        save_path: Optional path to save figure
    """
    residuals = y_true - y_pred
    plt.figure(figsize=(8, 5))
    plt.hist(residuals, bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel("Residual")
    plt.ylabel("Count")
    plt.title("Residual Distribution")
    plt.axvline(x=0, color='red', linestyle='--', linewidth=2)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def prediction_plot(y_true: np.ndarray, y_pred: np.ndarray, save_path: str = None):
    """
    Plot predicted vs actual values.

    Args:
        y_true: True values
        y_pred: Predicted values
        save_path: Optional path to save figure
    """
    plt.figure(figsize=(7, 7))
    plt.scatter(y_pred, y_true, alpha=0.3, s=10)
    lo, hi = y_true.min(), y_true.max()
    plt.plot([lo, hi], [lo, hi], "r--", linewidth=2, label="Perfect prediction")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Predicted vs Actual")
    plt.legend()
    plt.grid(alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def compute_error_buckets(y_true: np.ndarray, y_pred: np.ndarray,
                         bins: list, labels: list) -> pd.DataFrame:
    """
    Compute MAE per bucket.

    Args:
        y_true: True values
        y_pred: Predicted values
        bins: Bin edges
        labels: Bucket labels

    Returns:
        DataFrame with MAE per bucket
    """
    results = pd.DataFrame({"actual": y_true, "pred": y_pred})
    results["bucket"] = pd.cut(results["actual"], bins=bins, labels=labels)

    bucket_mae = (
        results.groupby("bucket", observed=False)
        .apply(lambda x: mean_absolute_error(x["actual"], x["pred"]), include_groups=False)
    )

    return bucket_mae
