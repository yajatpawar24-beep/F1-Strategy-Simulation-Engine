"""Data loading and splitting utilities."""
import pandas as pd
from typing import Dict


def load_raw_data(path: str) -> pd.DataFrame:
    """
    Load raw F1 strategy dataset.

    Args:
        path: Path to CSV file

    Returns:
        Raw DataFrame
    """
    df = pd.read_csv(path)
    print(f"Loaded {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def time_based_split(
    df: pd.DataFrame,
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series,
    train_end: int = 2022,
    valid_year: int = 2023,
    test_year: int = 2024
) -> Dict[str, any]:
    """
    Temporal split with no shuffling.

    If dataset has 'Split' column, uses that. Otherwise falls back to Year-based split.

    Args:
        df: Full dataset with Year column or Split column
        X: Feature matrix
        y: Target vector
        groups: Race-level groups (Year_EventName)
        train_end: Last year included in training (default: 2022)
        valid_year: Validation year (default: 2023)
        test_year: Test year (default: 2024)

    Returns:
        Dictionary with train/valid/test splits
    """
    if 'Split' in df.columns:
        # Use pre-defined split column
        train_mask = df["Split"] == "train"
        valid_mask = df["Split"] == "valid"
        test_mask = df["Split"] == "test"
    else:
        # Fall back to year-based split
        train_mask = df["Year"] <= train_end
        valid_mask = df["Year"] == valid_year
        test_mask = df["Year"] == test_year

    return {
        "X_train": X[train_mask],
        "y_train": y[train_mask],
        "X_valid": X[valid_mask],
        "y_valid": y[valid_mask],
        "X_test": X[test_mask],
        "y_test": y[test_mask],
        "groups_train": groups[train_mask],
        "groups_valid": groups[valid_mask],
        "groups_test": groups[test_mask],
    }


def create_groups(df: pd.DataFrame) -> pd.Series:
    """
    Create race-level groups for GroupKFold.

    Args:
        df: Dataset with Year and EventName columns

    Returns:
        Series of group identifiers (Year_EventName)
    """
    return df["Year"].astype(str) + "_" + df["EventName"]


def dataset_model(dataset: pd.DataFrame, drop_columns: list) -> pd.DataFrame:
    """
    Return a copy of dataset with specified columns removed.

    Args:
        dataset: Full dataset
        drop_columns: List of column names to drop

    Returns:
        Dataset with columns removed
    """
    return dataset.drop(columns=drop_columns, errors='ignore')
