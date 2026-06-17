"""FastAPI application for F1 Strategy Engine."""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.models import RaceStateInput, PredictionOutput, HealthResponse
from src.inference.predictor import F1StrategyPredictor

# Initialize FastAPI app
app = FastAPI(
    title="F1 Strategy Engine API",
    description="Real-time race strategy predictions using 5 ML models",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global predictor instance (loaded once at startup)
predictor: F1StrategyPredictor = None


@app.on_event("startup")
async def load_models():
    """Load all models at startup."""
    global predictor
    print("Loading F1 Strategy Engine models...")
    try:
        predictor = F1StrategyPredictor(registry_path="data/registry")
        print("✓ All models loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        raise


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "F1 Strategy Engine API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "recommend": "/recommend",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    return HealthResponse(
        status="healthy",
        models_loaded=5
    )


@app.post("/predict", response_model=PredictionOutput, tags=["Prediction"])
async def predict_strategy(state: RaceStateInput):
    """
    Predict race strategy for current lap state.

    Returns predictions from all 5 models:
    - M1: Lap time
    - M2: Pit probability (this lap)
    - M3: Pit-in-3 probability (within 3 laps)
    - M4: Long-horizon laps until pit
    - M5: Short-horizon laps until pit (if applicable)
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    try:
        # Convert Pydantic model to dict
        race_state = state.dict()

        # Get predictions
        predictions = predictor.predict_single_lap(race_state)

        return PredictionOutput(**predictions)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/recommend", tags=["Prediction"])
async def recommend_strategy(state: RaceStateInput):
    """
    Get human-readable strategy recommendation.

    Returns a strategic recommendation based on model predictions.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    try:
        race_state = state.dict()
        predictions = predictor.predict_single_lap(race_state)
        recommendation = predictor.recommend_strategy(race_state)

        return {
            "recommendation": recommendation,
            "predictions": predictions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")


# Mount frontend static files (if exists)
frontend_path = project_root / "frontend"
if frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
