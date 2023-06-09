'''
    file containing constants in order to ease the process to reproduce the analysis
'''

CITY_SHORTNAME = 'curitba' #without spaces or uppercase characters
CITY_DESCRIPTION = 'Curitiba, Brazil'

# Key, description for Nominatim
NEIGHBORHOODS = {'agua_verde':'Água Verde, Curitiba','jardim_das_americas':'Jardim das Américas, Curitiba'}

# cutoff threshold for non-blocks
block_ratio_cutoff = 5

# extra tests available on some scripts
EXTRA_TESTS = True

# less variable constants:

highway_values = ['motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street']

sidewalks_dict = {'footway':['sidewalk','crossing']}

kerbs_dict = {'barrier':['kerb'],'kerb':True}

EXTENSION = '.geojson'

streets_suffix = '_streets'+EXTENSION

blocks_suffix = '_protoblocks'+EXTENSION

sidewalks_suffix = '_sidewalks'+EXTENSION

pol_sidewalks_suffix = '_sidewalk_polygons'+EXTENSION

kerbs_suffix = '_kerbs'+EXTENSION

splitted_suffix = '_splitted'+EXTENSION

intersections_suffix = '_intersections'+EXTENSION

neighborhoods_descriptive_statistics_path = 'neighborhoods_descriptive.json'

normalized_ratio_fieldname = 'norm_p_a_ratio'
az_std_fieldname = 'azimuth_std'

