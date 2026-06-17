"""Feature engineering for F1 Strategy Engine."""
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


def enrich_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add rolling/lag, sector-delta, track-position and gap features.

    CRITICAL: All transforms use shift(1) to prevent data leakage.

    Args:
        df: Raw dataset with base features

    Returns:
        Enriched dataset with engineered features
    """
    df = df.copy()
    df = df.sort_values(["Year", "EventName", "Driver", "LapNumber"])

    # Driver-race grouping for rolling/lag features
    dg = df.groupby(["Year", "EventName", "Driver"])

    # Rolling lap time features (shifted by 1 lap)
    df["Rolling3LapTime"] = dg["LapTimeSec"].transform(
        lambda x: x.shift(1).rolling(3, min_periods=1).mean()
    )
    df["Rolling5LapTime"] = dg["LapTimeSec"].transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).mean()
    )
    df["LapTimeDelta"] = dg["LapTimeSec"].shift(1).diff().fillna(0)
    df["PrevLapTime"] = dg["LapTimeSec"].shift(1)

    # Sector time deltas (shifted)
    for s in ["Sector1TimeSec", "Sector2TimeSec", "Sector3TimeSec"]:
        df[f"{s}_Delta"] = dg[s].shift(1).diff().fillna(0)

    print("Rolling / lag features added ✓")

    # Track-position & gap features
    df["PositionGain"] = df["GridPosition"] - df["Position"]

    # Field median lap time (lagged 1 lap)
    field_median = df.groupby(["Year", "EventName", "LapNumber"])["LapTimeSec"].transform("median")
    df["PrevFieldMedian"] = (
        field_median.groupby([df["Year"], df["EventName"], df["Driver"]]).shift(1)
    )
    df["LapTimeVsField"] = df["PrevLapTime"] - df["PrevFieldMedian"]

    # Cumulative race time → on-track gap (lagged 1 lap)
    df = df.sort_values(["Year", "EventName", "Driver", "LapNumber"])
    df["RaceTime"] = df.groupby(["Year", "EventName", "Driver"])["LapTimeSec"].cumsum()

    df = df.sort_values(["Year", "EventName", "LapNumber", "Position"])
    lg = df.groupby(["Year", "EventName", "LapNumber"])
    df["GapAhead"] = df["RaceTime"] - lg["RaceTime"].shift(1)
    df["GapBehind"] = lg["RaceTime"].shift(-1) - df["RaceTime"]

    # Lag gaps by 1 lap to prevent leakage
    for col in ["GapAhead", "GapBehind"]:
        df[col] = df.groupby(["Year", "EventName", "Driver"])[col].shift(1)

    df["GapAhead"] = df["GapAhead"].fillna(999)
    df["GapBehind"] = df["GapBehind"].fillna(999)

    # Leader/last position flags
    last_pos = df.groupby(["Year", "EventName", "LapNumber"])["Position"].transform("max")
    df["IsLeader"] = (df["Position"] == 1).astype(int)
    df["IsLast"] = (df["Position"] == last_pos).astype(int)

    print("Position / gap features added ✓")

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# Model-specific Feature Engineering Transformers
# ═══════════════════════════════════════════════════════════════════════════════


class FeatureEngineeringM1(BaseEstimator, TransformerMixin):
    """
    Feature engineering for M1 (Lap Time Regressor).

    Learns max laps per race during fit to prevent FuelLoad leakage at transform time.
    Adds: FuelLoad, TrackAirDelta, TyreDegRate, TrackWind, CompoundDeg.
    """

    def fit(self, X, y=None):
        self.max_laps_ = X.groupby(["Year", "EventName"])["LapNumber"].max()
        return self

    def transform(self, X):
        X = X.copy()
        X["FuelLoad"] = X.apply(
            lambda r: self.max_laps_.get((r["Year"], r["EventName"]), r["LapNumber"]) - r["LapNumber"],
            axis=1
        )
        X["TrackAirDelta"] = X["TrackTemp"] - X["AirTemp"]
        X["TyreDegRate"] = X["TyreLife"] / (X["LapNumber"] + 1)
        X["TrackWind"] = X["TrackTemp"] * X["WindSpeed"]
        X["CompoundDeg"] = X["TyreLife"] * X["CompoundCode"]
        X["Rainfall"] = X["Rainfall"].astype(int)
        return X


class FeatureEngineeringM2(BaseEstimator, TransformerMixin):
    """
    Feature engineering for M2 (Pit Lap Classifier).

    Tyre-wear, race-progress, and pit-pressure features.
    Includes fillna guard for Compound before dictionary lookup.
    """
    EXPECTED_LIFE = {
        "SOFT": 18,
        "MEDIUM": 28,
        "HARD": 38,
        "INTERMEDIATE": 25,
        "WET": 30
    }

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        X["Compound"] = X["Compound"].fillna("UNKNOWN_COMPOUND")
        race_len = X.groupby(["Year", "EventName"])["LapNumber"].transform("max")

        X["FuelLoad"] = race_len - X["LapNumber"]
        X["TrackAirDelta"] = X["TrackTemp"] - X["AirTemp"]
        X["TyreDegRate"] = X["TyreLife"] / (X["LapNumber"] + 1)
        X["TrackWind"] = X["TrackTemp"] * X["WindSpeed"]
        X["CompoundDeg"] = X["TyreLife"] * X["CompoundCode"]
        X["Rainfall"] = X["Rainfall"].astype(int)
        X["ExpectedTyreLife"] = X["Compound"].map(self.EXPECTED_LIFE).fillna(25)
        X["TyreWearPct"] = X["TyreLife"] / X["ExpectedTyreLife"]
        X["RaceProgress"] = X["LapNumber"] / race_len
        X["CompoundTyreLife"] = X["CompoundCode"] * X["TyreLife"]
        X["FinalStint"] = (X["Stint"] >= 3).astype(int)
        X["PitPressure"] = X["TyreWearPct"] * X["RaceProgress"]
        X["PositionDelta"] = X["Position"] - X["GridPosition"]
        X["TeamCompound"] = X["Team"] + "_" + X["Compound"].astype(str)
        X["LapsRemaining"] = race_len - X["LapNumber"]
        X["WearRemaining"] = X["TyreWearPct"] * X["LapsRemaining"]
        return X


class FeatureEngineeringM3(BaseEstimator, TransformerMixin):
    """
    Feature engineering for M3 (Pit-in-3 Classifier).

    Extended tyre features including expected life and exceeded flags.
    """
    EXPECTED_LIFE = {
        "SOFT": 18,
        "MEDIUM": 28,
        "HARD": 38,
        "INTERMEDIATE": 25,
        "WET": 30
    }

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        race_len = X.groupby(["Year", "EventName"])["LapNumber"].transform("max")

        X["FuelLoad"] = race_len - X["LapNumber"]
        X["TrackAirDelta"] = X["TrackTemp"] - X["AirTemp"]
        X["TyreDegRate"] = X["TyreLife"] / (X["LapNumber"] + 1)
        X["TrackWind"] = X["TrackTemp"] * X["WindSpeed"]
        X["CompoundDeg"] = X["TyreLife"] * X["CompoundCode"]
        X["Rainfall"] = X["Rainfall"].astype(int)
        X["ExpectedTyreLife"] = X["Compound"].map(self.EXPECTED_LIFE).fillna(25)
        X["TyreWearPct"] = X["TyreLife"] / X["ExpectedTyreLife"]
        X["RaceProgress"] = X["LapNumber"] / race_len
        X["CompoundTyreLife"] = X["CompoundCode"] * X["TyreLife"]
        X["FinalStint"] = (X["Stint"] >= 3).astype(int)
        X["PitPressure"] = X["TyreWearPct"] * X["RaceProgress"]
        X["PositionDelta"] = X["Position"] - X["GridPosition"]
        X["TeamCompound"] = X["Team"] + "_" + X["Compound"].astype(str)
        X["LapsToExpectedEnd"] = X["ExpectedTyreLife"] - X["TyreLife"]
        X["TyreExceededLife"] = (X["TyreLife"] >= X["ExpectedTyreLife"]).astype(int)
        return X


class FeatureEngineeringM4(BaseEstimator, TransformerMixin):
    """
    Feature engineering for M4/M5 (Laps-Until-Pit Regressors).

    Extended tyre-wear + race-progress features including tyre-life flags.
    """
    EXPECTED_LIFE = {
        "SOFT": 18,
        "MEDIUM": 28,
        "HARD": 38,
        "INTERMEDIATE": 25,
        "WET": 30
    }

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        race_len = X.groupby(["Year", "EventName"])["LapNumber"].transform("max")

        X["FuelLoad"] = race_len - X["LapNumber"]
        X["TrackAirDelta"] = X["TrackTemp"] - X["AirTemp"]
        X["TyreDegRate"] = X["TyreLife"] / (X["LapNumber"] + 1)
        X["TrackWind"] = X["TrackTemp"] * X["WindSpeed"]
        X["CompoundDeg"] = X["TyreLife"] * X["CompoundCode"]
        X["Rainfall"] = X["Rainfall"].astype(int)
        X["ExpectedTyreLife"] = X["Compound"].map(self.EXPECTED_LIFE).fillna(25)
        X["TyreWearPct"] = X["TyreLife"] / X["ExpectedTyreLife"]
        X["RaceProgress"] = X["LapNumber"] / race_len
        X["CompoundTyreLife"] = X["CompoundCode"] * X["TyreLife"]
        X["FinalStint"] = (X["Stint"] >= 3).astype(int)
        X["PitPressure"] = X["TyreWearPct"] * X["RaceProgress"]
        X["PositionDelta"] = X["Position"] - X["GridPosition"]
        X["TeamCompound"] = X["Team"] + "_" + X["Compound"].astype(str)
        X["LapsToExpectedEnd"] = X["ExpectedTyreLife"] - X["TyreLife"]
        X["TyreExceededLife"] = (X["TyreLife"] >= X["ExpectedTyreLife"]).astype(int)
        return X
