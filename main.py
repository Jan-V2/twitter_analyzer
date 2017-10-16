import os


import time
from pprint import pprint
from twitter_api_keys import get_api_array
import tweepy

#todo make data and code differnt dirs so only the code syncs to github

def do_trendscrape():
    # this list is just under 150 trends, so it can be downloaded in 2 15 min api cycles.
    #  '' is for the worldwide trends
    trend_scraping_list = ['', 'United States', 'United Kingdom', 'Germany', 'Canada',
                           'Netherlands', 'Puerto Rico', 'Australia', 'Belgium', 'Malaysia', 'New Zealand', 'Singapore']
    #trend_scraping_list = ['Netherlands', 'Puerto Rico']
    test = False
    run_trendscrape(trend_scraping_list, test)



api_array = get_api_array()
ROOTDIR = os.path.dirname(os.path.realpath(__file__))
dir_sep = '/'


if __name__ == '__main__':
    from utils import log, log_return
    from trend_scraping import run_trendscrape
    from search_scraper import test as search_scrape_test
    log_return()
    log('starting application')

    #search_scrape_test(api_array[1])
    do_trendscrape()
    #pprint(api.trends_available())
    #pprint(api.trends_place(1))


    log("closing application")