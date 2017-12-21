import datetime
import time
import os
import tweepy

from main import ROOTDIR, dir_sep
from twitter_api_keys import get_api_array

api_array = get_api_array()


def limit_handler(cursor):
    log("handiling rate limit")
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            handle_ratelimit()
        break

def get_subdir_list(dir):
    # gets the names for all the subdirs one layer deep
    # (so only the dirs in the rootdir)
    for root, dirs, files in os.walk(dir, topdown=True):
        return dirs

def handle_ratelimit(thread_name):
    # only seems to work once you have hit the limit
    limit_status = api_array[0].rate_limit_status()

    #pprint(limit_status)

    unixtime_reset = limit_status['resources']['trends']['/trends/available']['reset']
    current_unixtime = int(time.time())
    time_till_reset = unixtime_reset - current_unixtime

    log(thread_name + 'handiling ratlimit, waitng ' + str(time_till_reset) + " seconds")
    time.sleep(time_till_reset + 2)


def count_active_threads(thread_list):
    active_threads = 0
    for thread in thread_list:
        if thread.is_alive():
            active_threads +=1
        else:
            thread.terminate()
    return active_threads


def log(logline):
    timestamp = get_timestamp()
    logline = timestamp + " " + logline
    print(logline)
    with open(ROOTDIR + dir_sep + "log.txt",mode='a') as logfile:
        logfile.write(logline + '\n')


def log_return():# puts an empty line in the logfile
    print()
    with open(ROOTDIR + '\\' + "log.txt",mode='a') as logfile:
        logfile.write('\n')


def get_timestamp():
    return '[{:%Y-%m-%d_%H-%M-%S}]'.format(datetime.datetime.now())


def escape_string(string):
    escaped = string.translate(str.maketrans({"-":  r"\-",
                                       "]":  r"\]",
                                       "\\": r"\\",
                                       "^":  r"\^",
                                       "$":  r"\$",
                                       "*":  r"\*",
                                       ".":  r"\.",
                                       ",":  r"\,",
                                       "\n": r"\\n"}))
    return escaped