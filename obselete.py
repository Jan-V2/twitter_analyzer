def get_local_trends(country_name):

    available_trends = api.trends_available()
    # pprint(available_trends)

    country_trend_ids = []
    country_trend_array = []

    for item in available_trends:
        if item['country'] == country_name:
            country_trend_ids.append(item)

    for item in country_trend_ids:
        # pprint(item)
        raw_json = api.trends_place(item['woeid'])
        raw_json = raw_json[0]
        country_trend_array.append([raw_json['locations'], raw_json['trends']])
        pprint(raw_json)
        log_return()

# the rest ai doesn't work properly and has prohibitive ratelimints
# i'll try implementing the stream api instead
class search_downloader():
    # could kind of parrallize this by getting the sinceid
    # range over the day and dividing it by the number of threads
    def start(self, api, date, search_term):
        # seaches a spesific
        end_stream = date.replace(day=date.day+1)
        results = self.__first_search(api, date, search_term)
        self.__tweets_to_queue(results)

        stream_end_timestamp = date.replace(day=+1)

        since_id = 0
        end_of_stream = False
        while not end_of_stream:
            last_id = since_id
            since_id = self.__get_since_id(results, since_id)
            print(len(results))
            assert since_id != 0

            if since_id > last_id:
                print("right")
            elif since_id == last_id:
                print("same")
                print("sleeping 3 seconds")
                time.sleep(3)
            else:
                print("wrong")

            try:
                results = api.search(search_term, since_id=since_id)
            except:
                handle_ratelimit("downloader")
            #end_of_stream = self.__end_of_stream(results, stream_end_timestamp)
            # cuts of the tweets that fall outside of the time range
            #if end_of_stream:
            #    results = self.__truncate_stream_end(results)

            # adds the results to the processing queue
            #self.__tweets_to_queue(results)
            self.__tweets_to_queue(results)
            if raw_tweet_queue.unfinished_tasks > 70:
                end_of_stream = True



    def __first_search(self, api, date, search_term):
        # gets the last id
        results = []
        search_term = self.__date_to_search_term(date, search_term)
        while not len(results) > 0:
            try:
                results = api.search(search_term)
            except:
                handle_ratelimit("first search downloader")
        self.__tweets_to_queue(results)
        return results


    def __get_since_id(self, results, since_id):
        if len(results)> 0:
            since_id = results[0].id
        return since_id


    def __tweets_to_queue(self, tweets):
        for tweet in tweets:
            raw_tweet_queue.put(tweet)


    def __tweets_to_test_list(self, results):
        if len(results)>0:
            test_tweet_list.append(results[0])
        else:
            print('results empty')


    def __date_to_search_term(self, date, search_term):
        # searchterm since:2017-09-18 until:2017-09-19
        # this string used as searchterm will search the daterange specified
        return str(search_term + " since:" + str(date.replace(day=date.day-1)) + " until:" + str(date))


    def __end_of_stream(self, results, stream_end):
        # stream_end is a datetime object of where the stream ends.
        if results[0].created_at.date() > stream_end:
            return True
        return False


    def __truncate_stream_end_results(self):
        # cuts of the tweets that fall outside of the time range
        pass

#version 2 scrapped because twitter doesn't want datescraping to work
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
