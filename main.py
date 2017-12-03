import os


#todo make data and code differnt dirs so only the code syncs to github
from pprint import pprint


def do_trendscrape():
    from trend_scraping import run_trendscrape
    # this list is just under 150 trends, so it can be downloaded in 2 15 min api cycles.
    #  '' is for the worldwide trends
    trend_scraping_list = ['', 'United States', 'United Kingdom', 'Germany', 'Canada',
                           'Netherlands', 'Puerto Rico', 'Australia', 'Belgium', 'Malaysia', 'New Zealand', 'Singapore']
    #trend_scraping_list = ['Netherlands', 'Puerto Rico']
    test = False
    run_trendscrape(trend_scraping_list, test)

def init_platform_vars():
    from sys import platform as _platform
    global dir_sep
    if _platform == "linux" or _platform == "linux2":
        # linux
        dir_sep = '/'
    # elif _platform == "darwin":
    #     # MAC OS X
    #     pass
    elif _platform == "win32":
        # Windows
        dir_sep = "\\"
    elif _platform == "win64":
        # Windows 64-bit
        dir_sep = "\\"
    else:
        raise OSError("OS not detected")

ROOTDIR = os.path.dirname(os.path.realpath(__file__))
dir_sep = ''
init_platform_vars()

if __name__ == '__main__':
    from utils import log, log_return
    #from trend_scraping import run_trendscrape
    from search_scraper import test as search_scrape_test
    log_return()
    log('starting application')
    do_trendscrape()
    #from trend_scraping import get_thread_country_lists
    #pprint(get_thread_country_lists(3, ['', 'United States', 'United Kingdom', 'Germany', 'Canada',
    #                                    'Netherlands', 'Puerto Rico', 'Australia', 'Belgium', 'Malaysia', 'New Zealand', 'Singapore']))



    #pprint(api_array[0].trends_available())

    #search_scrape_test(api_array[1])
    #do_trendscrape()
    #pprint(api.trends_available())
    #pprint(api.trends_place(1))


    log("closing application")