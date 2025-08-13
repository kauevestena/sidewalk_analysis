# sidewalk_analysis

The "secondary" repository of [OSM Sidewalkreator](https://github.com/kauevestena/osm_sidewalkreator)

Contains the analysis carried out for the plugin's scientific publication:

> de Moraes Vestena, Kauê, Silvana Philippi Camboim, and Daniel Rodrigues dos Santos. 2023. “OSM Sidewalkreator: A QGIS Plugin for an Automated Drawing of Sidewalk Networks for OpenStreetMap”. European Journal of Geography 14 (4):66-84. https://doi.org/10.48088/ejg.k.ves.14.4.066.084.

Nevertheless, if you wanna reproduce the analysis (only the generated data*) you can select other Nominatim-valid regions, you just need to edit the "config.py" with the names of the places in the proper variables.

For convenience, there's the script RUN_ALL.bash that you can use to run all the scripts in the correct order. You might need to change the variable 

    PYTHONPATH=python3

For your actual path to the Python 3 executable.

You might need to install the requirements for the analysis (from the repository path):

    <your_python_executable_path> -m pip install -r requirements.txt

*: Some charts were generated in QGIS, and the projects of the publication were kept here, but there's no actually automated way of reproducing. Some charts were generated using Colab Notebooks, available in the folder called "chart_generation_notebooks", some may need some sort of fine-tuning to render properly meaningful charts.

## Cities experiment

The standard utility at `cities_experiment/main.py` fetches data directly
from the OpenStreetMap API using OSMnx. For offline analysis, you have two
options:

* `cities_experiment/main_pbf.py` expects pre-cut `.osm.pbf` extracts. Download
  the desired files (for example, from [Geofabrik](https://download.geofabrik.de/))
  and place them in `cities_experiment/pbfs` using the pattern
  `<city_name>.osm.pbf` (spaces replaced by underscores).
* `cities_experiment/main_planet.py` works with a single
  `planet-latest.osm.pbf` placed in the `cities_experiment` folder. The script
  geocodes each city to a bounding box and filters the planet file locally using
  [Pyrosm](https://github.com/HTenkanen/pyrosm).

Both scripts rely on Pyrosm, which is listed in the project requirements.
