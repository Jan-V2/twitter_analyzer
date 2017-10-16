from random import randrange

import tweepy
import time

def get_roborake_api():
    consumer_key = "5tbwUZzmqPxZsJWB5pyOfRBQ3"
    consumer_secret = "gWG64nIK1EW84mcXzekmiXZ2pIX3lf8dTMQwqrBkmCTNKyrusv"

    access_token = "907747149923975169-WWek2FSWtpI6ZlfGumhwelrxC3BOv6e"
    access_token_secret = "lpmveZkc4c8c25l7eEkyV3ETY9DKN69Lx8iGvlRz5UeZU"

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    return api

def get_scraper_0_api():
    consumer_key = "uhkhzx10jry4XqGlfFoN5ib47"
    consumer_secret = "h6IyP7V0YOXM5KfnBssVpBd5V4DFXXho5VNLAHcMAQ6F0UAVyo"

    access_token = "907747149923975169-04wXlYBVVNXJXojf2esq3IPB0dfCALn"
    access_token_secret = "ElVAIyJuvKRJH3mHLoiZrRtGOa7pYcFTADwe2F7Kiz5pZ"

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    return api

def get_scraper_1_api():
    consumer_key = "SUFsADVTg65OPYWijhi8kwsB1"
    consumer_secret = "ass9jcFNY4s7fihMOq70jwuYl86xXFauLtbHdNmwUE9QxU5XVZ"

    access_token =  "907747149923975169-BIHqdwEzcSRjNSTMXUv2yYhe1dv2BWL"
    access_token_secret = "GvqgyCOIFtC2H25bQf5h95YvCtYQpFw4vERSwg8cZ4Mxz"

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    return api

def get_scraper_2_api():
    consumer_key = "gGXjWJrrnyCP1HTx6CbgknLEC"
    consumer_secret = "OIpF4AxBEZIRGHKbM1YnGF6s8K7KDKBTHpJYnqdX1SmByH0srB"

    access_token = "907747149923975169-GvqNYmUYJ1z9puqK7Z2fVmoYHRxtfih"
    access_token_secret = "Tvk0cEkfzktPS3OoO62xINVTCzzKFer3LSR2kMGboETAl"

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    return api

def get_api_array():
    api_list = [get_roborake_api(), get_scraper_0_api(),
               get_scraper_1_api(), get_scraper_2_api()]
    return api_list

class apis():
    def __init__(self, theadname):
        self.api_array = get_api_array()
        self.current_index  = 0
        self.thread_name = theadname

    def get_api(self):
        return self.api_array[self.current_index]

    def cycle_and_wait(self, exeption):
        from utils import log

        # extra secs are so that the threads,
        # don't all wake at the same time and go over ratelimit per sec
        extra_secs = randrange(10)
        log(str(exeption))
        log(self.thread_name + "cycling api and sleeping " + str(7+extra_secs) + " secs")
        time.sleep(7 + extra_secs)
        if self.current_index < len(self.api_array) -1:
            self.current_index +=1
        else:
            self.current_index = 0