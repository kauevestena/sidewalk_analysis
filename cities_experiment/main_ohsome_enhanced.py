#!/usr/bin/env python3
"""
Compute OSM network length stats for the N most populous cities using the ohsome API.

- No API key required for the public ohsome API. (See: https://api.ohsome.org )  # docs cited in write-up
- Cities: GeoNames 'cities1000' (CC BY).
- Boundaries: circles (bcircles) OR supplied polygons (bpolys, GeoJSON FeatureCollection with properties.id).
- Metrics (meters):
    car_len:        highway in {motorway, trunk, primary, tertiary, unclassified, residential}
    footway_len:    highway in {footway, path}
    sidewalk_len:   highway=footway AND footway in {sidewalk, crossing}
    with_sidewalk:  any way with 'sidewalk=*'   (length of road centerlines that carry a sidewalk tag)

IMPORTANT:
- 'with_sidewalk' measures centerline length carrying sidewalks, not physical sidewalk length.
- Be courteous to the shared public service: keep chunk sizes modest and threads low.

Usage examples:
  # Circles (radius scales with sqrt(pop), clamped 5–30 km):
  python city_lengths_ohsome_enhanced.py --top-n 1000 --aoi circles --min-km 5 --max-km 30 --threads 4

  # Polygons you provide (GeoJSON FeatureCollection with properties.id, properties.name, etc.):
  python city_lengths_ohsome_enhanced.py --aoi polygons --bpolys-file cities.geojson --top-n 1000 --threads 4
"""

import argparse
import io
import json
import math
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tqdm import tqdm

OHsome_BASE = "https://api.ohsome.org/v1"
GEONAMES_URL = "https://download.geonames.org/export/dump/cities1000.zip"

# --- Your categories translated to ohsome filter syntax (keep these aligned with your OSMnx sets) ---
FILTERS = {
    "car_len": (
        "type:way and geometry:line and "
        "highway in (motorway, trunk, primary, tertiary, unclassified, residential)"
    ),
    "footway_len": ("type:way and geometry:line and highway in (footway, path)"),
    "sidewalk_len": (
        "type:way and geometry:line and highway=footway and footway in (sidewalk, crossing)"
    ),
    "with_sidewalk": ("type:way and geometry:line and sidewalk=*"),
}


@dataclass
class City:
    idx: int  # 1-based rank/order within the selected set
    name: str
    country_code: str
    lat: float
    lon: float
    population: Optional[int]
    boundary_id: str  # used to correlate ohsome results
    radius_m: Optional[int]  # only for circles


def make_session() -> requests.Session:
    s = requests.Session()
    # conservative retry/backoff for transient issues; 413 is not retried (reduce chunk-size instead)
    retry = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "city-lengths-ohsome/2.0 (+research use)"})
    return s


def download_geonames() -> pd.DataFrame:
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
    df = df[df["population"].fillna(0) > 0].copy()
    return df


def radius_from_population(pop: int, min_km: float, max_km: float) -> int:
    # sqrt(pop) scaling, clamped
    r_km = max(min_km, min(max_km, 0.01 * math.sqrt(max(pop, 1))))
    return int(round(r_km * 1000))


def build_cities_from_geonames(n: int, min_km: float, max_km: float) -> List[City]:
    df = download_geonames()
    df = df.sort_values("population", ascending=False).head(n).reset_index(drop=True)
    cities: List[City] = []
    for i, row in df.iterrows():
        pop = int(row["population"]) if not pd.isna(row["population"]) else None
        r_m = radius_from_population(pop or 0, min_km, max_km)
        cities.append(
            City(
                idx=i + 1,
                name=str(row["name"]),
                country_code=str(row["country_code"]),
                lat=float(row["latitude"]),
                lon=float(row["longitude"]),
                population=pop,
                boundary_id=f"r{i+1:04d}",
                radius_m=r_m,
            )
        )
    return cities


def build_bcircles_chunk(cities: List[City]) -> str:
    return "|".join(
        f"{c.boundary_id}:{c.lon:.6f},{c.lat:.6f},{c.radius_m}" for c in cities
    )


def build_bpolys_chunk(features: List[dict]) -> str:
    # features must have properties.id set; ohsome expects a FeatureCollection string in 'bpolys'
    fc = {"type": "FeatureCollection", "features": features}
    return json.dumps(fc, separators=(",", ":"))  # compact to keep payload small


def post_length_groupby_boundary(
    session: requests.Session,
    filter_str: str,
    boundary_kind: str,
    boundary_payload: str,
    time: Optional[str],
    timeout_s: int = 300,
) -> Dict[str, float]:
    """
    Calls POST /elements/length/groupBy/boundary
    Returns {boundary_id: length_m}
    """
    url = f"{OHsome_BASE}/elements/length/groupBy/boundary"
    data = {boundary_kind: boundary_payload, "filter": filter_str, "format": "json"}
    if time:
        data["time"] = time  # e.g., '2025-01-01' or '2019-01-01/2025-01-01/P1Y'
    resp = session.post(url, data=data, timeout=timeout_s)
    if resp.status_code == 413:
        raise RuntimeError(
            "ohsome returned 413 (Payload Too Large). Decrease --chunk-size."
        )
    if resp.status_code >= 400:
        raise RuntimeError(f"ohsome error {resp.status_code}: {resp.text[:500]}")
    js = resp.json()
    out: Dict[str, float] = {}
    for g in js.get("groupByResult", []):
        gid = g.get("groupByObject")
        res = g.get("result", [])
        if not res:
            continue
        # When no 'time' is passed, result has a single item
        out[str(gid)] = float(res[-1].get("value", 0.0))
    return out


def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def main():
    ap = argparse.ArgumentParser(
        description="Compute OSM network length stats for populous cities with ohsome."
    )
    ap.add_argument(
        "--top-n",
        type=int,
        default=1000,
        help="Number of most populous cities (GeoNames) to include.",
    )
    ap.add_argument(
        "--aoi",
        choices=["circles", "polygons"],
        default="polygons",
        help="Use circle boundaries or polygons (GeoJSON).",
    )
    ap.add_argument(
        "--bpolys-file",
        type=str,
        default=None,
        help="GeoJSON FeatureCollection with per-city polygons (requires properties.id).",
    )
    ap.add_argument(
        "--min-km",
        type=float,
        default=5.0,
        help="Min circle radius (km) if --aoi=circles.",
    )
    ap.add_argument(
        "--max-km",
        type=float,
        default=30.0,
        help="Max circle radius (km) if --aoi=circles.",
    )
    ap.add_argument(
        "--time",
        type=str,
        default=None,
        help="ISO time or interval; omit to use latest snapshot in OSHDB.",
    )
    ap.add_argument(
        "--chunk-size", type=int, default=200, help="How many city boundaries per POST."
    )
    ap.add_argument("--threads", type=int, default=4, help="Max concurrent requests.")
    ap.add_argument(
        "--out",
        type=str,
        default="cities_experiment/city_network_lengths_v2.csv",
        help="Output CSV path.",
    )
    args = ap.parse_args()

    session = make_session()

    # Prepare boundaries + city metadata
    if args.aoi == "circles":
        cities = build_cities_from_geonames(args.top_n, args.min_km, args.max_km)
        # Build chunks as bcircle strings
        boundary_kind = "bcircles"
        chunks: List[Tuple[str, List[City]]] = []
        for part in chunked(cities, args.chunk_size):
            chunks.append((build_bcircles_chunk(part), part))
    else:
        if not args.bpolys_file:
            raise SystemExit("--bpolys-file is required when --aoi=polygons")
        with open(args.bpolys_file, "r", encoding="utf-8") as f:
            fc = json.load(f)
        feats = fc.get("features", [])

        # ensure each feature has an id in properties; also pick top-N by 'population' if present
        def feat_pop(feat):
            return feat.get("properties", {}).get("population") or 0

        feats_sorted = sorted(feats, key=feat_pop, reverse=True)[: args.top_n]
        # Build City rows from features; keep any available metadata
        cities = []
        for i, feat in enumerate(feats_sorted):
            props = feat.get("properties", {}) or {}
            bid = props.get("id") or f"poly{i+1:04d}"
            props["id"] = bid  # ensure id exists in outgoing bpolys
            cities.append(
                City(
                    idx=i + 1,
                    name=str(props.get("name") or props.get("NAME") or f"city_{i+1}"),
                    country_code=str(
                        props.get("country_code") or props.get("CC") or ""
                    ),
                    lat=float(props.get("lat") or 0.0),
                    lon=float(props.get("lon") or 0.0),
                    population=(
                        int(props.get("population"))
                        if props.get("population") is not None
                        else None
                    ),
                    boundary_id=bid,
                    radius_m=None,
                )
            )
        # create chunks as small FeatureCollections
        boundary_kind = "bpolys"
        chunks = []
        for part in tqdm(
            chunked(list(zip(feats_sorted, cities)), args.chunk_size),
            desc="Preparing chunks",
            total=(len(feats_sorted) + args.chunk_size - 1) // args.chunk_size,
        ):
            sub_feats = []
            sub_cities = []
            for feat, c in part:
                # guarantee properties.id equals the City.boundary_id we will use for joining
                feat = dict(feat)  # shallow copy
                feat["properties"] = dict(feat.get("properties", {}))
                feat["properties"]["id"] = c.boundary_id
                sub_feats.append(feat)
                sub_cities.append(c)
            chunks.append((build_bpolys_chunk(sub_feats), sub_cities))

    # Prepare results storage
    cols = [
        "idx",
        "city",
        "country_code",
        "lat",
        "lon",
        "population",
        "radius_m",
        "car_len_m",
        "footway_len_m",
        "sidewalk_len_m",
        "with_sidewalk_len_m",
    ]
    out_rows: List[dict] = []

    # Issue requests in parallel per chunk and per metric
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def one_metric(boundary_payload: str, metric_key: str) -> Dict[str, float]:
        filt = FILTERS[metric_key]
        return post_length_groupby_boundary(
            session=session,
            filter_str=filt,
            boundary_kind=boundary_kind,
            boundary_payload=boundary_payload,
            time=args.time,
        )

    # Iterate chunks; for each, fire all 4 metrics concurrently, then assemble rows
    for boundary_payload, part_cities in chunks:
        with ThreadPoolExecutor(max_workers=min(args.threads, 8)) as ex:
            futures = {
                ex.submit(one_metric, boundary_payload, k): k for k in FILTERS.keys()
            }
            metric_maps: Dict[str, Dict[str, float]] = {}
            for fut in as_completed(futures):
                k = futures[fut]
                metric_maps[k] = fut.result()

        # Append output rows for this chunk
        for c in part_cities:
            out_rows.append(
                {
                    "idx": c.idx,
                    "city": c.name,
                    "country_code": c.country_code,
                    "lat": c.lat,
                    "lon": c.lon,
                    "population": c.population,
                    "radius_m": c.radius_m,
                    "car_len_m": metric_maps["car_len"].get(c.boundary_id, 0.0),
                    "footway_len_m": metric_maps["footway_len"].get(c.boundary_id, 0.0),
                    "sidewalk_len_m": metric_maps["sidewalk_len"].get(
                        c.boundary_id, 0.0
                    ),
                    "with_sidewalk_len_m": metric_maps["with_sidewalk"].get(
                        c.boundary_id, 0.0
                    ),
                }
            )

    # Write CSV sorted by idx
    out_df = pd.DataFrame(out_rows).sort_values("idx")
    out_df.to_csv(args.out, index=False)
    print(f"Wrote {args.out} with {len(out_df)} rows")


if __name__ == "__main__":
    main()
