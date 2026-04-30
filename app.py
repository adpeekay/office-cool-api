from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from weather import get_epw
from off_app import office_cooling_from_epw
from electricity_prices import get_electricity_price_gbp

# -------------------------------------------------------
# Simple in-memory cache
# -------------------------------------------------------

RESULTS_CACHE = {}

# -------------------------------------------------------
# FastAPI app
# -------------------------------------------------------

app = FastAPI(
    title="Office Cooling API (Trial)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.polysolar.co.uk"],
    allow_credentials=True,   # OK for this stage
    allow_methods=["*"],
    allow_headers=["*"],
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
    floor_area: float = Field(
        150.0,
        gt=1.0,
        description="Office floor area (m²)"
    )
    cooling_setpoint: float = Field(
        24.0,
        description="Cooling setpoint (°C)"
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
    # ----------------------------
    # Build cache key
    # ----------------------------
    cache_key = (
        round(req.lat, 3),
        round(req.lon, 3),
        round(req.floor_area, 1),
        round(req.cooling_setpoint, 1),
    )

    if cache_key in RESULTS_CACHE:
        return RESULTS_CACHE[cache_key]

    # ----------------------------
    # Get EPW (cached)
    # ----------------------------
    epw_path = get_epw(req.lat, req.lon)

    # ----------------------------
    # Run glazing comparison
    # ----------------------------
    results = {}

    for glazing in ["normal", "solar_control", "cdte_pv"]:
        annual_kwh, peak_kw, _ = office_cooling_from_epw(
            epw_path=epw_path,
            lat=req.lat,
            floor_area=req.floor_area,
            glazing_type=glazing,
            cooling_setpoint=req.cooling_setpoint,
        )

        results[glazing] = {
            "annual_cooling_kwh": round(annual_kwh, 1),
            "peak_cooling_kw": round(peak_kw, 2),
        }

    # ----------------------------
    # Relative savings
    # ----------------------------
    base = results["normal"]["annual_cooling_kwh"]

    savings = {
        "solar_control_vs_normal_percent":
            round(100 * (base - results["solar_control"]["annual_cooling_kwh"]) / base, 1)
            if base > 0 else 0.0,

        "cdte_pv_vs_normal_percent":
            round(100 * (base - results["cdte_pv"]["annual_cooling_kwh"]) / base, 1)
            if base > 0 else 0.0,
    }

    # ---------------------------------------------------
    # Electricity price (GBP/kWh)
    #
    # NOTE:
    # At this stage, we intentionally use a country-level
    # price proxy. Country resolution can later be refined
    # or swapped for EPW metadata if desired.
    # ---------------------------------------------------

    # TEMPORARY / SIMPLE country handling:
    # If you already determine country elsewhere,
    # replace this with that logic.
    # ---------------------------------------------------
# Derive country from EPW
# ---------------------------------------------------

    country = get_country_from_epw(epw_path)

    price_info = get_electricity_price_gbp(country)

    price_info = get_electricity_price_gbp(country)

    # ----------------------------
    # Build response
    # ----------------------------
    response = {
        "location": {
            "lat": req.lat,
            "lon": req.lon,
            "country": country,
        },
        "floor_area": req.floor_area,
        "cooling_setpoint": req.cooling_setpoint,
        "results": results,
        "relative_savings": savings,
        "electricity_price": {
            "value_gbp_per_kwh": price_info["price_gbp_per_kwh"],
            "currency": "GBP",
            "source": price_info["source"],
            "fallback_used": price_info["fallback_used"],
        },
    }

    # ----------------------------
    # Store in cache
    # ----------------------------
    RESULTS_CACHE[cache_key] = response

    return response
