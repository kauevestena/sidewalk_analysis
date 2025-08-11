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
