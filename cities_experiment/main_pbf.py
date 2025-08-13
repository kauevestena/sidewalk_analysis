import os
import pandas as pd
from pyrosm import OSM

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
    csvpath = "cities_experiment/biggest_cities.csv"
    outpath = "cities_experiment/biggest_cities_23set2022.json"
    outfiles_folderpath = "cities_experiment/geojsons"
    pbf_folderpath = "cities_experiment/pbfs"
    output_folder = "cities_experiment"

    if not os.path.exists(outfiles_folderpath):
        os.makedirs(outfiles_folderpath)
    if not os.path.exists(pbf_folderpath):
        os.makedirs(pbf_folderpath)

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
            if i > 20:  # Limiting to 20 cities for testing purposes
                break
            if not cityname in data:
                data[cityname] = {}
            city_slug = cityname.replace(" ", "_").lower()
            pbf_path = os.path.join(pbf_folderpath, f"{city_slug}.osm.pbf")
            if not os.path.exists(pbf_path):
                print(f"PBF file for {cityname} not found at {pbf_path}. Skipping city.")
                continue
            osm = OSM(pbf_path)
            for category in filters:
                print(i, cityname, category)
                if not category in data[cityname]:
                    print(i, cityname, category)
                    print()
                    outpath_file = os.path.join(
                        outfiles_folderpath, f"{cityname}_{category}.geojson"
                    )
                    current_gdf = osm.get_data_by_custom_criteria(
                        custom_filter=filters[category], filter_type="keep", data_type="lines"
                    )
                    data[cityname][category] = calc_len_sum(current_gdf)
                    dump_json(data, outpath)
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
