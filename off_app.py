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
    """
    Robust EPW loader compatible with PVGIS TMY (v5.3)
    """

    # Read EPW data (EnergyPlus standard)
    df = pd.read_csv(path, skiprows=8, header=None)

    df.columns = [
        "Year", "Month", "Day", "Hour", "Minute", "DataSource",
        "DryBulb", "DewPoint", "RelHum", "Pressure",
        "ETR", "ETRN", "IRHoriz",
        "GHI", "DNI", "DHI",
        "GlobIllum", "DirNormIllum", "DifIllum",
        "ZenLum", "WindDir", "WindSpd", "TotalSkyCov",
        "OpaqueSkyCov", "Visibility", "CeilingHeight",
        "PresentWeatherObs", "PresentWeatherCodes",
        "PrecipitableWater", "AerosolOptDepth",
        "SnowDepth", "DaysSinceSnow",
        "Albedo", "LiquidPrecipDepth", "LiquidPrecipRate"
    ][:len(df.columns)]

    # EPW hours are 1–24 and represent END of hour
    df["Hour"] = df["Hour"].clip(1, 24) - 1

    df.index = pd.to_datetime(
        dict(
            year=df["Year"],
            month=df["Month"],
            day=df["Day"],
            hour=df["Hour"],
        ),
        errors="coerce",
        utc=True,
    )

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
    alt = np.asarray(alt)
    alt = np.clip(alt, 0.0, 90.0)
    alt[np.isnan(alt)] = 0.0

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
    # -------------------------------
    # 1. Validate glazing input
    # -------------------------------
    if glazing_type not in GLAZING:
        raise ValueError(f"Invalid glazing_type: {glazing_type}")

    glazing = GLAZING[glazing_type]

    # -------------------------------
    # 2. Derived building parameters
    # -------------------------------
    glass_area = 0.13 * floor_area   # same assumption as before
    n_occ = floor_area / 15

    internal_gains = (
        120 * n_occ +
        8 * floor_area +
        10 * floor_area
    )
    
    # -------------------------------
    # 3. Load EPW + solar geometry
    # -------------------------------
    df = load_epw(epw_path)
    df = solar_geometry(df, lat)
    df = irr_vertical(df)
    
    

    # -------------------------------
    # 4. Hourly cooling calculation
    # -------------------------------
    cool_kw = []

    for _, r in df.iterrows():
        Tout = r["DryBulb"]
        I = r["I_facade"]

        Q_cond = glazing["U"] * glass_area * max(Tout - cooling_setpoint, 0)
        Q_solar = glazing["SHGC"] * glass_area * I
        Q_pv = glazing["pv_eff"] * glass_area * I

        Q_total = internal_gains + Q_cond + Q_solar - Q_pv

        P_cool = max(Q_total / COP_COOL, 0.0)
        cool_kw.append(P_cool)

    # -------------------------------
    # 5. Convert to Pandas Series
    # -------------------------------
    cool_kw = pd.Series(cool_kw, index=df.index)
    

    # -------------------------------
    # 6. Aggregation
    # -------------------------------
    daily_kwh = cool_kw.resample("D").sum() / 1000
    

    annual_kwh = daily_kwh.sum()
    peak_kw = cool_kw.max()

    # -------------------------------
    # 7. Return results
    # -------------------------------
    return annual_kwh, peak_kw, daily_kwh
