'''
    file containing constants in order to ease the process of reproduce te analysis undertaken
'''

CITY_SHORTNAME = 'curitba' #without spaces or uppercase characters
CITY_DESCRIPTION = 'Curitiba, Brazil'

# Key, description for Nominatim
NEIGHBORHOODS = {'agua_verde':'Água Verde, Curitiba','jardim_das_americas':'Jardim das Américas, Curitiba'}

highway_values = ['motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street']

sidewalks_dict = {'footway':['sidewalk','crossing'],'barrier':['kerb'],'kerb':True}

streets_suffix = '_streets.geojson'

blocks_suffix = '_protoblocks.geojson'

sidewalks_suffix = '_sidewalks.geojson'

splitted_suffix = '_splitted.geojson'

intersections_suffix = '_intersections.geojson'