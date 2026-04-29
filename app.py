from fastapi import FastAPI
from pydantic import BaseModel, Field

from weather import download_epw_from_pvgis
from off_app import office_cooling_from_epw


# -------------------------------------------------------
# FastAPI app
# -------------------------------------------------------

app = FastAPI(
    title="Office Cooling API (Trial)",
    version="0.1.0",
)


# -------------------------------------------------------
# Request schema
# -------------------------------------------------------

class CoolingRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

    floor_area: float = Field(
        ...,
        gt=0,
        description="Floor area in square metres"
    )

    glazing_type: str = Field(
        "normal",
        description="normal | solar_control | cdte_pv"
    )

    cooling_setpoint: float = Field(
        24.0,
        ge=18,
        le=30,
        description="Cooling setpoint temperature (°C)"
    )


# -------------------------------------------------------
# Health check
# -------------------------------------------------------

@app.get("/")
def health_check():
    return {"status": "ok"}


# -------------------------------------------------------
# Cooling calculation endpoint
# -------------------------------------------------------

@app.post("/cooling")
def calculate_cooling(req: CoolingRequest):

    # 1. Download EPW dynamically from PVGIS
    epw_path = download_epw_from_pvgis(
        lat=req.lat,
        lon=req.lon,
    )

    # 2. Run cooling model
    annual_kwh, peak_kw, daily_kwh = office_cooling_from_epw(
        epw_path=epw_path,
        lat=req.lat,
        floor_area=req.floor_area,
        glazing_type=req.glazing_type,
        cooling_setpoint=req.cooling_setpoint,
    )

    # 3. Return API-friendly response
    return {
        "annual_cooling_kwh": round(annual_kwh, 1),
        "peak_kw": round(peak_kw, 2),
        "daily_kwh": [
            {
                "date": d.isoformat(),
                "kwh": float(v),
            }
            for d, v in daily_kwh.items()
        ],
    }
