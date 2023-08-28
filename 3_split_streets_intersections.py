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

    # intersections_gdf.to_file(key+intersections_suffix)

    # split:

    print('splits of ',key)

    all_lines = unary_union_from_gdf(streets_gdf)
    
    splitted = split(all_lines,unary_union_from_gdf(intersections_gdf))

    splitted_gdf = multigeom_to_gdf(splitted,streets_gdf.crs,key+splitted_suffix)


    # now generating the intersections using the splitted:
    intersections_gdf2 = find_intersections(splitted_gdf).dissolve().explode()[['geometry']]

    intersections = []


    local_utm = intersections_gdf2.estimate_utm_crs()
    test_gdf2 = intersections_gdf2.to_crs(local_utm)
    test_splitted = splitted_gdf.to_crs(local_utm)

    for i,tuple in enumerate(test_gdf2.itertuples()):
        if i % 10 == 0:
            print(i)

        small_buff = tuple.geometry.buffer(1)

        num_intersects = test_splitted.intersects(small_buff).sum()

        intersections.append(num_intersects)

    intersections_gdf2['number'] = intersections

    intersections_gdf2.to_file(key+intersections_suffix)