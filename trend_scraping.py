import multiprocessing
import os
import shutil
import time
import zipfile
from pprint import pprint
from zipfile import ZipFile
import threading
import simplejson
import tweepy
from twitter_api_keys import get_api_array
from main import ROOTDIR, dir_sep
from utils import count_active_threads, log, get_timestamp, get_subdir_list, handle_ratelimit
from twitter_api_keys import apis as getapi
import tarfile




# todo for some reason it doesn't download all the files.
# i think it's probably related to api cycling
# todo add some sort of code that spreads the load evenly  across several apis
def run_trendscrape(scraping_list, is_test):
    if is_test:
        scrapes_per_compress = 2
    else:
        scrapes_per_compress = 24

    trend_data_dir = dir_sep + 'scraped trends'# the subdir where scraped trenddata is stored
    try:
        uncompressed_scrapes = len(get_subdir_list(ROOTDIR + dir_sep + 'scraped trends'))
    except TypeError:
        uncompressed_scrapes = 0
    #compress_trend_data(trend_data_dir)

    dump_dir = ROOTDIR + trend_data_dir + dir_sep + get_timestamp()

    scrape_trends(dump_dir, scraping_list)
    uncompressed_scrapes += 1
    if uncompressed_scrapes % scrapes_per_compress == 0 and uncompressed_scrapes > 0:
        compress_trend_data(trend_data_dir, is_test)


def make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)


def compress_trend_data(trend_data_dir, is_test):
    log("compressing ")

    # gets a list of subdirs of the folder
    subdirs = get_subdir_list(ROOTDIR + dir_sep + trend_data_dir)

    # puts the number of dirs in the archive + timestamp in the filename
    arch_name = str(len(subdirs)) + " dirs " + get_timestamp()

    arch_folder = ROOTDIR + dir_sep + "compressed" + dir_sep
    if not os.path.exists(arch_folder):
        os.makedirs(arch_folder)

    arch_path = arch_folder + arch_name

    # combines all the dirs into a zip and then compresses it into a zip
    make_zipfile(arch_path, ROOTDIR + dir_sep + trend_data_dir + dir_sep)
    os.rename(arch_path, arch_path + '.zip')

    log("compressed dirs into " + arch_name)

    # todo verifies the archive? (maybe by uncompressing it)
	
    # deletes the old data folders
    if not is_test:
        for folder in subdirs:
            shutil.rmtree(ROOTDIR + dir_sep + trend_data_dir + dir_sep + folder)

    log("deleted old folders")


def get_thread_country_lists(max_threads, scraping_list):
    thread_country_lists = []
    ids_per_thread_list = []
    for i in range(max_threads):
        thread_country_lists.append([])
        ids_per_thread_list.append(0)

    ids_per_country = get_ids_per_country()

    for item in ids_per_country:
        if item[0] in scraping_list:
            shortest_list_idx = 0
            for j in range(len(thread_country_lists)):
                if ids_per_thread_list[j] < ids_per_thread_list[shortest_list_idx]:
                    shortest_list_idx = j
            thread_country_lists[shortest_list_idx].append(item[0])
            ids_per_thread_list[shortest_list_idx] += item[1]
    return thread_country_lists


def scrape_trends(trend_data_dump_dir, scraping_list):
    # the main scraping mehthod
    # this will scrape the country names that are given in the argument
    # the next scrape starts an hour after the last scrape started

    # todo this whole idea is stupid, is should just use the country balacing idea i had
    # what i was doing before
    # make it so that it gets a list of woeids and splits it among a bunch of scrape threads
    # first make the dir the woeid should go into then
    apis = get_api_array()
    threads = len(apis)

    country_lists_per_thread = get_thread_country_lists(threads, scraping_list)
    threadlist = []
    for i in range(threads):
        thread = threading.Thread(target=download_and_save_trends,
                                         args=(country_lists_per_thread[i], trend_data_dump_dir, i, apis[i]))
        log('launching scrapethead ' + str(i))
        threadlist.append(thread)
        thread.start()


    # joins scraping threads and sleeps this thread
    log('threadscraping joining threads')
    for t in threadlist:
        t.join()
    log("threads joined")
    log("trendscrape done")


def download_and_save_trends(country_names, dump_dir, thread_id, api):
    # passing in '' will save golbal trends
    thread_name = 'scrapethread '+ str(thread_id) + ': '

    log('fetching global trend list')
    available_trends = api.trends_available()
    # pprint(available_trends)

    for country_name in country_names:
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
                    local_trend_json = api.trends_place(item['woeid'])
                    local_trend_json = local_trend_json[0]

                    # dumps each areacode into a seperate json file
                    with open(country_dir + dir_sep + local_trend_json['locations'][0]['name'] + '.json', 'w') as outfile:
                        # you need to use simplejson to make it look nice
                        log(thread_name + 'dumping json for ' + local_trend_json['locations'][0]['name'])
                        simplejson.dump(local_trend_json, outfile, indent=4, sort_keys=True)

                except Exception as e:
                    log(str(e))
                    handle_ratelimit(thread_name)

                break
            time.sleep(1)
        log(thread_name + " scraped " + country_name)

    log(thread_name + " done")

api = get_api_array()[0]# for depricated methods

def get_country_list():
    trendlist = api.trends_available()
    #pprint(trendlist[0]['name'])

    country_name_list = []
    for item in trendlist:
        if item['country'] not in country_name_list:
            country_name_list.append(item['country'])
    return country_name_list

def get_ids_per_country():
    country_list = get_country_list()
    available_trends = api.trends_available()
    country_trendid_no = []

    for country in country_list:
        country_trendid_no.append(trendids_per_country(country, available_trends))

    country_trendid_no = sorted(country_trendid_no, key=lambda country: country[1], reverse=True)
    return country_trendid_no


# depricated

def trendids_per_country(country_name, available_trends):
    country_trend_ids = []
    for item in available_trends:
        if item['country'] == country_name:
            country_trend_ids.append(item)

    return [country_name ,len(country_trend_ids)]


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