from functions import *
from config import *

characteristics = {}

for key in NEIGHBORHOODS:
    characteristics[key] = {}

    # boundaries statistics
    boundaries_gdf = gpd.read_file(key+EXTENSION)

    characteristics[key]['area'] = total_area(boundaries_gdf)
    characteristics[key]['perimeter'] = total_perimeter_or_len(boundaries_gdf)

    # streets statistics
    streets_gdf = gpd.read_file(key+streets_suffix)
    characteristics[key]['roads_length'] = total_perimeter_or_len(streets_gdf)

    #protoblocks statistics
    protoblocks_gdf = gpd.read_file(key+blocks_suffix)
    characteristics[key].update(gdf_areas_description(protoblocks_gdf,'blocks'))

    # sideawalks statistics
    sidewalks_gdf = gpd.read_file(key+sidewalks_suffix)
    characteristics[key]['sidewalks_length'] = total_perimeter_or_len(sidewalks_gdf)




dump_json(characteristics,neighborhoods_descriptive_statistics_path)

statistics_df = pd.DataFrame(characteristics)

# dump also as .csv file
statistics_df.to_csv(neighborhoods_descriptive_statistics_path.replace('.json', '.csv'))



