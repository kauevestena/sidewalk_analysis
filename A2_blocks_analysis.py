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
    working_crs = blocks_gdf.crs

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
            contained_sidewalks.to_file(os.path.join('tests',f'{key}_{entry.Index}_{contained_sidewalks.shape[0]}.geojson'))

        # print('\n',contained_sidewalks_n)

        pol_sidewalks_unary = unary_union_from_gdf(contained_sidewalks)

        linestring_sidewalks_unary = get_exterior_ring(pol_sidewalks_unary)

        # print(linestring_sidewalks_unary)

        contained_streets_index = splitted_roads_gdf.geometry.within(block_geom.buffer(1))

        contained_streets = splitted_roads_gdf[contained_streets_index]

        if linestring_sidewalks_unary:
            buffs = []
            for road_stretch in contained_streets.itertuples():
                stretch_geom = road_stretch.geometry

                distance = stretch_geom.distance(linestring_sidewalks_unary)

                buffs.append(stretch_geom.buffer(distance))

            merged_buffs = unary_union(buffs)

            if EXTRA_TESTS:
                as_dict = {'name':['buff'],'geometry':[merged_buffs]}
                buffs_gdf = gpd.GeoDataFrame(as_dict,crs=working_crs)
                buffs_gdf.to_file(os.path.join('tests',f'{int(merged_buffs.area)}_buff_{key}_{entry.Index}.geojson'))

            reconstructed_sidewalk = get_interior_ring(merged_buffs,0)


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


        

        






