#!/usr/bin/env python3
"""
Compute OSM network length stats for the 1,000 most populous cities.

Data sources:
- Cities: GeoNames 'cities1000' (CC BY) – https://download.geonames.org/export/dump/cities1000.zip
- OSM stats: ohsome API – https://api.ohsome.org/v1 (elements/length grouped by boundary)

What it measures (meters):
- car_len:        highway in {motorway, trunk, primary, tertiary, unclassified, residential}
- footway_len:    highway in {footway, path}
- sidewalk_len:   highway=footway AND footway in {sidewalk, crossing}
- with_sidewalk:  any way with 'sidewalk=*' (length of road centerlines carrying a sidewalk tag)

NOTE: 'with_sidewalk' measures road centerline length where sidewalks are tagged on roads,
not the physical sidewalk length. Interpret accordingly.

Usage:
  python city_lengths_ohsome.py --top-n 1000 --radius-mode sqrtpop --min-km 5 --max-km 30 \
      --out city_network_lengths.csv
"""

import io
import math
import os
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd
import requests

OHsome_BASE = "https://api.ohsome.org/v1"
GEONAMES_URL = "https://download.geonames.org/export/dump/cities1000.zip"

# ---- Your OSMnx-style categories, translated to ohsome filter syntax ----
# See ohsome filter docs: key in (v1, v2) ; type:way ; geometry:line
# https://docs.ohsome.org/ohsome-api/stable/filter.html
FILTERS = {
    "car_len": (
        "type:way and geometry:line and "
        "highway in (motorway, trunk, primary, tertiary, unclassified, residential)"
    ),
    "footway_len": ("type:way and geometry:line and " "highway in (footway, path)"),
    "sidewalk_len": (
        "type:way and geometry:line and "
        "highway=footway and footway in (sidewalk, crossing)"
    ),
    "with_sidewalk": ("type:way and geometry:line and sidewalk=*"),
}


@dataclass
class City:
    rank: int
    name: str
    country_code: str
    lat: float
    lon: float
    population: int
    radius_m: int
    boundary_id: str  # short, URL-safe id for ohsome grouping


def download_geonames_cities() -> pd.DataFrame:
    """Download and parse GeoNames cities1000 into a DataFrame."""
    print("Downloading GeoNames cities1000…")
    r = requests.get(GEONAMES_URL, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        with zf.open("cities1000.txt") as fh:
            cols = [
                "geonameid",
                "name",
                "asciiname",
                "alternatenames",
                "latitude",
                "longitude",
                "feature_class",
                "feature_code",
                "country_code",
                "cc2",
                "admin1_code",
                "admin2_code",
                "admin3_code",
                "admin4_code",
                "population",
                "elevation",
                "dem",
                "timezone",
                "modification_date",
            ]
            df = pd.read_csv(
                fh,
                sep="\t",
                header=None,
                names=cols,
                low_memory=False,
                dtype={
                    "population": "Int64",
                    "latitude": float,
                    "longitude": float,
                    "country_code": str,
                },
            )
    # Keep plausible cities (feature class P is city/village, etc.). cities1000 is already filtered,
    # but we additionally require population > 0 for ranking.
    df = df[df["population"].fillna(0) > 0].copy()
    return df


def radius_from_population(
    pop: int, min_km: float, max_km: float, mode: str = "sqrtpop"
) -> int:
    """
    Compute a circle radius in meters around the city center.
    Default 'sqrtpop': radius_km = clamp(0.01 * sqrt(pop), min_km, max_km)
      - ~5.5 km at 300k, ~10 km at 1M, capped at 30 km for megacities.
    """
    if mode == "fixed":
        # Caller should pass min_km == max_km for a fixed radius.
        r_km = min_km
    else:
        r_km = 0.01 * math.sqrt(pop)
        r_km = max(min_km, min(max_km, r_km))
    return int(round(r_km * 1000))


def top_n_cities(
    df: pd.DataFrame, n: int, min_km: float, max_km: float, radius_mode: str
) -> List[City]:
    df_sorted = (
        df.sort_values("population", ascending=False).head(n).reset_index(drop=True)
    )
    cities: List[City] = []
    for i, row in df_sorted.iterrows():
        pop = int(row["population"])
        radius_m = radius_from_population(
            pop, min_km=min_km, max_km=max_km, mode=radius_mode
        )
        boundary_id = f"r{i+1:04d}"
        cities.append(
            City(
                rank=i + 1,
                name=str(row["name"]),
                country_code=str(row["country_code"]),
                lat=float(row["latitude"]),
                lon=float(row["longitude"]),
                population=pop,
                radius_m=radius_m,
                boundary_id=boundary_id,
            )
        )
    return cities


def build_bcircles(cities: List[City]) -> str:
    """
    Build ohsome bcircles parameter string:
    'id:lon,lat,r|id:lon,lat,r|…'
    """
    parts = [f"{c.boundary_id}:{c.lon:.6f},{c.lat:.6f},{c.radius_m}" for c in cities]
    return "|".join(parts)


def ohsome_length_groupby_boundary(
    filter_str: str, bcircles: str, session: requests.Session, chunk: int = 250
) -> Dict[str, float]:
    """
    Call ohsome /elements/length/groupBy/boundary in chunks of bcircle entries.
    Returns dict {boundary_id: length_m}.
    """
    url = f"{OHsome_BASE}/elements/length/groupBy/boundary"
    ids_to_value: Dict[str, float] = {}

    # Split bcircles into manageable chunks to avoid very large payloads
    entries = bcircles.split("|")
    for i in range(0, len(entries), chunk):
        bc_part = "|".join(entries[i : i + chunk])
        data = {
            "bcircles": bc_part,
            "filter": filter_str,
            "format": "json",
            # time omitted => latest snapshot in OSHDB
        }
        resp = session.post(url, data=data, timeout=300)
        if resp.status_code >= 400:
            raise RuntimeError(f"ohsome error {resp.status_code}: {resp.text[:500]}")

        js = resp.json()
        # groupByResult: [{groupByObject: id, result: [{timestamp:..., value: ...}]}]
        for g in js.get("groupByResult", []):
            gid = g.get("groupByObject")
            res = g.get("result", [])
            if not res:
                continue
            val = res[-1].get("value", 0.0)  # latest (only one when time omitted)
            ids_to_value[gid] = float(val)

    return ids_to_value


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute OSM network length stats for top-N world cities using ohsome."
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=1000,
        help="Number of most populous cities to include.",
    )
    parser.add_argument(
        "--radius-mode",
        type=str,
        choices=["sqrtpop", "fixed"],
        default="sqrtpop",
        help="How to set circle radius per city.",
    )
    parser.add_argument(
        "--min-km",
        type=float,
        default=5.0,
        help="Minimum radius in km (or the fixed radius if --radius-mode=fixed).",
    )
    parser.add_argument(
        "--max-km",
        type=float,
        default=30.0,
        help="Maximum radius in km (ignored if --radius-mode=fixed).",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="cities_experiment/city_network_lengths.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--chunk", type=int, default=250, help="How many city circles per ohsome POST."
    )
    args = parser.parse_args()

    # 1) Cities
    df_cities = download_geonames_cities()
    cities = top_n_cities(
        df_cities,
        n=args.top_n,
        min_km=args.min_km,
        max_km=args.max_km,
        radius_mode=args.radius_mode,
    )
    bcircles = build_bcircles(cities)
    print(f"Prepared {len(cities)} city circles for ohsome queries.")

    # 2) ohsome calls (four metrics)
    session = requests.Session()
    session.headers.update({"User-Agent": "city-lengths-ohsome/1.0"})

    results: Dict[str, Dict[str, float]] = {}
    for key, filt in FILTERS.items():
        print(f"Querying ohsome for '{key}' …")
        vals = ohsome_length_groupby_boundary(
            filt, bcircles, session=session, chunk=args.chunk
        )
        # Ensure we have an entry for each city (0.0 if missing)
        results[key] = {
            c.boundary_id: float(vals.get(c.boundary_id, 0.0)) for c in cities
        }

    # 3) Assemble output table
    rows = []
    for c in cities:
        rows.append(
            {
                "rank": c.rank,
                "city": c.name,
                "country_code": c.country_code,
                "lat": c.lat,
                "lon": c.lon,
                "population": c.population,
                "radius_m": c.radius_m,
                "car_len_m": results["car_len"][c.boundary_id],
                "footway_len_m": results["footway_len"][c.boundary_id],
                "sidewalk_len_m": results["sidewalk_len"][c.boundary_id],
                "with_sidewalk_len_m": results["with_sidewalk"][c.boundary_id],
            }
        )
    out_df = pd.DataFrame(rows)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote {args.out} (rows: {len(out_df)})")


if __name__ == "__main__":
    main()
