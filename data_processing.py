import pandas as pd
import numpy as np
import json
import math

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

    # AOI area from circle radius (km²).
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

def df_to_geojson(df):
    features = []
    for _, row in df.iterrows():
        # Convert row to dictionary and remove NaN values
        properties = row.to_dict()
        properties = {k: v for k, v in properties.items() if pd.notna(v)}

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
    return geojson

def main():
    df = pd.read_csv("cities_experiment/city_network_lengths_v2.csv")
    df = engineer_features(df)
    geojson_data = df_to_geojson(df)

    # Custom JSON encoder to handle numpy types
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NpEncoder, self).default(obj)

    print(json.dumps(geojson_data, indent=2, cls=NpEncoder))

if __name__ == "__main__":
    main()
