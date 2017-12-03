# to
# i can webscrape it without having to render it
# i just have to fish out the
# <div class="js-tweet-text-container"> </div>
# objects

# stages
# 1 download a searchpage every 4 seconds
# extract the tweet objects from the page into an array
# create a coherent timeline (elimiate doubles)
# save to disk in some format

import tweepy
import queue
import datetime
import pprint
import time
import multiprocessing
import threading
from main import ROOTDIR, dir_sep as dirsep
from utils import handle_ratelimit, escape_string, log
import csv



raw_tweet_queue = queue.Queue()
downloader_done = False


# TODO make it so that you download a set number of tweets rather
# TODO than a daterange cuz twitter just doesn't want me to have nice thing

def test(api):
    search_term = '@ISPuuuv'
    #search_term = '@Potus'
    dump_dir = ROOTDIR + dirsep + search_term + dirsep
    today = datetime.date.today()
    start_date = today.replace(month=today.month-1)
    end_date = start_date.replace(day=start_date.day +1)


    dlr = Tweet_Downloader()
    writer = Tweets_To_Csv()


    dl_process = threading.Thread(target=dlr.daterange_scrape, args=(api, search_term, start_date, end_date))
    dl_process.start()
    # join ends the thread once it's finished
    dl_process.join()

    writer_process = threading.Thread(target=writer.run, args=(dump_dir, search_term, start_date))
    writer_process.start()
    writer_process.join()


class Tweet_Downloader:
    def daterange_scrape(self, api, search_term, date_start, date_end):
        # the date arguments must be datetime.date objects
        log("starting datrange scrape")

        results = []
        since_id_search_term = self.__date_to_search_term(date_start, date_end, search_term)
        print(api.search(since_id_search_term))
        # this gets the since_id associated with the search term
        while not len(results) > 0:
            log("getting results")
            try:
                for page in tweepy.Cursor(api.search, q=since_id_search_term).pages():
                    results = page
                    print(page[0].created_at)
                    #break
            except Exception as e:
                log(str(e))
                handle_ratelimit("since id getter")

        since_id = results[0].id

        self.__download_tweets(api, search_term, since_id, date_end)


    def __date_to_search_term(self, date_start, date_end, search_term):
        # searchterm since:2017-09-18 until:2017-09-19
        # this string used as searchterm will search the daterange specified
        return str(search_term + " since:" + str(date_start) + " until:" + str(date_end))

    def __tweets_to_queue(self, tweets):
        # if in con't place the items in the queue it waits instead of throwing an exept (apparently)
        for tweet in tweets:
            global raw_tweet_queue
            raw_tweet_queue.put(tweet)


    def __check_stream_end(self, results, stream_end):
        # stream_end is a datetime.datetime object of where the stream ends.
        #stream_end = datetime(stream_end.year, stream_end.month, stream_end.day)

        if results[0].created_at > datetime.datetime(stream_end.year, stream_end.month, stream_end.day):
            return True
        return False


    def __truncate_stream_end(self, page, stream_end_date):
        # cuts of the tweets that fall outside of the time range
        return page#TODO

    def __download_tweets(self, api, search_term, since_id, stream_end_date):

        end_of_stream = False
        i = 1
        while not end_of_stream:
            print("trying page download")
            try:
                for page in tweepy.Cursor(api.search, q=search_term, since_id=since_id).pages():
                    print("downloaded page")
                    # page is a list of statuses

                    if self.__check_stream_end(page, stream_end_date):
                        end_of_stream = True

                        page = self.__truncate_stream_end(page, stream_end_date)
                        self.__tweets_to_queue(page)  # adds truncated page onto queue before exiting
                        break  # breaks out of try exept loop
                        # if break is not here it will continue until it hits the rate limit

                    #if i % 5 == 0:
                    log("got page " + str(i))
                    i += 1

                    self.__tweets_to_queue(page)

            except Exception as e:
                log(str(e))
                handle_ratelimit("dler")
        global downloader_done
        downloader_done = True



# methods for saving tweet data to a csv file
class Tweets_To_Csv:
    def run(self, dump_dir, searchterm, date):
        filename = searchterm + " " + str(date) + ".csv"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["posted_at", "tweet_id", "in_reply_to_tweet_id", "in_reply_to_user_id", "user_id",
                          "user_name", "user_screen_name", "user_verified", "tweet_text", "retweets_no", "likes",
                          "application_used", "user_location", "coordinates", "user_timezone",
                          "follower_count", "following_count", "user_likes_no", "lang", "user_created"]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            # while not downloader_done:
            i = 1

            while True:
                q = raw_tweet_queue
                if q.empty():
                    log("waiting 3 seconds for tweets to download")
                    time.sleep(3)
                else:
                    self.__mask_and_write(q.get(), writer)
                    if i % 30 == 0:
                        log(str(i) + " tweets encoded")
                    i+=1

                if q.empty() and downloader_done:
                    break



    def __mask_and_write(self, tweet, writer):
        posted_at = str(tweet.created_at)  # have to cast cause it's a datetime object
        tweet_id = tweet.id_str
        in_reply_to_tweet_id = tweet.in_reply_to_status_id_str
        in_reply_to_user_id = tweet.in_reply_to_user_id_str
        user_id = tweet.user.id_str
        user_name = tweet.user.name
        user_screen_name = tweet.user.screen_name
        user_verified = 0
        if tweet.user.verified:  # this is to save space
            user_verified = 1
        tweet_text = tweet.text
        tweet_text = escape_string(tweet_text)
        # replies_no = tweet.? #don't think it's in here
        retweets_no = tweet.retweet_count
        likes = tweet.favorite_count
        application_used = tweet.source_url
        # possibly_sensitive = 0
        # if tweet.retweeted_status.possibly_sensitive:
        #    possibly_sensitive = 1
        user_location = tweet.user.location
        coordinates = tweet.coordinates
        user_timezone = tweet.user.time_zone
        follower_count = tweet.user.followers_count
        following_count = tweet.user.friends_count
        user_likes_no = tweet.user.favourites_count
        lang = tweet.lang
        user_created = str(tweet.user.created_at)  # have to cast cause it's a datetime object

        writer.writerow({"posted_at": posted_at, "tweet_id": tweet_id, "in_reply_to_tweet_id": in_reply_to_tweet_id,
                     "in_reply_to_user_id": in_reply_to_user_id, "user_id": user_id, "user_name": user_name,
                     "user_screen_name": user_screen_name, "user_verified": user_verified, "tweet_text": tweet_text,
                     "retweets_no": retweets_no, "likes": likes, "application_used": application_used, "user_location":
                         user_location, "coordinates": coordinates, "user_timezone": user_timezone, "follower_count":
                         follower_count, "following_count": following_count, "user_likes_no": user_likes_no, "lang": lang,
                     "user_created": user_created})




