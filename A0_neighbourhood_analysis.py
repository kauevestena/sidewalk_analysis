from functions import *
from config import *

characteristics = {}

for key in NEIGHBORHOODS:
    characteristics[key] = {}

    neighborhoods_path = key+EXTENSION

    as_gdf = gpd.read_file(neighborhoods_path)

    characteristics[key]['area'] = total_area(as_gdf)
    characteristics[key]['perimeter'] = total_perimeter(as_gdf)

dump_json(characteristics,neighborhoods_descriptive_statistics_path)



