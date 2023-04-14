from functions import *
from config import *
from shapely.ops import split



for key in NEIGHBORHOODS:
    inputfilename = key+streets_suffix

    streets_gdf = gpd.read_file(inputfilename)


    # intersections:

    print('intersections of ',key)

    intersections_gdf = find_intersections(streets_gdf)

    intersections_gdf = intersections_gdf.sjoin(intersections_gdf)

    intersections_gdf.to_file(key+intersections_suffix)

    # split:

    print('splits of ',key)

    all_lines = unary_union_from_gdf(streets_gdf)
    
    splitted = split(all_lines,unary_union_from_gdf(intersections_gdf))

    splitted_gdf = multigeom_to_gdf(splitted,streets_gdf.crs,key+splitted_suffix)

