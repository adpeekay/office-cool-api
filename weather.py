import requests
import tempfile
from pathlib import Path


def download_epw_from_pvgis(lat: float, lon: float) -> Path:
    """
    Download an EnergyPlus EPW file from PVGIS (ERA5 reanalysis)
    for a given latitude and longitude.

    Returns
    -------
    Path
        Path to a temporary EPW file on disk.
    """

    url = (
        "https://re.jrc.ec.europa.eu/api/era5?"
        f"lat={lat}&lon={lon}"
        "&outputformat=epw"
    )

    response = requests.get(url, timeout=90)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".epw"
    )
    tmp.write(response.content)
    tmp.close()

    return Path(tmp.name)
