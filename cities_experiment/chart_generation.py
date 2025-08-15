#!/usr/bin/env python3
"""
OSM Walk vs Car — Static PNG chart generator (Plotly + Kaleido)

Usage:
  python make_osm_walk_vs_car_charts.py --csv city_network_lengths.csv

If the file isn't found, the script writes a small sample CSV (from your message)
and uses that, so everything runs out-of-the-box.

Outputs (PNG files) will land in ./charts/
Requires: pandas, numpy, plotly, kaleido
"""

import argparse
import os
import math
import textwrap
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio


# ---------- Helpers ----------
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path


def save_fig(
    fig, path_png: str, scale: float = 2.0, width: int = 1200, height: int = 700
):
    """
    Save a plotly figure to PNG using Kaleido.
    If Kaleido isn't installed, instruct the user how to install it.
    """
    try:
        fig.write_image(
            path_png, scale=scale, width=width, height=height, engine="kaleido"
        )
        print(f"✔ saved: {path_png}")
    except Exception as e:
        print(f"✖ failed to save {path_png}: {e}")
        print("Hint: make sure 'kaleido' is installed:  pip install -U kaleido")
        # Plotly static export docs: https://plotly.com/python/static-image-export/
        # px.ecdf docs: https://plotly.com/python-api-reference/generated/plotly.express.ecdf.html
        # px.scatter_geo docs: https://plotly.com/python-api-reference/generated/plotly.express.scatter_geo.html
        # px.treemap docs: https://plotly.com/python-api-reference/generated/plotly.express.treemap.html
        # px.imshow docs: https://plotly.com/python-api-reference/generated/plotly.express.imshow.html


def safe_div(a, b):
    a = np.asarray(a, dtype="float64")
    b = np.asarray(b, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b > 0, a / b, np.nan)


# ---------- Sample CSV (used only if the given CSV is missing) ----------
SAMPLE_CSV = """\
rank,city,country_code,lat,lon,population,radius_m,car_len_m,footway_len_m,sidewalk_len_m,with_sidewalk_len_m
1,Shanghai,CN,31.22222,121.45806,24874500,30000,14302915.66,1666039.33,457725.97,114337.39
2,Beijing,CN,39.9075,116.39723,18960744,30000,16876608.85,3716029.22,480143.97,218140.31
3,Shenzhen,CN,22.54554,114.0683,17494398,30000,10287625.48,8128926.17,2252774.96,1448489.06
4,Guangzhou,CN,23.11667,113.25,16096724,30000,15542594.85,2137960.77,551344.77,250632.66
5,Kinshasa,CD,-4.32758,15.31357,16000000,30000,12749027.51,424968.72,17143.48,29982.48
6,Istanbul,TR,41.01384,28.94966,15701602,30000,16931323.82,2008953.1,266245.3,419837.83
"""


def load_data(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        # Write sample so the script always runs
        sample_path = "sample_city_network_lengths.csv"
        with open(sample_path, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(SAMPLE_CSV))
        print(f"'{csv_path}' not found; using sample data -> {sample_path}")
        csv_path = sample_path
    df = pd.read_csv(csv_path)
    expected = [
        "rank",
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
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    # dtypes
    for c in expected:
        if c not in ["city", "country_code"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["city"] = df["city"].astype(str)
    df["country_code"] = df["country_code"].astype(str)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    # meters -> km
    df["car_len_km"] = df["car_len_m"] / 1000.0
    df["footway_len_km"] = df["footway_len_m"] / 1000.0
    df["sidewalk_len_km"] = df["sidewalk_len_m"] / 1000.0
    df["with_sidewalk_len_km"] = df["with_sidewalk_len_m"] / 1000.0

    # AOI area from circle radius (km²). If you switch to polygons later, replace this with polygon area.
    df["aoi_area_km2"] = math.pi * (df["radius_m"] / 1000.0) ** 2

    # densities (km per km²)
    df["car_density_km_per_km2"] = safe_div(df["car_len_km"], df["aoi_area_km2"])
    df["foot_density_km_per_km2"] = safe_div(df["footway_len_km"], df["aoi_area_km2"])
    df["sidewalk_density_km_per_km2"] = safe_div(
        df["sidewalk_len_km"], df["aoi_area_km2"]
    )
    df["with_sidewalk_density_km_per_km2"] = safe_div(
        df["with_sidewalk_len_km"], df["aoi_area_km2"]
    )

    # per-capita
    df["pop_k"] = df["population"] / 1000.0
    df["car_km_per_1k"] = safe_div(df["car_len_km"], df["pop_k"])
    df["foot_km_per_1k"] = safe_div(df["footway_len_km"], df["pop_k"])

    # ratios / shares
    df["foot_to_car_ratio"] = safe_div(df["footway_len_km"], df["car_len_km"])
    df["sidewalk_share_of_foot"] = safe_div(df["sidewalk_len_km"], df["footway_len_km"])
    df["roads_with_sidewalk_share"] = safe_div(
        df["with_sidewalk_len_km"], df["car_len_km"]
    )
    return df


# ---------- Chart builders ----------
def charts(df: pd.DataFrame, outdir: str):
    ensure_dir(outdir)

    # Long-form for length distributions
    long = df.melt(
        id_vars=["city", "country_code"],
        value_vars=[
            "car_len_km",
            "footway_len_km",
            "with_sidewalk_len_km",
            "sidewalk_len_km",
        ],
        var_name="metric",
        value_name="km",
    )

    # 01 Boxplot (basics)
    fig_box = px.box(
        long,
        x="metric",
        y="km",
        points="all",
        hover_data=["city", "country_code"],
        title="Distribution of network lengths (km)",
    )
    fig_box.update_layout(xaxis_title="", yaxis_title="km")
    save_fig(fig_box, os.path.join(outdir, "01_box_lengths.png"))

    # 02 Violin
    fig_violin = px.violin(
        long,
        x="metric",
        y="km",
        box=True,
        points="all",
        hover_data=["city", "country_code"],
        title="Violin plot of network lengths (km)",
    )
    fig_violin.update_layout(xaxis_title="", yaxis_title="km")
    save_fig(fig_violin, os.path.join(outdir, "02_violin_lengths.png"))

    # 03 Histogram of ratio with marginal box
    fig_hist = px.histogram(
        df,
        x="foot_to_car_ratio",
        nbins=30,
        marginal="box",
        hover_data=["city", "country_code"],
        title="Histogram of foot/car ratio (with marginal boxplot)",
    )
    fig_hist.update_layout(xaxis_title="Footway km / Car km", yaxis_title="Count")
    save_fig(fig_hist, os.path.join(outdir, "03_hist_ratio.png"))

    # 04 ECDF of ratio (fallback to cumulative histogram if px.ecdf not present)
    try:
        fig_ecdf = px.ecdf(
            df, x="foot_to_car_ratio", markers=True, title="ECDF of foot/car ratio"
        )
        fig_ecdf.update_layout(xaxis_title="Footway/Car ratio", yaxis_title="ECDF")
    except Exception:
        fig_ecdf = px.histogram(
            df,
            x="foot_to_car_ratio",
            cumulative=True,
            nbins=100,
            title="Cumulative histogram (ECDF fallback): foot/car ratio",
        )
        fig_ecdf.update_layout(
            xaxis_title="Footway/Car ratio", yaxis_title="Cumulative count"
        )
    save_fig(fig_ecdf, os.path.join(outdir, "04_ecdf_ratio.png"))

    # 05 Population vs Car length (log-x)
    fig_sc_car = px.scatter(
        df,
        x="population",
        y="car_len_km",
        color="country_code",
        hover_name="city",
        size="car_len_km",
        log_x=True,
        labels={"population": "Population", "car_len_km": "Car length (km)"},
        title="Population vs Car length (log-x)",
    )
    save_fig(fig_sc_car, os.path.join(outdir, "05_scatter_population_car.png"))

    # 06 Population vs Footway length (log-x)
    fig_sc_foot = px.scatter(
        df,
        x="population",
        y="footway_len_km",
        color="country_code",
        hover_name="city",
        size="footway_len_km",
        log_x=True,
        labels={"population": "Population", "footway_len_km": "Footway length (km)"},
        title="Population vs Footway length (log-x)",
    )
    save_fig(fig_sc_foot, os.path.join(outdir, "06_scatter_population_foot.png"))

    # 07 2D density: population vs footway density
    fig_dens = px.density_heatmap(
        df,
        x="population",
        y="foot_density_km_per_km2",
        nbinsx=30,
        nbinsy=30,
        labels={"foot_density_km_per_km2": "Footway density (km/km²)"},
        title="Population vs Footway density — 2D density heatmap",
    )
    save_fig(fig_dens, os.path.join(outdir, "07_density_pop_footdens.png"))

    # 08 Map (token-free): scatter_geo
    fig_map = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        hover_name="city",
        hover_data=[
            "country_code",
            "population",
            "car_len_km",
            "footway_len_km",
            "foot_to_car_ratio",
        ],
        color="foot_to_car_ratio",
        size="car_len_km",
        projection="natural earth",
        title="Cities — size: car km, color: foot/car ratio",
    )
    save_fig(fig_map, os.path.join(outdir, "08_map_geo.png"))

    # 09 Scatter-matrix (SPLOM)
    dims = [
        "car_density_km_per_km2",
        "foot_density_km_per_km2",
        "foot_to_car_ratio",
        "roads_with_sidewalk_share",
        "sidewalk_share_of_foot",
        "car_km_per_1k",
        "foot_km_per_1k",
    ]
    # Only keep columns present & finite for SPLOM
    dims = [d for d in dims if d in df.columns]
    fig_splom = px.scatter_matrix(
        df,
        dimensions=dims,
        color="country_code",
        hover_name="city",
        title="Scatter-matrix of densities & ratios",
    )
    fig_splom.update_layout(width=1200, height=900)
    save_fig(fig_splom, os.path.join(outdir, "09_scatter_matrix.png"))

    # 10 Parallel coordinates (normalized 0–1)
    pc_cols = [
        "car_density_km_per_km2",
        "foot_density_km_per_km2",
        "car_km_per_1k",
        "foot_km_per_1k",
        "foot_to_car_ratio",
        "roads_with_sidewalk_share",
        "sidewalk_share_of_foot",
    ]
    pc = df[pc_cols].copy()
    for c in pc_cols:
        col = pc[c].values.astype(float)
        mn, mx = np.nanmin(col), np.nanmax(col)
        if np.isfinite(mn) and np.isfinite(mx) and mx > mn:
            pc[c] = (col - mn) / (mx - mn)
        else:
            pc[c] = 0.5
    pc["ratio_color"] = df["foot_to_car_ratio"]
    fig_par = px.parallel_coordinates(
        pc,
        color="ratio_color",
        title="Parallel coordinates (normalized 0–1; color=foot/car ratio)",
    )
    save_fig(fig_par, os.path.join(outdir, "10_parallel_coords.png"))

    # 11 Top-N bar by foot/car ratio
    topn = min(20, len(df))
    top_ratio = df.sort_values("foot_to_car_ratio", ascending=False).head(topn)
    fig_top = px.bar(
        top_ratio,
        x="city",
        y="foot_to_car_ratio",
        color="country_code",
        hover_data=["population", "car_len_km", "footway_len_km"],
        title=f"Top {topn} cities by foot/car ratio",
    )
    fig_top.update_layout(xaxis={"categoryorder": "total descending"})
    save_fig(fig_top, os.path.join(outdir, "11_top_ratio_bar.png"))

    # 12 Treemap (Country → City), size=footway_km, color=ratio
    fig_tree = px.treemap(
        df,
        path=["country_code", "city"],
        values="footway_len_km",
        color="foot_to_car_ratio",
        hover_data={
            "footway_len_km": ":.2f",
            "car_len_km": ":.2f",
            "foot_to_car_ratio": ":.2f",
        },
        title="Footway composition by Country → City (size = footway km, color = foot/car ratio)",
    )
    save_fig(fig_tree, os.path.join(outdir, "12_treemap.png"))

    # 13 Correlation heatmap
    corr_cols = [
        "car_len_km",
        "footway_len_km",
        "sidewalk_len_km",
        "with_sidewalk_len_km",
        "car_density_km_per_km2",
        "foot_density_km_per_km2",
        "car_km_per_1k",
        "foot_km_per_1k",
        "foot_to_car_ratio",
        "roads_with_sidewalk_share",
        "sidewalk_share_of_foot",
    ]
    corr = df[corr_cols].corr(numeric_only=True)
    fig_corr = px.imshow(
        corr, aspect="auto", title="Correlation heatmap (selected metrics)"
    )
    save_fig(fig_corr, os.path.join(outdir, "13_corr_heatmap.png"))


def main():
    ap = argparse.ArgumentParser(
        description="Make static PNG charts for OSM walk vs car metrics."
    )
    ap.add_argument("--csv", default="city_network_lengths.csv", help="Input CSV path.")
    ap.add_argument(
        "--outdir", default="charts", help="Output directory for PNG files."
    )
    args = ap.parse_args()

    df = load_data(args.csv)
    df = engineer_features(df)
    charts(df, args.outdir)

    # Print a tiny summary
    print("\nSummary:")
    print("  Cities:", len(df))
    print("  Total car km:     {:,.0f}".format(df["car_len_km"].sum()))
    print("  Total footway km: {:,.0f}".format(df["footway_len_km"].sum()))
    print("  Median foot/car ratio: {:.2f}".format(df["foot_to_car_ratio"].median()))


if __name__ == "__main__":
    main()
