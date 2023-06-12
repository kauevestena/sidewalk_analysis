import osmnx as ox
import geopandas as gpd
import pandas as pd
import json, shutil, os
import Levenshtein
from shapely.ops import unary_union
from shapely.measurement import hausdorff_distance, frechet_distance
from shapely._geometry import get_exterior_ring, get_interior_ring,get_num_geometries, get_parts 
from shapely.geometry import LineString, Polygon, LinearRing, Point, MultiLineString
from math import atan2, degrees
import numpy as np


def features_from_place(place_name, tags):
    features = ox.geometries.geometries_from_place(place_name, tags=tags)
    return features


def features_to_file(place_name, tags,outpath):
    gdf = features_from_place(place_name,tags)

    transform_list_cols_to_str(gdf)

    gdf.to_file(outpath)

def transform_list_cols_to_str(df):
    # to correct the problem with 
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: str(x))


def gdf_to_file(gdf,outpath):
    transform_list_cols_to_str(gdf)
    gdf.to_file(outpath)


def read_json(inputpath):
    with open(inputpath) as reader:
        data = reader.read()

    return json.loads(data)
    
def dump_json(inputdict,outputpath,indent=4):
    with open(outputpath,'w+',encoding='utf8') as json_handle:
        json.dump(inputdict,json_handle,indent=indent,ensure_ascii=False)

def most_similar_string(string_list,target_string):
    return min(string_list, key=lambda x: Levenshtein.distance(x, target_string))

def most_similar_string_in_df(df,column,target_string):
    return most_similar_string(list(df[column].fillna('NULL')),target_string)

def save_gdf_row_by_match(gdf,colum,value,outputpath):
    row = gdf[gdf[colum] == value]
    gdf_to_file(row,outputpath)

def wipe_osmnx_cache(folderpath='cache'):
    if os.path.exists(folderpath):
        shutil.rmtree(folderpath)

def unary_union_from_gdf(input_gdf):
    return unary_union(input_gdf.geometry)

def multigeom_to_gdf(inputgeom,crs,outfilepath=None):

    splitted_geoms = {
    'names' : [],
    'geometry' : []
    }

    for i,subgeom in enumerate(inputgeom.geoms):
        splitted_geoms['names'].append(f'{i}')
        splitted_geoms['geometry'].append(subgeom)

    as_gdf = gpd.GeoDataFrame(splitted_geoms,crs=crs)
    

    if outfilepath:
        # gdf_to_file(as_gdf,outfilepath)
        as_gdf.to_file(outfilepath)


    return as_gdf


def find_intersections(input_gdf,return_gdf = True):

    intersections_dict = {'names':[],'geometry':[]}

    for i,line in enumerate(input_gdf.geometry):
        for j,line2 in enumerate(input_gdf.geometry):
            if not i == j:
                if line.intersects(line2):
                    intersec = line.intersection(line2)
                    intersections_dict['names'].append(f'{i} {j} ')
                    intersections_dict['geometry'].append(intersec)

    if return_gdf:
        return gpd.GeoDataFrame(intersections_dict,crs=input_gdf.crs)
    else:
        return MultiPoint(intersections_dict['geometry'])
    

def total_area(input_gdf):
    prj_crs = input_gdf.estimate_utm_crs()
    return sum(input_gdf.to_crs(prj_crs).geometry.area)

def total_perimeter_or_len(input_gdf):
    '''
    Returns the geopandas "length", 
    that shall be the total length for linear 
    geometries or perimeter for areas
    '''
    prj_crs = input_gdf.estimate_utm_crs()
    return sum(input_gdf.to_crs(prj_crs).geometry.length)


def df_element_count(input_gdf):
    return input_gdf.shape[0]

def gdf_areas_description(input_gdf,preffix=None):
    prj_crs = input_gdf.estimate_utm_crs()
    as_dict = input_gdf.to_crs(prj_crs).geometry.area.describe().to_dict()

    if preffix:
        as_dict = {f'{preffix}_{key}': value for key, value in as_dict.items()}

    return as_dict

def normalized_perimeter_area_ratio(inputgeom,tol=0.000000001):
    '''
         calculates the normalized ratio between perimeter and areas
    '''

    if inputgeom.area > tol:
        return (inputgeom.length*inputgeom.length) / inputgeom.area


def project_to_estimate_utm(input_gdf):
    return input_gdf.to_crs(input_gdf.estimate_utm_crs())

def apply_func_on_estimate_utm(inout_gdf:gpd.GeoDataFrame,func,outcolumnname:str,inputcolum='geometry'):
    inout_gdf[outcolumnname] = inout_gdf.to_crs(inout_gdf.estimate_utm_crs())[inputcolum].apply(func)

def centroids_difference(p1,p2):
    return LineString([p1,p2]).length


def calculate_azimuth(point1, point2):
    dx = point2.x - point1.x
    dy = point2.y - point1.y
    azimuth = atan2(dy, dx)
    return degrees(azimuth) % 360

def azimuth_std(polygon):
    
    if isinstance(polygon,Polygon):
        as_linearring = get_exterior_ring(polygon)
    if isinstance(polygon,LinearRing):
        as_linearring = polygon

    prev_coords = None
    azimuth_list = []
    for coord in (as_linearring.coords):
        as_point = Point(*coord)

        if prev_coords:
            azimuth_list.append(calculate_azimuth(as_point, prev_coords))

        prev_coords=as_point

    return np.array(azimuth_list).std()

def read_gdf_in_local_utm(inputpath):
    gdf = gpd.read_file(inputpath)

    return gdf.to_crs(gdf.estimate_utm_crs())

def feature_list_to_gdf(input_feature_list,crs='EPSG:4326',filepath=None):
    ids = [i[0] for i in enumerate(input_feature_list)]

    as_dict = {
        'ids' : ids,
        'geometry' : input_feature_list,
    }

    as_gdf = gpd.GeoDataFrame(as_dict,crs=crs)

    if filepath:
        as_gdf.to_file(filepath)

    return as_gdf    


def df_index_to_str(input_df,suffix=''):
    if not input_df.empty:
        return "_".join(list(map(str,list(input_df.index))))+suffix
    
def create_folder_if_not_exists(folderpath):
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)

def exterior_ring_multipolygon(input_multipolygon):
    return MultiLineString([get_exterior_ring(geom) for geom in get_parts(input_multipolygon)])

def calc_perc(ref_val,val,min_val=0.000001):
    if ref_val > min_val:
        return val/ref_val*100
    
def geom_area(inputpolygon):
    return inputpolygon.area