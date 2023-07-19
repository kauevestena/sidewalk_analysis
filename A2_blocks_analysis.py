from functions import *
from config import *



resulting_gdfs = []

reconstructed_sidewalks = []

for key in NEIGHBORHOODS:

    extra_columns = {
    'contained_pol_sidewalks': [],
    'ratio_unary_sidewalk': [],
    'ratio_reconstructed_sidewalk': [],
    'diff_norm_ratio': [],
    'hausdorff_distance':[],
    'frechet_distance' :[],
    'hausd_fretch_diff' : [],
    'contained_pol_sidewalks_ids':[],
    'area_diff':[],
    'area_diff_perc':[],
    'neighborhood':[],
    'condition':[],
    'perimeter_diff':[],
    'perimeter_diff_abs':[],
    'perimeter_diff_perc':[],
    # 'centroid_distance': [],
    }

    # reading the protoblocks:
    blocks_gdf = read_gdf_in_local_utm(key+blocks_suffix)
    working_crs = blocks_gdf.crs

    # reading sidewalks as blocks:
    polyg_sidewalks_gdf = read_gdf_in_local_utm(key+pol_sidewalks_suffix)

    # reading splitted roads:
    splitted_roads_gdf = read_gdf_in_local_utm(key+splitted_suffix) 

    # reading original sidewalks:
    sidewalks_gdf  = read_gdf_in_local_utm(key+sidewalks_suffix)
    
    sidewalks_gdf  = sidewalks_gdf.loc[sidewalks_gdf['footway']=='sidewalk']

    # iterating over the blocks, to find the sidewalk polygon it belongs 
    for entry in blocks_gdf.itertuples():
        print(entry.Index,key)

        block_geom = entry.geometry

        block_centroid = block_geom.centroid

        # getting as linestring to use distance measurement
        # block_as_linestring = get_exterior_ring(block_geom)

        contained_pol_sidewalks_index = polyg_sidewalks_gdf.geometry.within(block_geom)

        contained_pol_sidewalks = polyg_sidewalks_gdf[contained_pol_sidewalks_index]


        contained_sidewalks_index = sidewalks_gdf.geometry.within(block_geom)

        contained_sidewalks = sidewalks_gdf[contained_sidewalks_index]


        contained_pol_sidewalks_ids = df_index_to_str(contained_pol_sidewalks,f'_{key}')
        # print(contained_pol_sidewalks_ids)

        contained_pol_sidewalks_n = contained_pol_sidewalks.shape[0]
        ratio_unary_sidewalk = None
        ratio_reconstructed_sidewalk = None
        ratio_diff = None
        hausdorf_d = None
        frechet_d = None
        hausd_fretch_diff = None
        area_diff = None
        area_diff_perc = None
        condition = ''
        perimeter_diff = None
        perimeter_diff_perc = None
        perimeter_diff_abs = None

        diff_ratio = 0
        centroid_distance = 0

        # contained_pol_sidewalks_ids = ''

        if EXTRA_TESTS:
            contained_pol_sidewalks.to_file(os.path.join('tests',f'{key}_{entry.Index}_{contained_pol_sidewalks.shape[0]}.geojson'))

        # print(entry.Index)

        # print('\n',contained_pol_sidewalks_n)

        pol_sidewalks_unary = unary_union_from_gdf(contained_pol_sidewalks)

        linestring_sidewalks_unary = get_exterior_ring(pol_sidewalks_unary)

        if contained_pol_sidewalks_n > 1:
            linestring_sidewalks_unary = exterior_ring_multipolygon(pol_sidewalks_unary)


        # print(linestring_sidewalks_unary)

        contained_streets_index = splitted_roads_gdf.geometry.within(block_geom.buffer(1))

        contained_streets = splitted_roads_gdf[contained_streets_index]

        if linestring_sidewalks_unary:
            if contained_pol_sidewalks_n > 1:
                condition = 'Closed Multi'
            else:
                condition = 'Closed'



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

            rec_sidewalk_line = get_interior_ring(merged_buffs,0)

            reconstructed_sidewalk = Polygon(rec_sidewalk_line).buffer(-curve_radius).buffer(curve_radius)

            reconstructed_sidewalks.append(reconstructed_sidewalk)

            ratio_reconstructed_sidewalk = normalized_perimeter_area_ratio(reconstructed_sidewalk)

            ratio_unary_sidewalk = normalized_perimeter_area_ratio(pol_sidewalks_unary)
            
            hausdorf_d = hausdorff_distance(linestring_sidewalks_unary,rec_sidewalk_line,densify=.05)

            frechet_d = frechet_distance(linestring_sidewalks_unary,rec_sidewalk_line,densify=.05)

            hausd_fretch_diff = hausdorf_d - frechet_d

            if ratio_reconstructed_sidewalk and ratio_unary_sidewalk:
                ratio_diff = ratio_reconstructed_sidewalk-ratio_unary_sidewalk

            area_diff_perc = calc_perc(reconstructed_sidewalk.area,pol_sidewalks_unary.area)

            if area_diff_perc < 150 and area_diff_perc > 50:
                area_diff =  reconstructed_sidewalk.area - pol_sidewalks_unary.area

            perimeter_diff_perc = calc_perc(reconstructed_sidewalk.length,pol_sidewalks_unary.length)

            # if perimeter_diff_perc < 150 and perimeter_diff_perc > 50:
            perimeter_diff =  reconstructed_sidewalk.length - pol_sidewalks_unary.length

            if condition == 'Closed':
                perimeter_diff_abs = abs(perimeter_diff)
            

        else:
            if contained_sidewalks.empty:
                condition = 'Without S.'
            else:
                condition = 'Unclosed'




        
        # print(contained_pol_sidewalks_n)
        extra_columns['hausdorff_distance'].append(hausdorf_d)


        extra_columns['frechet_distance'].append(frechet_d)

        extra_columns['hausd_fretch_diff'].append(hausd_fretch_diff)

        extra_columns['contained_pol_sidewalks'].append(contained_pol_sidewalks_n)
        

        extra_columns['ratio_unary_sidewalk'].append(ratio_unary_sidewalk)

        extra_columns['ratio_reconstructed_sidewalk'].append(ratio_reconstructed_sidewalk)

        extra_columns['diff_norm_ratio'].append(ratio_diff)
        # extra_columns['centroid_distance'].append(centroid_distance)

        extra_columns['contained_pol_sidewalks_ids'].append(contained_pol_sidewalks_ids)

        extra_columns['area_diff'].append(area_diff)
        extra_columns['area_diff_perc'].append(area_diff_perc)

        extra_columns['neighborhood'].append(NEIGHBORHOODS[key])

        extra_columns['condition'].append(condition)

        extra_columns['perimeter_diff'].append(perimeter_diff)
        extra_columns['perimeter_diff_abs'].append(perimeter_diff_abs)
        extra_columns['perimeter_diff_perc'].append(perimeter_diff_perc)




    extra_columns_df = pd.DataFrame(extra_columns)

    expanded_blocks_gdf = blocks_gdf.join(extra_columns_df)

    expanded_blocks_gdf.to_file(key+blocks_with_analysis_suffix)

    resulting_gdfs.append(expanded_blocks_gdf)

    # dump_json(extra_columns,f'{key}_extra_cols.json')


gpd.GeoDataFrame(pd.concat(resulting_gdfs, ignore_index=True), crs=working_crs).to_file('all_neighborhoods_block_analysis.geojson')

if EXTRA_TESTS:
    feature_list_to_gdf(reconstructed_sidewalks,working_crs,os.path.join('tests','reconstructed_sidewalks.geojson'))

        






