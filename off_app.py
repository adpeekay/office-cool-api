import numpy as np
import pandas as pd

# -------------------------------------------------------
# Glazing Definitions (unchanged)
# -------------------------------------------------------

GLAZING = {
    "normal": {"U": 5.5, "SHGC": 0.75, "pv_eff": 0.0},
    "solar_control": {"U": 2.0, "SHGC": 0.35, "pv_eff": 0.0},
    "cdte_pv": {"U": 3.0, "SHGC": 0.12, "pv_eff": 0.08},
}

AIR_CP = 1005
COP_COOL = 3.0
CEILING_HEIGHT = 3.0
ORIENTATION = 180  # south facing


# -------------------------------------------------------
# EPW Loader (unchanged)
# -------------------------------------------------------

def load_epw(path):
    df = pd.read_csv(path, skiprows=8, header=None)
    df.index = pd.date_range(
        "2020-01-01 00:00",
        periods=len(df),
        freq="H"
    )
    df = df.rename(columns={
        6: "DryBulb",
        13: "DHI",
        14: "DNI",
        15: "GHI",
    })
    return df[["DryBulb", "GHI", "DNI", "DHI"]]


# -------------------------------------------------------
# Solar Geometry (lat now passed in)
# -------------------------------------------------------

def solar_geometry(df, lat):
    doy = df.index.dayofyear + df.index.hour / 24

    decl = 23.45 * np.sin(np.deg2rad(360 * (284 + doy) / 365))
    hra = 15 * (df.index.hour - 12)

    alt = np.rad2deg(np.arcsin(
        np.sin(np.deg2rad(lat)) * np.sin(np.deg2rad(decl)) +
        np.cos(np.deg2rad(lat)) * np.cos(np.deg2rad(decl)) * np.cos(np.deg2rad(hra))
    ))
    alt = np.maximum(alt, 0)

    az = np.rad2deg(np.arctan2(
        -np.cos(np.deg2rad(decl)) * np.sin(np.deg2rad(hra)),
        np.cos(np.deg2rad(lat)) * np.sin(np.deg2rad(decl)) -
        np.sin(np.deg2rad(lat)) * np.cos(np.deg2rad(decl)) * np.cos(np.deg2rad(hra))
    ))

    df["altitude"] = alt
    df["azimuth"] = az
    return df


def irr_vertical(df):
    alt = np.deg2rad(df["altitude"])
    azi = np.deg2rad(df["azimuth"])
    ori = np.deg2rad(ORIENTATION)

    cos_theta = np.maximum(
        np.cos(alt) * np.sin(np.pi / 2) * np.cos(azi - ori),
        0
    )

    df["I_facade"] = df["DNI"] * cos_theta + 0.5 * df["DHI"]
    return df


# -------------------------------------------------------
# Main Cooling Function (API-ready)
# -------------------------------------------------------

def office_cooling_from_epw(
    epw_path,
    lat,
    floor_area,
    glazing_type="normal",
    cooling_setpoint=24.0,
):
    glazing = GLAZING[glazing_type]

