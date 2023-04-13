import osmnx as ox
import geopandas as gpd
import json, shutil, os
import Levenshtein

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