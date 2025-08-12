import os
import osmnx as ox
import pandas as pd
from cities_experiment.functions import read_json, dump_json, calc_len_sum, generate_boxplot, generate_wordcloud

def main():
    csvpath = "cities_experiment/biggest_cities.csv"
    output_folder = "cities_experiment/sample_check"
    outpath = os.path.join(output_folder, "biggest_cities_sample.json")
    outfiles_folderpath = os.path.join(output_folder, "geojsons")

    if not os.path.exists(outfiles_folderpath):
        os.makedirs(outfiles_folderpath)

    cities_df = pd.read_csv(csvpath)
    cities_df = cities_df[(cities_df['rank'] >= 996) & (cities_df['rank'] <= 1000)]


    if not os.path.exists(outpath):
        data = {}
    else:
        data = read_json(outpath)

    filters = {
        'car_len': {'highway': ['motorway', 'trunk', 'primary', 'tertiary', 'unclassified', 'residential']},
        'footway_len': {'highway': ['footway', 'path']},
        'sidewalk_len': {'footway': ['sidewalk', 'crossing']},
        'with_sidewalk': {'sidewalk': True}
    }

    for i, cityname in enumerate(cities_df['Name']):
        try:
            if not cityname in data:
                data[cityname] = {}
            for category in filters:
                print(i, cityname, category)
                if not category in data[cityname]:
                    print(i, cityname, category)
                    print()
                    outpath_file = os.path.join(outfiles_folderpath, f"{cityname}_{category}.geojson")
                    current_gdf = ox.features_from_place(cityname, filters[category])
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

if __name__ == '__main__':
    main()
