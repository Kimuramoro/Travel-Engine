#!/usr/bin/env python
# coding: utf-8

# # IST256 Project Deliverable 3 (P3)
# 
# ## Phase 3: Implementation
# 
# In this step, you submit the final version of working code. No changes to your code will be considered after this submission. It is important to take prior instructor feedback taken into consideration and these factor into your evaluation.
# 
# **IMPORTANT**: Don't forget to journal your work on the project as it factors into the evaluation of your work!

# ### Step 1: What is Your Idea, Again?
# 
# Please reiterate your project idea below (you can copy it from P1/P2).
# 
# `--== Double-click and put the title or brief description of your project below  ==--`
# This is a search engine for travelers. the user enters a keyword relating to what they want to go see, do, or experience. The program will return back pins on a map that correspond to these locations. the color of the pin corresponds to the programs confidence that that location is related to the keyword. It will also return the sentiment of the area based on news titles from the area, and the news title that best relates to the keyword and location.
# 

# ### Step 2: Project Code
# 
# Include all project code below. Make sure to execute your code to ensure it runs properly before you turn it in. 
# 

# In[1]:


pip install emoji


# In[2]:


import folium
from IPython.display import display,HTML
from ipywidgets import interact_manual
import ipywidgets as widgets
import emoji
import pandas as pd
import requests

key = "cb3cf11b59a14bb791919a7e56eae065"
endpoint = "https://ist256-rpolivie-text-analytics.cognitiveservices.azure.com/"
cities = pd.read_csv('https://query.data.world/s/olaqkxf2k4c4xc5kmzx26xi4ql7hms')

def keywordSearch(keyword,location):    
    url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/WebSearchAPI"
    querystring = {"q":f'{location} {keyword}',"pageNumber":"1","pageSize":"20","autoCorrect":"true"}
    headers = {
        "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com",
        "X-RapidAPI-Key": "36e707a89dmshf67581c39cd7da1p16206bjsnbdb02d514260"
        #'X-RapidAPI-Key': '9e734338c8mshee3ab62bca3466cp15aeeejsn99f532683f7a'
    }
    response = requests.get(url, headers=headers, params=querystring)
    search_results = response.json()
    return search_results

def combineresults(search_results,keyword):    
    mashed_results = ""
    TitleList = []
    for i in search_results['value']:
        i['title'].replace(',','').replace(keyword,'').replace('-',' ')
        splitTitle = i['title'].split()
        stringedTitle = ' '.join(splitTitle)
        mashed_results = mashed_results + stringedTitle + " | "
    return mashed_results

def location_detect(mashed_results):
    locations = []
    payload = { "documents": [ {"id": "1", "text": mashed_results } ] }
    url = f'{endpoint}text/analytics/v3.0/entities/recognition/general'
    header = { 'Ocp-Apim-Subscription-Key' : key}
    response = requests.post(url,headers=header, json=payload)
    response.raise_for_status()
    entities = response.json()
    for entity in entities['documents'][0]['entities']:
        if entity['category'] == 'Location':
            locations.append(entity['text'])
    #real_locations = list(set(locations))
    dict_locations = { i : locations.count(i) for i in locations }
    return dict_locations

def cityfilter(dict_locations): 
    filteredcities = {}
    isCountry = []
    i = 0
    m = len(dict_locations.keys())
    for place, confidence in dict_locations.items():
        i += 1 
        print(int((i/m)*100),"% complete", end = "\r")
        for index in cities.index:
            if cities.loc[index,'country_name'] == place:
                filteredcities[index] = confidence
                Id = cities.loc[index,'id']
                isCountry.append(Id)
                break
            elif cities.loc[index,'state_name'] == place:
                filteredcities[index] = confidence
                break
            elif cities.loc[index,'state_code'] == place:
                filteredcities[index] = confidence
                break
            #elif cities.loc[index,'name'] == place:
             #   filteredcities[index] = confidence
             #   break
    return filteredcities, isCountry
 
def confidence(filteredcities_df,filteredcities):
    confidence_df = filteredcities_df.copy()
    confidence_df['confidence'] = 1
    #confidence_list = [confidence for confidence, key in filteredcities.values()]
    for index in confidence_df.index:
        confidence_df.loc[index,'confidence'] = filteredcities.get(index)
    return confidence_df

def color(confidence_df):
    colorcoded_df = confidence_df.copy()
    colorcoded_df['color'] = 'lightred'
    colorcoded_df.loc[colorcoded_df['confidence'] == colorcoded_df['confidence'].max(), 'color'] = 'darkred'
    colorcoded_df.loc[colorcoded_df['confidence'] == 1, 'color'] = 'orange'
    return colorcoded_df

def geocode(location):
    query = {'q' : location, 'format': 'json'}
    url = 'https://nominatim.openstreetmap.org/search'
    response = requests.get(url, params = query)
    response.raise_for_status()
    geodata = response.json()
    return geodata[0]['lat'], geodata[0]['lon']

def lines(origin, pos):
    user_loc = (list(geocode(origin)))
    other = (list(pos))
    origin = [float(user_loc[0]),float(user_loc[1])]
    other = [float(other[0]),float(other[1])]
    return [origin,other]

def locationNews(search_results,location,keyword):
    myList = [location,keyword]
    newslist = []
    for i in search_results['value']:
        rawstring = i['title']
        if any(x in rawstring for x in myList):
            stop = rawstring.find('|')
            string = rawstring[:stop]
            newslist.append(string)
            return newslist
        
def sentiment(search_results):
    stringed_results = ''
    for i in search_results['value']:
        stringed_results = stringed_results + i['title']
    
    url = "https://twinword-sentiment-analysis.p.rapidapi.com/analyze/"
    querystring = {"text":stringed_results}
    headers = {
        "X-RapidAPI-Host": "twinword-sentiment-analysis.p.rapidapi.com",
        "X-RapidAPI-Key": "36e707a89dmshf67581c39cd7da1p16206bjsnbdb02d514260"
        }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    return f"sentiment : {data['type']}"

def countryDecide(state,country,Id,isCountry):
    if len(isCountry) != 0:
        for i in isCountry:
            if i == Id:
                return f'Somewhere in {country}'
            else:
                return f'{state},{country}'
    else:
        return f'{state},{country}' 


display(HTML("<H1>" + "THE TRAVELERS ALMANAC" + "</H1>"))
display(HTML("<H1>" + "Find Anything : See Anywhere" + "</H1>"))
@interact_manual(search='',origin='')
def draw_map(search,origin):
    search_results = keywordSearch(search,'')
    mashed_results = combineresults(search_results,search)
    dict_locations = location_detect(mashed_results)
    filteredcities,isCountry = cityfilter(dict_locations)
    filteredcities_df = cities.loc[filteredcities.keys()]
    confidence_df = confidence(filteredcities_df,filteredcities)
    colorcoded_df = color(confidence_df)
    
    origin_loc = geocode(origin)
    map = folium.Map(location=origin_loc, zoom_start=2)
    marker = folium.Marker(location=origin_loc,popup=origin)
    map.add_child(marker)
    
    for row in colorcoded_df.to_records():
        if row['confidence'] == colorcoded_df['confidence'].max():
            state = row['state_name']
            location_search = keywordSearch(search,state)
            location_news = locationNews(location_search,state,search)
            location_sentiment = sentiment(location_search)
        else:
            location_news = ''
            location_sentiment = ''
        
        pos = (row['latitude'],row['longitude'])
        state = str(row['state_name'])
        country = str(row['country_name'])
        Id = row['id']
        marker = folium.Marker(location=pos,
                               popup=f"{countryDecide(state,country,Id,isCountry)}   \n {location_sentiment}   \n {location_news}",
                               icon=folium.Icon(color=row['color']))
        coordinates = lines(origin,pos)
        my_PolyLine=folium.PolyLine(locations=coordinates,weight=2)
        map.add_child(marker)
        map.add_child(my_PolyLine)
    display(map) 
    display(confidence_df)


# In[ ]:





# ### Prepare for your Pitch and Reflection
# 
# With the project code complete, its time to prepare for the final deliverable - submitting your project demo Pitch and reflection.
# 

# In[ ]:


# run this code to turn in your work!
from coursetools.submission import Submission
Submission().submit()


# In[ ]:




