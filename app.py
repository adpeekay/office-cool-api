import csv
from pvlib.iotools import read_epw
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from weather import get_epw, get_country_from_epw
from off_app import office_cooling_from_epw
from electricity_prices import get_electricity_price_gbp

# -------------------------------------------------------
# Load country energy data once at startup
# -------------------------------------------------------

COUNTRY_DATA = {}

with open("countries.txt", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        COUNTRY_DATA[row["iso3"]] = {
            "country_name": row["country_name"],
            "grid_intensity_gco2_per_kwh": (
                float(row["grid_intensity_gco2_per_kwh"])
                if row["grid_intensity_gco2_per_kwh"] else None
            ),
            "electricity_price_usd_per_kwh": (
                float(row["electricity_price_usd_per_kwh"])
                if row["electricity_price_usd_per_kwh"] else None
            ),
        }

# Global fallback values (used if country data missing)
GLOBAL_AVG_ELECTRICITY_PRICE_USD = 0.20
GLOBAL_AVG_GRID_INTENSITY = 450.0  # gCO2 / kWh
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

from fastapi.responses import JSONResponse

@app.post("/cooling")
def calculate_cooling(req: CoolingRequest):
    try:
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
        # Get EPW
        # ----------------------------
        epw_path = get_epw(req.lat, req.lon)
        _, meta = read_epw(epw_path)
        iso3 = meta.get("country")
        # ---------------------------------------------------
        # Resolve country data
        # ---------------------------------------------------

        country = COUNTRY_DATA.get(iso3)

        country_name = (
        country["country_name"]
        if country else "Unknown"
        )

        electricity_price = (
        country["electricity_price_usd_per_kwh"]
        if country and country["electricity_price_usd_per_kwh"] is not None
        else GLOBAL_AVG_ELECTRICITY_PRICE_USD
        )

        grid_intensity = (
        country["grid_intensity_gco2_per_kwh"]
        if country and country["grid_intensity_gco2_per_kwh"] is not None
        else GLOBAL_AVG_GRID_INTENSITY
        )
        # ----------------------------
        # Extract country safely
        # ----------------------------
        country = get_country_from_epw(epw_path)

        # ----------------------------
        # Electricity price (NEVER crashes)
        # ----------------------------
        price_info = get_electricity_price_gbp(country)

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

            annual_cost_usd = annual_kwh * electricity_price
            annual_carbon_kg = annual_kwh * grid_intensity / 1000

            results[glazing] = {
                "annual_cooling_kwh": round(annual_kwh, 1),
                "peak_cooling_kw": round(peak_kw, 2),
            }

        base = results["normal"]["annual_cooling_kwh"]

        savings = {
            "solar_control_vs_normal_percent":
                round(100 * (base - results["solar_control"]["annual_cooling_kwh"]) / base, 1)
                if base > 0 else 0.0,
            "cdte_pv_vs_normal_percent":
                round(100 * (base - results["cdte_pv"]["annual_cooling_kwh"]) / base, 1)
                if base > 0 else 0.0,
        }

        response = {
            "location": {
                "lat": req.lat,
                "lon": req.lon,
                "iso3": iso3,
                "country": country_name,
            },
            "electricity": {
                "price_usd_per_kwh": electricity_price,
            },
            "carbon": {
                "grid_intensity_gco2_per_kwh": grid_intensity,
            },
            "results": results,
            "relative_savings": savings,
        }
        return response

    except Exception as e:
        # ✅ CRITICAL: return JSON instead of crashing
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "type": type(e).__name__,
            },
        )
