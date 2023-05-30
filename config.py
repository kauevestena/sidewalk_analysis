'''
    file containing constants in order to ease the process of reproduce te analysis undertaken
'''

CITY_SHORTNAME = 'curitba' #without spaces or uppercase characters
CITY_DESCRIPTION = 'Curitiba, Brazil'

# Key, description for Nominatim
NEIGHBORHOODS = {'agua_verde':'Água Verde, Curitiba','jardim_das_americas':'Jardim das Américas, Curitiba'}

highway_values = ['motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street']

sidewalks_dict = {'footway':['sidewalk','crossing'],'barrier':['kerb'],'kerb':True}

EXTENSION = '.geojson'

streets_suffix = '_streets'+EXTENSION

blocks_suffix = '_protoblocks'+EXTENSION

sidewalks_suffix = '_sidewalks'+EXTENSION

splitted_suffix = '_splitted'+EXTENSION

intersections_suffix = '_intersections'+EXTENSION

neighborhoods_descriptive_statistics_path = 'neighborhoods_descriptive.json'