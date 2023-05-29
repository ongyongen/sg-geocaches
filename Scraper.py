import math
import requests
import pandas as pd
import geopandas as gpd 
from shapely.geometry import Point
from bs4 import BeautifulSoup
from data import *
from cookies import * 

class GeocacheScraper:

    def __init__(self):

        # url for the table of all caches
        self.table_url = 'https://www.geocaching.com/api/proxy/web/search/v2'

        # url for the individual cache listing pages
        self.cache_url = 'https://www.geocaching.com/geocache/'

        # geodataframe of SG planning area polygons (from data.gov.sg)
        self.gdf = gpd.read_file("map.geojson")
    
        # dataframe to copy over the scraped data
        self.df = pd.DataFrame(columns=[
            'cache_id','cache_code', 'name','favorite_points',
            'geocache_type','container_type','difficulty', 'terrain',
            'latitude', 'longitude', 'details_url', 'placed_date',
            'last_found_date', 'owner_name', 'owner_id', 'trackable_count'
            ]
        )
        
        # dictionary for decrypting the hints (at the individual cache listing pages)
        self.hint_decryption_keys = {
            "a": "n", "n": "a", "b": "o", "o": "b", "c": "p", "p": "c",
            "d": "q", "q": "d", "e": "r", "r": "e", "f": "s", "s": "f",
            "g": "t", "t": "g", "h": "u", "u": "h", "i": "v", "v": "i",
            "j": "w", "w": "j", "k": "x", "x": "k", "l": "y", "y": "l",
            "m": "z", "z": "m"
        }

        # dictionary for mapping int values to cache types
        self.cache_types = {
            2 : "traditional",
            3 : "multi-cache",
            4 : "virtual",
            5 : "letterbox",
            6 : "event",
            8 : "mystery",
            137 : "earth",
            1858 : "whereigo"
        }

        # dictionary for mapping int values to container types
        self.container_types = {
            1 : "not specified",
            2 : "micro",
            3 : "regular",
            4 : "large",
            5 : "virtual",
            6 : "other",
            8 : "small"
        }

    # Method to scrape for all cache data from the results table 
    def scrape_table_data(self):
        response = requests.get(self.table_url, params=table_params, cookies=table_cookies, headers=table_headers)
        res = response.json()['results']
    
        # Obtain all relevant data for non-premium caches and copy it over to the dataframe
        for i in range(len(res)):
            if res[i]['premiumOnly'] == False:
                data = res[i]
                self.df.loc[i, 'cache_id'] = data['id']
                self.df.loc[i,'cache_code'] =  data['code']
                self.df.loc[i,'name'] = data['name']
                self.df.loc[i,'favorite_points'] = data['favoritePoints'],
                self.df.loc[i,'difficulty'] = data['difficulty'],
                self.df.loc[i,'terrain'] = data['terrain'],
                self.df.loc[i,'latitude'] = data['postedCoordinates']['latitude']
                self.df.loc[i,'longitude'] = data['postedCoordinates']['longitude']
                self.df.loc[i,'details_url'] = data['detailsUrl']
                self.df.loc[i,'placed_date'] = data['placedDate']
                self.df.loc[i,'last_found_date'] = data['lastFoundDate']
                self.df.loc[i,'owner_name'] = data['owner']['username']
                self.df.loc[i,'owner_id'] = data['owner']['code']
                self.df.loc[i,'trackable_count'] = data['trackableCount']

                # Map int representation to cache and container type 
                geocache_type = data['geocacheType']
                if geocache_type not in self.cache_types:
                    self.df.loc[i,'geocache_type'] = "other"
                else:
                    self.df.loc[i,'geocache_type'] = [self.cache_types[geocache_type]]

                container_type = data['containerType']
                if container_type not in self.container_types:
                    self.df.loc[i,'container_type'] = "other"
                else:
                    self.df.loc[i,'container_type'] = [self.container_types[container_type]]

        # Clean up data to obtain only the integer values
        self.df['favorite_points'] = list(map(lambda x: x[0], list(self.df['favorite_points'])))
        self.df['geocache_type'] = list(map(lambda x: x[0], list(self.df['geocache_type'])))
        self.df['container_type'] = list(map(lambda x: x[0], list(self.df['container_type'])))
        self.df['difficulty'] = list(map(lambda x: x[0], list(self.df['difficulty'])))
        self.df['terrain'] = list(map(lambda x: x[0], list(self.df['terrain'])))

        # Format URL link to individual caches
        self.df['details_url'] = list(map(lambda x: "www.geocaching.com" + str(x), list(self.df['details_url'])))

        # Format datetime into separate cols (either date or time)
        self.df['placed_date'] = list(map(lambda x: str(x).split("T")[0] if len(str(x)) > 0 else x, list(self.df['placed_date'])))
        found_date = [str(x).split("T")[0] if len(str(x)) > 0 else x for x in list(self.df['last_found_date'])]
        self.df['last_found_date'] = found_date

        # match coordinates to the correct planning area polygon 
        self.df = self.df.reset_index()
        for i in range(len(self.df)):
            point = Point(self.df.loc[i,'longitude'], self.df.loc[i,'latitude'])
            found_pa = False
            for j in range(len(self.gdf)):
                polygon = self.gdf.loc[j,'geometry']
                if polygon.contains(point):
                    found_pa = True
                    self.df.loc[i,'planning_area'] = self.gdf.loc[j,'PLN_AREA_N']
                    break
            if found_pa == False:
                self.df.loc[i,'planning_area'] = "NIL"

        # filter out entries in Johor
        self.df = self.df[self.df['planning_area'] != "NIL"]
        
        # Rearrange columns
        self.df = self.df.reset_index()
        self.df = self.df.drop(columns=["level_0", "index"])
        self.df = self.df.reindex(columns=[
            "cache_id","cache_code","name","geocache_type","container_type","difficulty","terrain",
            "favorite_points","trackable_count","latitude","longitude","planning_area", 
            "owner_id","owner_name","placed_date","last_found_date","last_found_time","details_url"
        ])

        print("Done scraping from table")

    # Method to scrape for cache description, hints and nos of times cache is found / not found (at the individual cache listing pages)
    def scrape_cache_desc(self):
        for i in range(len(self.df)):
            code = self.df.loc[i,'cache_code']
            response = requests.get(self.cache_url + code, cookies=desc_cookies, headers=desc_headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # scrape for cache description
            desc = ""
            if len(soup.find_all("span", {"id": "ctl00_ContentBody_LongDescription"})) > 0:
                desc = soup.find_all("span", {"id": "ctl00_ContentBody_LongDescription"})[0].text.replace("\xa0", " ").replace("\n", " ")

            # scrape for and decode cache hint
            hint = ""
            if len(soup.find_all("div", {"id": "div_hint"})) > 0:
                hint = soup.find_all("div", {"id": "div_hint"})[0].text.replace("\r\n","").strip()

            decoded_hint = ""
            for char in hint:
                char = char.lower()
                if char not in self.hint_decryption_keys:
                    decoded_hint += char
                else:
                    decoded_hint += self.hint_decryption_keys[char]
            
            print("Scraped: " + code)

            # scrape for total nos of times cache is found / not found
            tally = soup.find_all("ul", {"class": "LogTotals"})[0].text.strip().split(" ")
            found = int(tally[0].replace(",",""))
            dnf = int(tally[1].replace(",",""))
            self.df.loc[i, 'description'] = desc
            self.df.loc[i, 'hint'] = decoded_hint
            self.df.loc[i, 'total_found'] = found
            self.df.loc[i, 'total_did_not_find'] = dnf
            self.df.loc[i, 'found_rate'] = math.ceil((found/(found+dnf)) * 100)

        print("Done scraping from individual cache description pages")

    # clean the file one last time to remove invalid entries (ie missing detailsUrl)
    def clean_files_before_export(self):
        self.df = self.df[self.df['details_url'].str.strip().astype(bool)]
        self.df = self.df.reset_index()
        self.df = self.df.drop(columns=["index"])

    # method to export dataframe as a csv and json
    def export_files(self, filename):
        self.df.to_json(filename + '.json', orient='records')

# Start the scraper
scraper = GeocacheScraper()
scraper.scrape_table_data()
scraper.scrape_cache_desc()
scraper.clean_files_before_export()
scraper.export_files('sg_geocaches')
