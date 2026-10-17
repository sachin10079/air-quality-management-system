"""Live air-quality data from the free Open-Meteo APIs (no API key needed).

  * Geocoding : https://geocoding-api.open-meteo.com/v1/search
  * Air data  : https://air-quality-api.open-meteo.com/v1/air-quality

Open-Meteo returns hourly pollutant concentrations (µg/m³) and a US AQI.
We also compute the Indian CPCB AQI from those concentrations.
"""
import pandas as pd
import requests

from modules.calculator import compute_aqi

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
TIMEOUT = 20
POLL_KEYS = ["PM2.5", "PM10", "NO2", "SO2", "O3", "CO"]


def search_city(name, count=8):
    """Return a list of matching places for a city name."""
    r = requests.get(
        GEO_URL,
        params={"name": name, "count": count, "language": "en", "format": "json"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return [
        {
            "name": x["name"],
            "admin1": x.get("admin1", ""),
            "country": x.get("country", ""),
            "lat": x["latitude"],
            "lon": x["longitude"],
        }
        for x in r.json().get("results", [])
    ]


def get_air_quality(lat, lon, past_days=10):
    """Fetch current + hourly air-quality data (raw JSON)."""
    hourly = "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi"
    r = requests.get(
        AIR_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": hourly,
            "current": "us_aqi",
            "past_days": past_days,
            "forecast_days": 1,
            "timezone": "auto",
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def build_hourly(raw):
    df = pd.DataFrame(raw["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")
    return df.apply(pd.to_numeric, errors="coerce")


def get_now(raw, df):
    t = raw.get("current", {}).get("time")
    return pd.to_datetime(t) if t else df.index[-1]


def _safe_cpcb(conc):
    try:
        return compute_aqi(conc)["aqi"]
    except ValueError:
        return float("nan")


def live_snapshot(df, now):
    """Latest pollutant levels in CPCB averaging periods (24 h / 8 h)."""
    d = df[df.index <= now]
    last24, last8 = d.tail(24), d.tail(8)
    return {
        "PM2.5": last24["pm2_5"].mean(),
        "PM10": last24["pm10"].mean(),
        "NO2": last24["nitrogen_dioxide"].mean(),
        "SO2": last24["sulphur_dioxide"].mean(),
        "O3": last8["ozone"].mean(),
        "CO": last8["carbon_monoxide"].mean() / 1000.0,  # µg/m³ -> mg/m³
    }


def daily_summary(df, now, days=10):
    """Daily AQI table for the last `days` days (CPCB computed + US from API)."""
    d = df[df.index <= now]
    o3_8h = d["ozone"].rolling(8, min_periods=4).mean()
    co_8h = (d["carbon_monoxide"] / 1000.0).rolling(8, min_periods=4).mean()

    daily = pd.DataFrame({
        "PM2.5": d["pm2_5"].resample("D").mean(),
        "PM10": d["pm10"].resample("D").mean(),
        "NO2": d["nitrogen_dioxide"].resample("D").mean(),
        "SO2": d["sulphur_dioxide"].resample("D").mean(),
        "O3": o3_8h.resample("D").max(),
        "CO": co_8h.resample("D").max(),
        "US AQI": d["us_aqi"].resample("D").mean(),
    })
    daily["CPCB AQI"] = daily[POLL_KEYS].apply(lambda r: _safe_cpcb(r.to_dict()), axis=1)
    return daily.tail(days)
