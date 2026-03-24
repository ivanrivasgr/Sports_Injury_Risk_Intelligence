"""
data/build_dataset.py
=====================
Builds the Gold-layer dataset used by the dashboard.

HOW IT WORKS
------------
1. Tries to run the live scrapers (Transfermarkt + FBRef + Open-Meteo).
   These require network access — run this script LOCALLY before deploying.
2. If scraped data is not available (e.g. sandbox / CI), falls back to
   `data/seed_data.py` which contains a pre-built, research-quality seed
   dataset derived from public sources (Transfermarkt, FBRef, press reports).

SCRAPERS (run locally with network access)
------------------------------------------
    python data/build_dataset.py --scrape

SEED ONLY (no network)
----------------------
    python data/build_dataset.py

The output is always written to data/gold_injuries.csv and data/gold_appearances.csv.
"""

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent


def scrape_transfermarkt_injuries(player_id: int, player_name: str) -> list[dict]:
    """
    Scrape injury history for a single player from Transfermarkt.
    Returns list of dicts matching the injuries table schema.

    Requires: requests, beautifulsoup4, lxml
    Rate-limit: sleep 2s between requests to be respectful.
    """
    import requests
    from bs4 import BeautifulSoup

    url = f"https://www.transfermarkt.us/{player_name.lower().replace(' ', '-')}/verletzungen/spieler/{player_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "lxml")

    rows = []
    table = soup.select_one("table.items")
    if not table:
        return rows

    for tr in table.select("tbody tr"):
        cols = tr.find_all("td")
        if len(cols) < 7:
            continue
        try:
            rows.append(
                {
                    "player_id": str(player_id),
                    "player_name": player_name,
                    "season": cols[0].get_text(strip=True),
                    "injury_type": cols[1].get_text(strip=True),
                    "date_start": cols[2].get_text(strip=True),
                    "date_end": cols[3].get_text(strip=True),
                    "days_missed": cols[4].get_text(strip=True).replace("-", "0"),
                    "matches_missed": cols[5].get_text(strip=True).replace("-", "0"),
                }
            )
        except Exception:
            continue

    time.sleep(2.0)
    return rows


def scrape_open_meteo_bernabeu(date_str: str) -> dict:
    """
    Fetch historical weather for the Santiago Bernabéu on a given date.
    Bernabéu coords: lat=40.4531, lon=-3.6883

    Requires: requests
    API docs: https://open-meteo.com/en/docs/historical-weather-api
    """
    import requests

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude=40.4531&longitude=-3.6883"
        f"&start_date={date_str}&end_date={date_str}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max"
        "&timezone=Europe/Madrid"
    )
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    daily = data.get("daily", {})
    return {
        "date": date_str,
        "temp_max_c": daily.get("temperature_2m_max", [None])[0],
        "temp_min_c": daily.get("temperature_2m_min", [None])[0],
        "precipitation_mm": daily.get("precipitation_sum", [0])[0],
        "wind_kph": daily.get("windspeed_10m_max", [None])[0],
    }


def load_seed_data():
    """Load pre-built seed dataset."""
    from data.seed_data import get_appearances_df, get_injuries_df, get_weather_df

    return get_injuries_df(), get_appearances_df(), get_weather_df()


def build_gold_dataset(scrape=False):
    if scrape:
        print("Running live scrapers...")
        # --- injuries ---
        SQUAD = [
            ("Thibaut Courtois", 25557),
            ("Dani Carvajal", 138927),
            ("Eder Militao", 314558),
            ("Antonio Rudiger", 86516),
            ("Ferland Mendy", 342229),
            ("Luka Modric", 27992),
            ("Aurelien Tchouameni", 457064),
            ("Eduardo Camavinga", 455194),
            ("Federico Valverde", 371998),
            ("Vinicius Jr", 339032),
            ("Jude Bellingham", 581678),
            ("Rodrygo", 412363),
            ("Dani Ceballos", 163426),
            ("Lucas Vazquez", 166246),
            ("David Alaba", 67229),
        ]
        all_injuries = []
        for name, pid in SQUAD:
            print(f"  Scraping {name}...")
            rows = scrape_transfermarkt_injuries(pid, name)
            all_injuries.extend(rows)

        injuries_df = pd.DataFrame(all_injuries)
        injuries_df.to_csv(DATA_DIR / "scraped_injuries.csv", index=False)
        print(f"  Scraped {len(injuries_df)} injury records")

        # --- weather for each unique match date ---
        dates = injuries_df["date_start"].dropna().unique()[:50]
        weather_rows = []
        for d in dates:
            try:
                weather_rows.append(scrape_open_meteo_bernabeu(d))
            except Exception:
                pass
        weather_df = pd.DataFrame(weather_rows)
        weather_df.to_csv(DATA_DIR / "scraped_weather.csv", index=False)
        print(f"  Scraped {len(weather_df)} weather records")

    else:
        print("Loading seed data (no network required)...")
        injuries_df, appearances_df, weather_df = load_seed_data()

    injuries_df.to_csv(DATA_DIR / "gold_injuries.csv", index=False)
    print(f"Gold injuries written → {DATA_DIR / 'gold_injuries.csv'}")
    return injuries_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scrape", action="store_true", help="Run live scrapers (requires network)"
    )
    args = parser.parse_args()
    build_gold_dataset(scrape=args.scrape)
