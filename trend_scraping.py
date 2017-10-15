import multiprocessing
import os
import time
from pprint import pprint

import simplejson
import tweepy

from main import api_array, ROOTDIR, dir_sep
from utils import count_active_threads, log, get_timestamp, get_subdir_list
from twitter_api_keys import apis as getapi
import tarfile




# todo implement automatic compression of files
def run_trendscrape(scraping_list, test):
    wait_in_secs = 0
    iters_per_compress = 0
    trend_data_dir = ROOTDIR + dir_sep + 'scraped trends'# the dir where scraped trenddata is stored
    if test:
        wait_in_secs = 15
        iters_per_compress = 2
    else:
        wait_in_secs = 3600
        iters_per_compress = 24

    iters = 0
    while True:
        # has to be refreshed every ineration otherwise it overwrites itself
        dump_dir = trend_data_dir + dir_sep + get_timestamp()

        trendscrapingloop(dump_dir, scraping_list, wait_in_secs)
        iters +=1
        #if iters % iters_per_compress == 0:
        #his    compress_trend_data(trend_data_dir)


def compress_trend_data(trend_data_dir):
    # todo
    # gets a list of subdirs of the folder
    subdirs = get_subdir_list(trend_data_dir)

    # puts the number of dirs in the archive + timestamp in the filename
    arch_name = str(len(subdirs)) + " dirs " + get_timestamp() + ".tar.gz"

    # combines all the dirs into a tar and then compresses it into a tar.gz
    arch = tarfile.open( arch_name, "w:gz")
    for dir in subdirs:
        arch.add(trend_data_dir + dir_sep + dir)
    arch.close()

    # verifies the archive? (maybe by uncompressing it)
    # deletes the old data folders
    pass


def trendscrapingloop(trend_data_dump_dir, scraping_list, wait_in_secs):
    # the main scraping mehthod
    # this will scrape the country names that are given in the argument
        # the next scrape starts an hour after the last scrape started
        nextscrape = int(time.time()) + wait_in_secs
        max_theads = 5

        threadlist = []
        for country in scraping_list:
            active_threads = count_active_threads(threadlist)
            thread = multiprocessing.Process(target=download_and_save_trends,
                                             args=(country, trend_data_dump_dir, active_threads))
            # launches the scraping threads
            while True:
                if active_threads < max_theads:
                    log('launching scrapethead ' + str(active_threads))
                    threadlist.append(thread)
                    thread.start()
                    break
                else:
                    time.sleep(2)
                    active_threads = count_active_threads(threadlist)

        # joins scraping threads and sleeps this thread
        log('threadscraping joining threads')
        for t in threadlist:
            t.join()
        log("threads joined")
        sleeptime = nextscrape - int(time.time())
        log('sleeping for ' + str(sleeptime) + ' seconds until next trendscrape')
        time.sleep(sleeptime)


def download_and_save_trends(country_name, dump_dir, thread_id):
    # passing in '' will save golbal trends

    thread_name = 'scrapethread '+ str(thread_id) + ': '
    log('fetching global trend list')
    available_trends = api.trends_available()
    # pprint(available_trends)

    apis = getapi(thread_name)

    country_trend_ids = []

    for item in available_trends:
        if item['country'] == country_name:
            country_trend_ids.append(item)

    if country_name != '':
        # creates a country directory if it doesn't already exist
        country_dir = dump_dir + dir_sep + country_name
        if not os.path.exists(country_dir):
            os.makedirs(country_dir)
        log(thread_name + 'fetching local trends for ' + country_name)
    else:
        country_dir = dump_dir + dir_sep + 'Worldwide'
        if not os.path.exists(country_dir):
            os.makedirs(country_dir)
        log(thread_name + 'fetching local trends for Worldwide')

    # dumps each areacode into a seperate json file
    for item in country_trend_ids:
        # pprint(item)
        while True:
            try:
                # fetches data for each area code
                local_trend_json = apis.get_api().trends_place(item['woeid'])
                local_trend_json = local_trend_json[0]

                # dumps each areacode into a seperate json file
                with open(country_dir + dir_sep + local_trend_json['locations'][0]['name'] + '.json', 'w') as outfile:
                    # you need to use simplejson to make it look nice
                    log(thread_name + 'dumping json for ' + local_trend_json['locations'][0]['name'])
                    simplejson.dump(local_trend_json, outfile, indent=4, sort_keys=True)

            except tweepy.RateLimitError:
                apis.cycle_and_wait()

            break
    log(thread_name + "done")


# depricated
api = api_array[0]# for depricated methods
def print_ids_per_country():
    country_list = get_country_list()
    available_trends = api.trends_available()
    country_trendid_no = []

    for country in country_list:
        country_trendid_no.append(trendids_per_country(country, available_trends))

    country_trendid_no = sorted(country_trendid_no, key=lambda country: country[1], reverse=True)
    pprint(country_trendid_no)

def trendids_per_country(country_name, available_trends):
    country_trend_ids = []
    for item in available_trends:
        if item['country'] == country_name:
            country_trend_ids.append(item)

    return [country_name ,len(country_trend_ids)]

def get_country_list():
    trendlist = api.trends_available()
    #pprint(trendlist[0]['name'])

    country_name_list = []
    for item in trendlist:
        if item['country'] not in country_name_list:
            country_name_list.append(item['country'])
    return country_name_list

def get_highest_tending(trends_json):
    # takes json objects produced by the api.trends_place or api.trends_closest
    # and determines which hashtag has the highest volume
    # if tweetvolume is None it's ignored
    highest_tweet_volume = 0
    highest_trending = object

    for items in trends_json['trends']:
        # pprint(items)
        if items['tweet_volume'] != None:
            if (items['tweet_volume'] > highest_tweet_volume):
                highest_tweet_volume = items['tweet_volume']
                highest_trending = items

    pprint("the highest trading hashtag = " + highest_trending['name'])
    pprint("url = " + highest_trending['url'])
    pprint("tweetvolume = " + str(highest_trending['tweet_volume']))