import requests
import tempfile
from pathlib import Path


def download_epw_from_pvgis(lat: float, lon: float):
    """
    Download an EnergyPlus EPW file from PVGIS (TMY, ERA5-based)
    """

    url = (
        "https://re.jrc.ec.europa.eu/api/v5_3/tmy?"
        f"lat={lat}&lon={lon}"
        "&outputformat=epw"
        "&usehorizon=1"
    )

    response = requests.get(url, timeout=90)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".epw")
    tmp.write(response.content)
    tmp.close()

    return Path(tmp.name)

