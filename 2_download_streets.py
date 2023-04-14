#!/usr/bin/env python
# coding: utf-8

# In[1]:


from functions import *
from config import *


# In[2]:


# sometimes it just doesn't update stuff
wipe_osmnx_cache()


# In[3]:


gdf_dict = {}
for key in NEIGHBORHOODS:
    # gdf_dict[key] = features_from_place(key,{'highway':True})
    features_to_file(NEIGHBORHOODS[key],{'highway':highway_values},key+streets_suffix)

