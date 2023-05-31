#!/usr/bin/bash

# run using:
# bash RUN_ALL.bash

# python executable:
PYTHONPATH=python3

# Base scripts

$PYTHONPATH 1_download_boundaries.py

$PYTHONPATH 2_download_streets.py

$PYTHONPATH 3_split_streets_intersections.py

$PYTHONPATH 4_create_protoblocks.py

$PYTHONPATH 5_download_sidewalks.py

$PYTHONPATH 6_download_kerbs.py

# Analysis

$PYTHONPATH A0_neighbourhood_analysis.py