from functions import *
from config import *
from shapely.ops import polygonize_full


for key in NEIGHBORHOODS:
    filename = key+streets_suffix

    as_gdf = gpd.read_file(filename)

    proto_blocks, dangles, cuts, invalids = polygonize_full(unary_union_from_gdf(as_gdf))

    multigeom_to_gdf(proto_blocks,as_gdf.crs,key+blocks_suffix)
    