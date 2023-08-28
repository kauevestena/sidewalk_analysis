from functions import *
from config import *


all_neighborhoods = []

for key in NEIGHBORHOODS:
    filepath = key+sidewalks_suffix

    footway_data = read_gdf_in_local_utm(filepath)

    footway_data['neighborhood'] = key

    only_crossings = footway_data.loc[footway_data['footway'] == 'crossing'].copy()
    only_sidewalks = footway_data.loc[footway_data['footway'] == 'sidewalk'].copy()


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

        number_sidewalks.append(only_sidewalks.intersects(geom).sum())

    only_crossings['number_kerbs'] = number_kerbs
    only_crossings['number_sidewalks'] = number_sidewalks

    all_neighborhoods.append(only_crossings)


all_crossings = gpd.GeoDataFrame(pd.concat(all_neighborhoods, ignore_index=True), crs=footway_data.crs)
all_crossings.to_file('all_neighborhoods_crossing_analysis.geojson')




# counting how many crossings we have per block:
all_blocks = read_gdf_in_local_utm('all_neighborhoods_block_analysis.geojson')

crossings_count = []
crossings_boolean = []

for i,btuple in enumerate(all_blocks.itertuples()):
    n_crossings = all_crossings.intersects(btuple.geometry).sum()

    crossings_count.append(n_crossings)

    if n_crossings == 0:
        crossings_boolean.append(False)
    else:
        crossings_boolean.append(True)

all_blocks['number_crossings'] = crossings_count
all_blocks['has_crossings'] = crossings_boolean

# rewriting: 
all_blocks.to_file('all_neighborhoods_block_analysis.geojson')


# exporting as centroids to facilitate the representation
all_crossings.geometry = all_crossings.geometry.centroid

all_crossings.to_file('all_neighborhoods_crossing_analysis_centroids.geojson')






    





