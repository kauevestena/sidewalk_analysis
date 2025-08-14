import os
import osmnx as ox
import pandas as pd

# from cities_experiment.functions import read_json, dump_json, calc_len_sum, generate_boxplot, generate_wordcloud

import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from functions import (
    read_json,
    dump_json,
    calc_len_sum,
    generate_boxplot,
    generate_wordcloud,
)


def main():
    ox.settings.timeout = 3600
    csvpath = "cities_experiment/biggest_cities.csv"
    outpath = "cities_experiment/data.json"
    outfiles_folderpath = "cities_experiment/geojsons"
    output_folder = "cities_experiment"

    if not os.path.exists(outfiles_folderpath):
        os.makedirs(outfiles_folderpath)

    cities_df = pd.read_csv(csvpath)

    if not os.path.exists(outpath):
        data = {}
    else:
        data = read_json(outpath)

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

    for i, cityname in enumerate(cities_df["Name"]):
        try:
            sums = {}
            if i > 1000: 
                break
            if not cityname in data:
                data[cityname] = {}
            for category in filters:
                print(i, cityname, category)
                if not category in data[cityname]:
                    print(i, cityname, category)
                    print()
                    outpath_file = os.path.join(
                        outfiles_folderpath, f"{cityname}_{category}.geojson"
                    )
                    current_gdf = ox.features_from_place(cityname, filters[category])
                    sum = calc_len_sum(current_gdf)
                    data[cityname][category] = sum
                    sums[category] = sum
                    dump_json(data, outpath)
            print(f"Processed {cityname}: {sums}")
            # current_gdf.to_file(outpath_file, driver='GeoJSON') # Disabling to avoid large files
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
