import requests
import tempfile
from pathlib import Path


COUNTRY_NORMALISATION = {
    "GBR": "United Kingdom",
    "UK": "United Kingdom",
    "USA": "United States",
    "US": "United States",
}


EPW_CACHE = {}

def download_epw_from_pvgis(lat: float, lon: float) -> Path:
    """
    Download a PVGIS TMY EPW file for a given location.
    """

    url = (
        "https://re.jrc.ec.europa.eu/api/v5_3/tmy?"
        f"lat={lat}&lon={lon}"
        "&outputformat=epw"
        "&usehorizon=1"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".epw")
    tmp.write(response.content)
    tmp.close()

    return Path(tmp.name)

def get_epw(lat: float, lon: float) -> Path:
    """
    Return a cached EPW file for the given location.
    Falls back to PVGIS download on first request.
    """

    # Round to avoid cache explosion from tiny coordinate changes
    key = (round(lat, 4), round(lon, 4))

    if key not in EPW_CACHE:
        EPW_CACHE[key] = download_epw_from_pvgis(lat, lon)

    return EPW_CACHE[key]



def get_country_from_epw(epw_path) -> str:
    try:
        epw_path = Path(epw_path)
        if not epw_path.exists():
            return "Unknown"

        with epw_path.open("r", encoding="utf-8", errors="ignore") as f:
            line = f.readline()

        parts = line.strip().split(",")
        if len(parts) >= 4:
            raw = parts[3].strip()
            return COUNTRY_NORMALISATION.get(raw, raw.title())

    except Exception as e:
        print("EPW country parse failed:", e)

    return "Unknown"

