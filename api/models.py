"""Pydantic request/response schemas for FastAPI."""
from pydantic import BaseModel, Field
from typing import Optional


class RaceStateInput(BaseModel):
    """Input schema for single lap prediction."""

    # Lap info
    LapNumber: int = Field(..., ge=1, description="Current lap number")
    Stint: int = Field(..., ge=1, description="Current stint number")
    TyreLife: int = Field(..., ge=0, description="Laps on current tyre set")

    # Position
    Position: int = Field(..., ge=1, le=20, description="Current position")
    GridPosition: int = Field(..., ge=1, le=20, description="Starting grid position")

    # Tyre compound
    Compound: str = Field(..., description="Tyre compound (SOFT, MEDIUM, HARD, etc.)")
    CompoundCode: int = Field(..., description="Compound numeric code")
    FreshTyre: int = Field(..., ge=0, le=1, description="Fresh tyre indicator")

    # Weather & track
    TrackTemp: float = Field(..., description="Track temperature (°C)")
    AirTemp: float = Field(..., description="Air temperature (°C)")
    WindSpeed: float = Field(..., ge=0, description="Wind speed")
    Rainfall: int = Field(..., ge=0, le=1, description="Rainfall indicator")

    # Race control
    IsSC: int = Field(..., ge=0, le=1, description="Safety car flag")
    IsVSC: int = Field(0, ge=0, le=1, description="Virtual safety car flag")
    IsDRS: int = Field(..., ge=0, le=1, description="DRS available")

    # Rolling features (computed from history)
    Rolling3LapTime: Optional[float] = Field(None, description="Rolling 3-lap average")
    Rolling5LapTime: Optional[float] = Field(None, description="Rolling 5-lap average")
    LapTimeDelta: Optional[float] = Field(0.0, description="Lap time delta")
    PrevLapTime: Optional[float] = Field(None, description="Previous lap time")
    LapTimeVsField: Optional[float] = Field(0.0, description="Lap time vs field median")

    # Sector deltas
    Sector1TimeSec_Delta: Optional[float] = Field(0.0, description="Sector 1 delta")
    Sector2TimeSec_Delta: Optional[float] = Field(0.0, description="Sector 2 delta")
    Sector3TimeSec_Delta: Optional[float] = Field(0.0, description="Sector 3 delta")

    # Position dynamics
    PositionGain: Optional[int] = Field(0, description="Positions gained from grid")
    PrevFieldMedian: Optional[float] = Field(None, description="Previous field median lap time")

    # Gaps
    RaceTime: Optional[float] = Field(0.0, description="Cumulative race time")
    GapAhead: Optional[float] = Field(999.0, description="Gap to car ahead (seconds)")
    GapBehind: Optional[float] = Field(999.0, description="Gap to car behind (seconds)")

    # Position flags
    IsLeader: Optional[int] = Field(0, ge=0, le=1, description="Leader flag")
    IsLast: Optional[int] = Field(0, ge=0, le=1, description="Last position flag")

    # Identifiers
    Team: str = Field(..., description="Team name")
    Driver: str = Field(..., description="Driver name")
    EventName: str = Field(..., description="Race/Event name")
    Year: int = Field(..., description="Season year")

    class Config:
        schema_extra = {
            "example": {
                "LapNumber": 20,
                "Stint": 2,
                "TyreLife": 12,
                "Position": 5,
                "GridPosition": 7,
                "Compound": "MEDIUM",
                "CompoundCode": 2,
                "FreshTyre": 0,
                "TrackTemp": 45.0,
                "AirTemp": 28.0,
                "WindSpeed": 2.5,
                "Rainfall": 0,
                "IsSC": 0,
                "IsVSC": 0,
                "IsDRS": 1,
                "Rolling3LapTime": 84.5,
                "Rolling5LapTime": 84.8,
                "LapTimeDelta": -0.3,
                "PrevLapTime": 84.2,
                "Team": "Red Bull Racing",
                "Driver": "Max Verstappen",
                "EventName": "Monaco Grand Prix",
                "Year": 2024
            }
        }


class PredictionOutput(BaseModel):
    """Output schema for predictions."""

    lap_time_sec: float = Field(..., description="Predicted lap time (seconds)")
    pit_probability: float = Field(..., ge=0, le=1, description="Probability of pitting this lap")
    will_pit_in_3: float = Field(..., ge=0, le=1, description="Probability of pitting within 3 laps")
    laps_until_pit: float = Field(..., description="Estimated laps until next pit stop")
    laps_until_pit_short: Optional[float] = Field(None, description="Short-horizon estimate (if applicable)")

    class Config:
        schema_extra = {
            "example": {
                "lap_time_sec": 84.3,
                "pit_probability": 0.12,
                "will_pit_in_3": 0.08,
                "laps_until_pit": 18.5,
                "laps_until_pit_short": None
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    models_loaded: int
