import os
import json
import osmnx as ox
import pandas as pd
from shapely.geometry import LineString
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def read_json(inputpath):
    with open(inputpath) as reader:
        data = reader.read()
    return json.loads(data)

def dump_json(inputdict, outputpath):
    with open(outputpath, 'w+') as json_handle:
        json.dump(inputdict, json_handle)

def calc_len_sum(inputdf):
    if inputdf.empty:
        return 0
    sum = 0
    new_crs = inputdf.estimate_utm_crs()
    for geom in inputdf.to_crs(new_crs)['geometry']:
        if isinstance(geom, LineString):
            sum += geom.length
    return sum / 1000

def generate_boxplot(data, output_folder):
    fig, ax = plt.subplots(figsize=(15, 10))
    df = pd.DataFrame(data).T
    df.plot(kind='box', ax=ax)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'cities_boxplot.png'))

def generate_wordcloud(data, output_folder):
    with_sidewalk_data = {city: data[city].get('with_sidewalk', 0) for city in data}
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(with_sidewalk_data)
    plt.figure(figsize=(15, 10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(os.path.join(output_folder, 'sidewalk_wordcloud.png'))

def main():
    csvpath = "cities_experiment/biggest_cities.csv"
    outpath = "cities_experiment/biggest_cities_23set2022.json"
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
        'car_len': {'highway': ['motorway', 'trunk', 'primary', 'tertiary', 'unclassified', 'residential']},
        'footway_len': {'highway': ['footway', 'path']},
        'sidewalk_len': {'footway': ['sidewalk', 'crossing']},
        'with_sidewalk': {'sidewalk': True}
    }

    for i, cityname in enumerate(cities_df['Name']):
        try:
            if i > 20: # Limiting to 20 cities for testing purposes
                break
            if not cityname in data:
                data[cityname] = {}
            for category in filters:
                print(i, cityname, category)
                if not category in data[cityname]:
                    print(i, cityname, category)
                    print()
                    outpath_file = os.path.join(outfiles_folderpath, f"{cityname}_{category}.geojson")
                    current_gdf = ox.geometries_from_place(cityname, filters[category])
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
