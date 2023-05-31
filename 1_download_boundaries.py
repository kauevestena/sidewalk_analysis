#!/usr/bin/env python
# coding: utf-8

# In[1]:


from functions import *
from config import *


# In[2]:


city_boundaries = features_from_place(CITY_DESCRIPTION,{'admin_level':'8'})


# In[3]:


# find the best match between names and the input name for the city
correspondence = most_similar_string_in_df(city_boundaries,'name',CITY_SHORTNAME)


# In[4]:


city_row = city_boundaries[city_boundaries['name'] == correspondence]


# In[5]:


gdf_to_file(city_row,CITY_SHORTNAME+EXTENSION)


# In[6]:


for key in NEIGHBORHOODS:
    neigh_boundaries = features_from_place(NEIGHBORHOODS[key],{'admin_level':'10'})
    correspondence = most_similar_string_in_df(neigh_boundaries,'name',key)
    save_gdf_row_by_match(neigh_boundaries,'name',correspondence,key+EXTENSION)

