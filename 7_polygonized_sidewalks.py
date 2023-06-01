from functions import *
from config import *
from shapely.ops import polygonize_full


for key in NEIGHBORHOODS:
    filename = key+sidewalks_suffix

    as_gdf = gpd.read_file(filename)

    only_sidewalks = as_gdf.loc[as_gdf['footway']=='sidewalk']

    sidewalk_blocks, dangles, cuts, invalids = polygonize_full(unary_union_from_gdf(only_sidewalks))

    multigeom_to_gdf(sidewalk_blocks,as_gdf.crs,key+pol_sidewalks_suffix)
    multigeom_to_gdf(dangles,as_gdf.crs,key+pol_sidewalks_suffix.replace(EXTENSION,'_dangles'+EXTENSION))
    multigeom_to_gdf(cuts,as_gdf.crs,key+pol_sidewalks_suffix.replace(EXTENSION,'_cuts'+EXTENSION))
    multigeom_to_gdf(invalids,as_gdf.crs,key+pol_sidewalks_suffix.replace(EXTENSION,'_invalids'+EXTENSION))



    