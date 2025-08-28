import pandas as pd
import json
import math
import numpy as np
import os

def safe_div(a, b):
    a = np.asarray(a, dtype="float64")
    b = np.asarray(b, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b > 0, a / b, np.nan)

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

def csv_to_geojson(csv_path, geojson_path):
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(geojson_path), exist_ok=True)

    df = pd.read_csv(csv_path)
    df = engineer_features(df)

    features = []
    for _, row in df.iterrows():
        # Drop NaN values for cleaner JSON
        properties = row.dropna().to_dict()

        # Ensure basic types for JSON serialization
        for key, value in properties.items():
            if isinstance(value, (np.integer, np.int64)):
                properties[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                properties[key] = float(value)

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["lon"], row["lat"]]
            },
            "properties": properties
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(geojson_path, "w") as f:
        json.dump(geojson, f, indent=2)

if __name__ == "__main__":
    csv_to_geojson(
        "cities_experiment/city_network_lengths.csv",
        "cities_experiment/webmap/cities_data.geojson"
    )
    print("GeoJSON file created successfully.")
