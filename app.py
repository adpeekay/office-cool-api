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
    lat: float = Field(
        52.205,
        ge=-90,
        le=90,
        description="Latitude (degrees)"
    )
    lon: float = Field(
        0.1218,
        ge=-180,
        le=180,
        description="Longitude (degrees)"
    )

    floor_area: float
    glazing_type: str = "normal"
    cooling_setpoint: float = 24.0


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
