from functions import *
from config import *
from lineage_functions import *
from tqdm import tqdm

all_gdf = []
# loading data
for key in NEIGHBORHOODS:
    sidewalks = gpd.read_file(key+sidewalks_suffix)

    sidewalks['feature_type'] = sidewalks['footway']

    kerbs =     gpd.read_file(key+kerbs_suffix)

    kerbs['feature_type'] = 'kerb'

    all_neigh_data = gpd.GeoDataFrame(pd.concat([sidewalks,kerbs], ignore_index=True), crs=sidewalks.crs)

    all_neigh_data = all_neigh_data[['geometry','osmid','element_type','feature_type']]

    all_neigh_data['neighborhood'] = key

    total_feats = all_neigh_data.shape[0]

    start_months = []
    number_revs = []
    for feature in tqdm(all_neigh_data.itertuples(),total=total_feats):
        num_updates,d,m,y = get_datetime_update_info(feature.osmid,feature.element_type,desired_index=0)

        # this will obey alphabetical order: 
        start_months.append(f'{y}_{m}')

        number_revs.append(num_updates)

    all_neigh_data['number_revs'] = number_revs
    all_neigh_data['start_month'] = start_months

    all_gdf.append(all_neigh_data)



gpd.GeoDataFrame(pd.concat(all_gdf, ignore_index=True), crs=sidewalks.crs).to_file('lineage_analysis.geojson')