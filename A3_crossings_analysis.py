from functions import *
from config import *


all_neighborhoods = []

for key in NEIGHBORHOODS:
    filepath = key+sidewalks_suffix

    all_data = read_gdf_in_local_utm(filepath)

    all_data['neighborhood'] = key

    only_crossings = all_data.loc[all_data['footway'] == 'crossing'].copy()
    only_sidewalks = all_data.loc[all_data['footway'] == 'sidewalk'].copy()


    # reading additional data:
    protoblocks = read_gdf_in_local_utm(key + blocks_suffix)
    kerbs = read_gdf_in_local_utm(key + kerbs_suffix)
    kerbs_small_buf = kerbs.buffer(1)
    intersections = read_gdf_in_local_utm(key + intersections_suffix)

    number_kerbs = []
    number_sidewalks = []

    # iterating the crossings:
    for i,dtuple in enumerate(only_crossings.itertuples()):
        if i % 50 == 0:
            print(i)

        geom = dtuple.geometry

        number_kerbs.append(kerbs_small_buf.intersects(geom).sum())

        number_sidewalks.append(only_sidewalks.intersects(geom.buffer(.2)).sum())

    only_crossings['number_kerbs'] = number_kerbs
    only_crossings['number_sidewalks'] = number_sidewalks

    all_neighborhoods.append(only_crossings)


all_data = gpd.GeoDataFrame(pd.concat(all_neighborhoods, ignore_index=True), crs=all_data.crs)
all_data.to_file('all_neighborhoods_crossing_analysis.geojson')

all_data.geometry = all_data.geometry.centroid

all_data.to_file('all_neighborhoods_crossing_analysis_centroids.geojson')


    

    







    





