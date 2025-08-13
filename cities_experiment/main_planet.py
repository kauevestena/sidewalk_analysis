import os
import pandas as pd
import osmnx as ox
from pyrosm import OSM

import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from functions import read_json, dump_json, calc_len_sum, generate_boxplot, generate_wordcloud


def main():
    csvpath = "cities_experiment/biggest_cities.csv"
    outpath = "cities_experiment/biggest_cities_planet.json"
    outfiles_folderpath = "cities_experiment/geojsons"
    planet_pbf = "cities_experiment/planet-latest.osm.pbf"
    output_folder = "cities_experiment"

    if not os.path.exists(outfiles_folderpath):
        os.makedirs(outfiles_folderpath)

    cities_df = pd.read_csv(csvpath)

    if not os.path.exists(outpath):
        data = {}
    else:
        data = read_json(outpath)

    if not os.path.exists(planet_pbf):
        raise FileNotFoundError(
            f"Planet file not found at {planet_pbf}. Download from https://planet.openstreetmap.org/"
        )

    filters = {
        "car_len": {
            "highway": [
                "motorway",
                "trunk",
                "primary",
                "tertiary",
                "unclassified",
                "residential",
            ]
        },
        "footway_len": {"highway": ["footway", "path"]},
        "sidewalk_len": {"footway": ["sidewalk", "crossing"]},
        "with_sidewalk": {"sidewalk": True},
    }

    for i, row in cities_df.iterrows():
        cityname = row["Name"]
        if i > 20:  # Limiting to 20 cities for testing purposes
            break
        if cityname not in data:
            data[cityname] = {}
        try:
            geocode_str = f"{cityname}, {row['Country']}"
            city_geom = ox.geocode_to_gdf(geocode_str).unary_union
            bbox = city_geom.bounds
            osm = OSM(planet_pbf, bounding_box=bbox)
            for category in filters:
                if category in data[cityname]:
                    continue
                print(i, cityname, category)
                current_gdf = osm.get_data_by_custom_criteria(
                    custom_filter=filters[category],
                    filter_type="keep",
                    data_type="lines",
                )
                data[cityname][category] = calc_len_sum(current_gdf)
                dump_json(data, outpath)
        except Exception as e:
            print(f"Error processing {cityname}: {e}")
            if cityname in data:
                del data[cityname]

    if os.path.exists(outpath):
        data = read_json(outpath)

    generate_boxplot(data, output_folder)
    generate_wordcloud(data, output_folder)


if __name__ == "__main__":
    main()
