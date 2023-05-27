import requests
import pandas as pd
from bs4 import BeautifulSoup
from data import *
from cookies import * 

class GeocacheScraper:

    def __init__(self):

        # url for the table of all caches
        self.table_url = 'https://www.geocaching.com/api/proxy/web/search/v2'

        # url for the individual cache listing pages
        self.cache_url = 'https://www.geocaching.com/geocache/'
    
        # dataframe to copy over the scraped data
        self.df = pd.DataFrame(columns=[
            'id','code', 'name','premiumOnly','favoritePoints',
            'geocacheType','containerType','difficulty', 'terrain',
            'cacheStatus', 'latitude', 'longitude', 'detailsUrl', 'placedDate',
            'lastFoundDate', 'ownerName', 'ownerId', 'trackableCount'
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

    # Method to scrape for all cache data from the results table 
    def scrape_table_data(self):
        response = requests.get(self.table_url, params=table_params, cookies=table_cookies, headers=table_headers)
        res = response.json()['results']
    
        # Obtain all relevant data for non-premium caches and copy it over to the dataframe
        for i in range(len(res)):
            if res[i]['premiumOnly'] == False:
                data = res[i]
                self.df.loc[i, 'id'] = data['id']
                self.df.loc[i,'code'] =  data['code']
                self.df.loc[i,'name'] = data['name']
                self.df.loc[i,'premiumOnly'] = data['premiumOnly'],
                self.df.loc[i,'favoritePoints'] = data['favoritePoints'],
                self.df.loc[i,'geocacheType'] = data['geocacheType'],
                self.df.loc[i,'containerType'] = data['containerType'],
                self.df.loc[i,'difficulty'] = data['difficulty'],
                self.df.loc[i,'terrain'] = data['terrain'],
                self.df.loc[i,'cacheStatus'] = data['cacheStatus'],
                self.df.loc[i,'latitude'] = data['postedCoordinates']['latitude']
                self.df.loc[i,'longitude'] = data['postedCoordinates']['longitude']
                self.df.loc[i,'detailsUrl'] = data['detailsUrl']
                self.df.loc[i,'placedDate'] = data['placedDate']
                self.df.loc[i,'lastFoundDate'] = data['lastFoundDate']
                self.df.loc[i,'ownerName'] = data['owner']['username']
                self.df.loc[i,'ownerId'] = data['owner']['code']
                self.df.loc[i,'trackableCount'] = data['trackableCount']

        # Clean up data to obtain only the integer values
        self.df['premiumOnly'] = list(map(lambda x: x[0], list(self.df['premiumOnly'])))
        self.df['favoritePoints'] = list(map(lambda x: x[0], list(self.df['favoritePoints'])))
        self.df['geocacheType'] = list(map(lambda x: x[0], list(self.df['geocacheType'])))
        self.df['containerType'] = list(map(lambda x: x[0], list(self.df['containerType'])))
        self.df['difficulty'] = list(map(lambda x: x[0], list(self.df['difficulty'])))
        self.df['terrain'] = list(map(lambda x: x[0], list(self.df['terrain'])))
        self.df['cacheStatus'] = list(map(lambda x: x[0], list(self.df['cacheStatus'])))

        # Format URL link to individual caches
        self.df['detailsUrl'] = list(map(lambda x: "www.geocaching.com" + str(x), list(self.df['detailsUrl'])))

        # Format datetime into separate cols (either date or time)
        self.df['placedDate'] = list(map(lambda x: str(x).split("T")[0] if len(str(x)) > 0 else x, list(self.df['placedDate'])))
        found_date = [str(x).split("T")[0] if len(str(x)) > 0 else x for x in list(self.df['lastFoundDate'])]
        found_time = [str(x).split("T")[1] if len(str(x)) > 0 else x for x in list(self.df['lastFoundDate'])]
        self.df['lastFoundDate'] = found_date
        self.df['lastFoundTime'] = found_time

        # Rearrange columns
        self.df = self.df.reset_index()
        self.df = self.df.drop(columns=["index", "premiumOnly"])
        self.df = self.df.reindex(columns=[
            "id","code","name","geocacheType","containerType","difficulty","terrain",
            "cacheStatus","favoritePoints","trackableCount",
            "latitude","longitude","ownerId","ownerName",
            "placedDate","lastFoundDate","lastFoundTime","detailsUrl"
        ])

    # Method to scrape for cache description, hints and nos of times cache is found / not found (at the individual cache listing pages)
    def scrape_cache_desc(self):
        for i in range(len(self.df)):
            code = self.df.loc[i,'code']
            response = requests.get(self.cache_url + code, cookies=desc_cookies, headers=desc_headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # scrape for cache description
            desc = soup.find_all("span", {"id": "ctl00_ContentBody_LongDescription"})[0].text.replace("\xa0", " ").replace("\n", " ")

            # scrape for and decode cache hint
            hint = soup.find_all("div", {"id": "div_hint"})[0].text.replace("\r\n","").strip()
            decoded_hint = ""
            for char in hint:
                char = char.lower()
                if char not in self.hint_decryption_keys:
                    decoded_hint += char
                else:
                    decoded_hint += self.hint_decryption_keys[char]

            # scrape for total nos of times cache is found / not found
            tally = soup.find_all("ul", {"class": "LogTotals"})[0].text.strip().split(" ")
            found = tally[0]
            dnf = tally[1]

            self.df.loc[i, 'description'] = desc
            self.df.loc[i, 'hint'] = decoded_hint
            self.df.loc[i, 'total_found'] = found
            self.df.loc[i, 'total_did_not_find'] = dnf
     
    # method to export dataframe as a csv and json
    def export_files(self, filename):
        self.df.to_csv(filename + '.csv')
        self.df.to_json(filename + '.json', orient='records')

scraper = GeocacheScraper()
scraper.scrape_table_data()
scraper.scrape_cache_desc()
scraper.export_files('sg_caches')