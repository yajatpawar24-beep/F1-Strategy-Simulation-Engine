"""Dependency injection for FastAPI."""
from fastapi import HTTPException
from src.inference.predictor import F1StrategyPredictor
from src.inference.strategic_predictor import StrategicF1Predictor

# Global predictor instances
_predictor: F1StrategyPredictor = None
_strategic_predictor: StrategicF1Predictor = None


def initialize_predictor(registry_path: str = "data/registry"):
    """Initialize the global predictor instances."""
    global _predictor, _strategic_predictor
    _predictor = F1StrategyPredictor(registry_path=registry_path)
    _strategic_predictor = StrategicF1Predictor(registry_path=registry_path)
    return _predictor


def get_predictor() -> F1StrategyPredictor:
    """
    Dependency injection for ML predictor.

    Raises 503 if models not loaded.
    """
    if _predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return _predictor


def get_strategic_predictor() -> StrategicF1Predictor:
    """
    Dependency injection for strategic predictor.

    Raises 503 if predictor not loaded.
    """
    if _strategic_predictor is None:
        raise HTTPException(status_code=503, detail="Strategic predictor not loaded")
    return _strategic_predictor
