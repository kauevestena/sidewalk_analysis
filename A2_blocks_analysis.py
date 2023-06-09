from functions import *
from config import *

extra_columns = {
    'contained_sidewalks': [],
    # 'diff_norm_ratio': [],
    # 'centroid_distance': [],
}

for key in NEIGHBORHOODS:
    # reading the protoblocks:
    blocks_gdf = read_gdf_in_local_utm(key+blocks_suffix)

    # reading sidewalks as blocks:
    polyg_sidewalks_gdf = read_gdf_in_local_utm(key+pol_sidewalks_suffix)

    # reading splitted roads:
    splitted_roads_gdf = read_gdf_in_local_utm(key+splitted_suffix)    

    # iterating over the blocks, to find the sidewalk polygon it belongs 
    for entry in blocks_gdf.itertuples():
        block_geom = entry.geometry

        block_centroid = block_geom.centroid

        # getting as linestring to use distance measurement
        block_as_linestring = get_exterior_ring(block_geom)

        contained_sidewalks_index = polyg_sidewalks_gdf.geometry.within(block_geom)

        contained_sidewalks = polyg_sidewalks_gdf[contained_sidewalks_index]

        contained_sidewalks_n = contained_sidewalks.shape[0]
        extra_columns['contained_sidewalks'].append(contained_sidewalks_n)
        diff_ratio = 0
        centroid_distance = 0

        if EXTRA_TESTS:
            contained_sidewalks.to_file(os.path.join('tests',f'{entry.Index}_{contained_sidewalks.shape[0]}.geojson'))

        print('\n',contained_sidewalks_n)

        as_unary = unary_union_from_gdf(contained_sidewalks)

        # contained roads 

        # if not contained_sidewalks.empty:
            

            # for each in contained_sidewalks.itertuples():
            #     sidewalk_pol_geom = each.geometry
            #     sidewalk_as_linestring = get_exterior_ring(sidewalk_pol_geom)

            #     sidewalk_pol_centroid = sidewalk_pol_geom.centroid

            # centroid_distance += centroids_difference(block_centroid,sidewalk_pol_centroid)

            #     distance_block_sidewalk = block_as_linestring.distance(sidewalk_as_linestring)



            # print(contained_sidewalks_n)
            
            
        # extra_columns['diff_norm_ratio'].append(diff_ratio)
        # extra_columns['centroid_distance'].append(centroid_distance)


        

        






