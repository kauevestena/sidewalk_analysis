from functions import *
from config import *

extra_columns = {
    'contains': []
}

for key in NEIGHBORHOODS:
    # reading the protoblocks:
    blocks_gdf = gpd.read_file(key+blocks_suffix)

    # readding sidewalks as blocks:
    polyg_sidewalks_gdf = gpd.read_file(key+pol_sidewalks_suffix)

    # iterating over the blocks, to find the sidewalk
    for line in blocks_gdf.itertuples():
        contained_index = polyg_sidewalks_gdf.geometry.within(line.geometry)

        contained = polyg_sidewalks_gdf[contained_index]

        extra_columns['contains'].append(contained.shape[0])

        if EXTRA_TESTS:
            contained.to_file(os.path.join('tests',f'{line.Index}_{contained.shape[0]}.geojson'))






