import csv
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from weather import get_epw
from off_app import office_cooling_from_epw

# ======================================================
# Representative EPW per country
# (climate representative, not political statement)
# ======================================================

COUNTRY_EPW = {
    "GBR": ("Cambridge", 52.205, 0.1218),
    "FRA": ("Paris", 48.8566, 2.3522),
    "DEU": ("Berlin", 52.52, 13.405),
    "ESP": ("Madrid", 40.4168, -3.7038),
    "ITA": ("Rome", 41.9028, 12.4964),
    "IRL": ("Dublin", 53.3498, -6.2603),
    "NLD": ("Amsterdam", 52.3676, 4.9041),
    "USA": ("Chicago", 41.8781, -87.6298),
}

# ======================================================
# Load country energy registry (single source of truth)
# ======================================================

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

GLOBAL_AVG_ELECTRICITY_PRICE_USD = 0.20
GLOBAL_AVG_GRID_INTENSITY = 450.0  # gCO2 / kWh

# ======================================================
# FastAPI app
# ======================================================

app = FastAPI(
    title="Office Cooling API (Country‑Driven)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.polysolar.co.uk"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# Request schema
# ======================================================

class CoolingRequest(BaseModel):
    lat: float = Field(
        52.205,
        ge=-90,
        le=90,
        description="Latitude (degrees). Used only as fallback."
    )
    lon: float = Field(
        0.1218,
        ge=-180,
        le=180,
        description="Longitude (degrees). Used only as fallback."
    )
    iso3: Optional[str] = Field(
        None,
        description="ISO‑3166 alpha‑3 country code (e.g. GBR, FRA). Preferred."
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

# ======================================================
# Health check
# ======================================================

@app.get("/")
def health_check():
    return {"status": "ok"}

# ======================================================
# Cooling calculation endpoint
# ======================================================

@app.post("/cooling")
def calculate_cooling(req: CoolingRequest):
    """
    Country‑driven cooling calculation.

    Rules:
    - If iso3 is provided and recognised, it is authoritative.
    - EPW is selected from COUNTRY_EPW.
    - Cost & carbon come ONLY from countries.txt.
    - EPW metadata is never used for country.
    - All errors return JSON (no fake CORS failures).
    """

    # --------------------------------------------------
    # 1. Select EPW
    # --------------------------------------------------

    if req.iso3 and req.iso3 in COUNTRY_EPW:
        _, epw_lat, epw_lon = COUNTRY_EPW[req.iso3]
    else:
        epw_lat, epw_lon = req.lat, req.lon

    try:
        epw_path = get_epw(epw_lat, epw_lon)
    except Exception as e:
        # IMPORTANT: return JSON so CORS headers are applied
        return JSONResponse(
            status_code=502,
            content={
                "error": "Failed to retrieve weather data",
                "detail": str(e),
                "lat": epw_lat,
                "lon": epw_lon,
            },
        )

    iso3 = req.iso3 if req.iso3 in COUNTRY_DATA else None

    # --------------------------------------------------
    # 2. Resolve country economics (single source)
    # --------------------------------------------------

    country_row = COUNTRY_DATA.get(iso3)

    country_name = (
        country_row["country_name"] if country_row else "Unknown"
    )

    electricity_price = (
        country_row["electricity_price_usd_per_kwh"]
        if country_row and country_row["electricity_price_usd_per_kwh"] is not None
        else GLOBAL_AVG_ELECTRICITY_PRICE_USD
    )

    grid_intensity = (
        country_row["grid_intensity_gco2_per_kwh"]
        if country_row and country_row["grid_intensity_gco2_per_kwh"] is not None
        else GLOBAL_AVG_GRID_INTENSITY
    )

    # --------------------------------------------------
    # 3. Run cooling model (pure physics)
    # --------------------------------------------------

    results = {}

    for glazing in ["normal", "solar_control", "cdte_pv"]:
        annual_kwh, peak_kw, _ = office_cooling_from_epw(
            epw_path=epw_path,
            lat=epw_lat,
            floor_area=req.floor_area,
            glazing_type=glazing,
            cooling_setpoint=req.cooling_setpoint,
        )

        annual_cost_usd = annual_kwh * electricity_price
        annual_carbon_kg = annual_kwh * grid_intensity / 1000

        results[glazing] = {
            "annual_cooling_kwh": round(annual_kwh, 1),
            "annual_cost_usd": round(annual_cost_usd, 2),
            "annual_carbon_kg": round(annual_carbon_kg, 1),
            "peak_cooling_kw": round(peak_kw, 2),
        }

    # --------------------------------------------------
    # 4. Savings vs baseline
    # --------------------------------------------------

    base = results["normal"]

    savings = {
        "solar_control": {
            "energy_percent": round(
                100
                * (base["annual_cooling_kwh"]
                   - results["solar_control"]["annual_cooling_kwh"])
                / base["annual_cooling_kwh"],
                1,
            ),
            "cost_usd": round(
                base["annual_cost_usd"]
                - results["solar_control"]["annual_cost_usd"],
                2,
            ),
            "carbon_kg": round(
                base["annual_carbon_kg"]
                - results["solar_control"]["annual_carbon_kg"],
                1,
            ),
        },
        "cdte_pv": {
            "energy_percent": round(
                100
                * (base["annual_cooling_kwh"]
                   - results["cdte_pv"]["annual_cooling_kwh"])
                / base["annual_cooling_kwh"],
                1,
            ),
            "cost_usd": round(
                base["annual_cost_usd"]
                - results["cdte_pv"]["annual_cost_usd"],
                2,
            ),
            "carbon_kg": round(
                base["annual_carbon_kg"]
                - results["cdte_pv"]["annual_carbon_kg"],
                1,
            ),
        },
    }

    # --------------------------------------------------
    # 5. Response
    # --------------------------------------------------

    return {
        "location": {
            "lat": epw_lat,
            "lon": epw_lon,
            "iso3": iso3 if iso3 else "unknown",
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
