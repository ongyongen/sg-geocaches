# sg-geocaches
Scraper for all non-premium geocaches in Singapore from https://www.geocaching.com

Libraries used
- pandas (https://pandas.pydata.org)
- BeautifulSoup (https://beautiful-soup-4.readthedocs.io/en/latest/)
- requests (https://pypi.org/project/requests/)

Setup required
- Create `cookies.py` file
- Go to https://www.geocaching.com/play/results/?asc=true&sort=distance (cache data table) and https://www.geocaching.com/geocache/GC9GZHA (or any other individual cache listing page)
- Go to the network tab under dev tools and copy the cURL command that returns the JSON data (for the cache table page) or the HTML doc (for the individual cache listing page)
- Cache table page :
  <img width="1200" alt="Screenshot 2023-05-27 at 6 53 03 PM" src="https://github.com/ongyongen/sg-geocaches/assets/97529863/d89ead3b-d250-437f-b44c-b40631eb8453">
  <img width="1200" alt="Screenshot 2023-05-27 at 6 54 09 PM" src="https://github.com/ongyongen/sg-geocaches/assets/97529863/6bfae413-6887-4fc3-b2d8-2e2df85514b2">
- Individual cache listing page : 
  <img width="1200" alt="Screenshot 2023-05-27 at 7 20 54 PM" src="https://github.com/ongyongen/sg-geocaches/assets/97529863/d94d5183-22eb-4d99-abb1-68aaa3fa0a3d">
  <img width="1200" alt="Screenshot 2023-05-27 at 7 26 46 PM" src="https://github.com/ongyongen/sg-geocaches/assets/97529863/4966af5d-0367-42f2-b8fb-59bf5901763d">
- Convert cURL code to Python at this link : https://curlconverter.com/python/ and copy over the cookies data into `cookies.py`
- Data in `cookies.py`
 <br></br><img width="250" alt="Screenshot 2023-05-27 at 7 03 11 PM" src="https://github.com/ongyongen/sg-geocaches/assets/97529863/a69e23ec-da18-4d77-bb21-822370561979">
- run the `Scraper.py` file to start the scraping (edit the name of the output CSV and JSON file if needed)

Note
- Example output files with Singapore's geocache data are provided within this repo in CSV and JSON format (`sg_caches.csv` and `sg_caches.json`)
- These files contain data that are last scraped on 27 May 2023

