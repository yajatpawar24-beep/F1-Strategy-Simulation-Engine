"""
F1 Strategy Engine API - Version 2.0
Enterprise-grade FastAPI application with modular routing architecture.
"""
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.dependencies import initialize_predictor
from api.routers import predictions, models, analytics


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 Starting F1 Strategy Engine API v2.0...")
    print("📦 Loading models...")
    try:
        initialize_predictor(registry_path="data/registry")
        print("✅ All 5 models loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load models: {e}")
        raise

    yield  # Application runs

    # Shutdown
    print("🛑 Shutting down F1 Strategy Engine API")


# Initialize FastAPI app with enhanced configuration
app = FastAPI(
    title="F1 Strategy Engine API",
    description="""
    ## 🏎️ Real-time F1 Race Strategy Predictions

    **Production-ready API** powered by 5 ML models for comprehensive race strategy analysis.

    ### Features:
    - 🔮 Single & batch predictions
    - 📊 Full race simulations
    - 🔬 Tyre compound comparisons
    - 🎯 Optimal pit window analysis
    - 📈 Model performance metrics
    - 🏁 Strategy recommendations

    ### Models:
    1. **M1** - Lap Time Regressor (LightGBM)
    2. **M2** - Pit Lap Classifier (CatBoost)
    3. **M3** - Pit-in-3 Classifier (CatBoost)
    4. **M4** - Long Horizon Regressor (CatBoost)
    5. **M5** - Short Horizon Regressor (CatBoost)

    ### Meta-Feature Pipeline:
    ```
    M2 (PitProb) → M3 (PitProbIn3) → M4/M5
    ```
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Root",
            "description": "Root endpoints and API information"
        },
        {
            "name": "Predictions",
            "description": "Single, batch, and scenario predictions"
        },
        {
            "name": "Models",
            "description": "Model information, health, and performance metrics"
        },
        {
            "name": "Analytics",
            "description": "Race simulations, tyre comparisons, and strategy analysis"
        }
    ]
)


# ═══════════════════════════════════════════════════════════════════════════════
# Middleware
# ═══════════════════════════════════════════════════════════════════════════════

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "path": request.url.path
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Routers
# ═══════════════════════════════════════════════════════════════════════════════

# Include all routers with versioned prefix
API_V1_PREFIX = "/api/v1"

app.include_router(predictions.router, prefix=API_V1_PREFIX)
app.include_router(models.router, prefix=API_V1_PREFIX)
app.include_router(analytics.router, prefix=API_V1_PREFIX)


# ═══════════════════════════════════════════════════════════════════════════════
# Root Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Root"])
async def root():
    """
    API root - Welcome message and quick links.
    """
    return {
        "message": "🏎️ F1 Strategy Engine API v2.0",
        "status": "operational",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "api_version": "v1",
        "endpoints": {
            "predictions": f"{API_V1_PREFIX}/predictions",
            "models": f"{API_V1_PREFIX}/models",
            "analytics": f"{API_V1_PREFIX}/analytics"
        },
        "quick_links": {
            "health_check": f"{API_V1_PREFIX}/models/health",
            "model_info": f"{API_V1_PREFIX}/models/info",
            "single_prediction": f"{API_V1_PREFIX}/predictions/single",
            "race_simulation": f"{API_V1_PREFIX}/analytics/race-simulation"
        },
        "frontend": "/app/index.html"
    }


@app.get("/health", tags=["Root"])
async def health():
    """Quick health check (alias for /api/v1/models/health)."""
    from api.dependencies import get_predictor
    predictor = get_predictor()
    return {"status": "healthy", "models_loaded": 5, "api_version": "2.0.0"}


@app.get("/version", tags=["Root"])
async def version():
    """Get API version and build information."""
    return {
        "api_version": "2.0.0",
        "models_version": "1.0.0",
        "framework": "FastAPI",
        "python_version": sys.version,
        "features": [
            "Single predictions",
            "Batch predictions",
            "Race simulations",
            "Tyre comparisons",
            "Pit window optimization",
            "Strategy recommendations"
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Static Files
# ═══════════════════════════════════════════════════════════════════════════════

# Mount frontend
frontend_path = project_root / "frontend"
if frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    print(f"✅ Frontend mounted at /app")


# ═══════════════════════════════════════════════════════════════════════════════
# Development Server
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_v2:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
