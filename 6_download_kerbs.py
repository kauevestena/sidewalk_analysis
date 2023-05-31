#!/usr/bin/env python
# coding: utf-8

# In[1]:


from functions import *
from config import *



wipe_osmnx_cache()


gdf_dict = {}
for key in NEIGHBORHOODS:
    # gdf_dict[key] = features_from_place(key,{'highway':True})
    features_to_file(NEIGHBORHOODS[key],kerbs_dict,key+kerbs_suffix)

