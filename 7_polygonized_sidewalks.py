from functions import *
from config import *
from shapely.ops import polygonize_full
from shapely import minimum_clearance


for key in NEIGHBORHOODS:
    filename = key+sidewalks_suffix

    as_gdf = gpd.read_file(filename)

    only_sidewalks = as_gdf.loc[as_gdf['footway']=='sidewalk']

    sidewalk_blocks, dangles, cuts, invalids = polygonize_full(unary_union_from_gdf(only_sidewalks))

    multigeom_to_gdf(dangles,as_gdf.crs,key+pol_sidewalks_suffix.replace(EXTENSION,'_dangles'+EXTENSION))
    multigeom_to_gdf(cuts,as_gdf.crs,key+pol_sidewalks_suffix.replace(EXTENSION,'_cuts'+EXTENSION))
    multigeom_to_gdf(invalids,as_gdf.crs,key+pol_sidewalks_suffix.replace(EXTENSION,'_invalids'+EXTENSION))

    # adding custom columns like minimum clearance
    sidewalk_blocks_gdf = multigeom_to_gdf(sidewalk_blocks,as_gdf.crs)

    # sidewalk_blocks_gdf['ḿin_clearance'] = sidewalk_blocks_gdf['geometry'].apply(minimum_clearance)
    apply_func_on_estimate_utm(sidewalk_blocks_gdf,minimum_clearance,'ḿin_clearance')

    sidewalk_blocks_gdf.to_file(key+pol_sidewalks_suffix)




    