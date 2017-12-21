from pprint import pprint
import os
import json
import pycountry
from my_logging import log_message as log, log_return
from platfowm_vars import ROOTDIR, dir_sep
from utils import get_subdir_list, get_only_files_in_dir
from csv_obj import Csv_Obj

# it's all contained in one database.
# however it is spread out across many tables
# the first table is the main table. in contains the names of all the country tables.
# the country tables contain the names of all the region table + some metadata like woeid
# the region tables contain the actual trenddata.
# the region tables have the following collums
# timestamp, name(the utf-8 version of search), query (can be appended to twitter url),  bool promoted content, tweet volume (0 if under 10000)


def get_files(datadir):
    # there is probalbly a build in function for doing this.
    # or at the very least a more functional way or using recursion of something
    # todo make more efficient in terms of ram by only loading filepaths in this method and loading the json files when needed.
    log('getting files')
    json_files = []

    i = 1
    for observ_dir in  get_subdir_list(datadir):
        observ = []
        for country_dir in get_subdir_list(datadir + observ_dir):
            country_dir_list = []
            country_dir_list.append(country_dir)# each item will have the name of the country als the first index
            for region_file in os.listdir(datadir + observ_dir + dir_sep + country_dir):
                file_path = datadir + observ_dir + dir_sep + country_dir + dir_sep + region_file
                country_dir_list.append([region_file.replace(".json", ''), file_path])
            observ.append(country_dir_list)
        json_files.append(observ)
        if i % 20 == 0:
            log('got observation ' + str(i) + " out of " + str(len(get_subdir_list(datadir))))
        i += 1
        # if i % 100 == 0:
        #     break

    return json_files


# noinspection PyMethodMayBeStatic
class Csvs_Twitter_Trend_Data:

    def get_idx_0(self, x):
        return x[0]
    def get_woeid_from_json(self, path):
        return self.get_json(path)['locations'][0]['woeid']
    def get_new_country_abrv(self, country_name):
        if country_name == 'Worldwide':
            return 'WRLD'
        else:
            return pycountry.countries.get(name=country_name).alpha_3
    def get_region_table_name(self, region_name, country_abrv):
        return 'REGION_' + country_abrv + '_' + region_name.upper()
    def get_country_table_name(self, x):
        return 'COUNTRY_' + x.upper()
    def get_saved_country_abrv(self, country_name):
        return self.country_abr_list[list(map(self.get_idx_0, self.country_abr_list)).index(country_name)][1]
    def get_json(self, path):
        return json.load(open(path))

    country_abr_list = []


    def __init__(self,json_files):
        log('creating csvs')
        # global csv
        global_csv = Csv_Obj(header=['country table'])

        country_header = ['region table', 'woeid']
        region_header = ['timestamp', 'search', 'tweet volume', 'is promoted content']
        country_csvs = []
        region_csvs = []

        j = 1
        for observation in json_files:
            if j % 20 == 0:
                print(j)
            if j % 4 == 0: # checks every 4 observations, not i deal but realisically is should be fine
                for country in observation:
                    if country[0] not in map(self.get_idx_0, self.country_abr_list):
                        self.country_abr_list.append((country[0], self.get_new_country_abrv(country[0])))
                    country_abrv = self.get_saved_country_abrv(country[0])
                    if not country[0] in map(self.get_idx_0, country_csvs):
                        country_csvs.append((country[0], Csv_Obj(country_header)))
                    for region in country[1:]:
                        region_in_list = False
                        for csv in region_csvs:
                            if csv[0] == self.get_region_table_name(region[0], country_abrv):
                                region_in_list = True
                                break
                        if not region_in_list:
                            region_csvs.append((self.get_region_table_name(region[0], country_abrv), Csv_Obj(region_header)))
            j += 1


        self.global_csv = global_csv
        self.country_csvs = tuple(country_csvs)
        self.region_csvs = tuple(region_csvs)

    def create_global_and_country_tables(self, json_files):
        log('building global+country tables')
        global_table_list = []
        country_table_list = []
        i = 0
        for observation in json_files:
            if i % 20 == 0 and i != 0:
                print(i)
            i += 1
            for country in observation:
                country_abrv = self.get_saved_country_abrv(country[0])
                if self.get_country_table_name(country[0]) not in map(self.get_idx_0, global_table_list):
                    global_table_list.append([self.get_country_table_name(country[0])])
                for region in country[1:]:
                    if self.get_region_table_name(region[0], country_abrv) not in map(self.get_idx_0, map(self.get_idx_0, country_table_list)):
                        country_table_list.append([[self.get_region_table_name(region[0], country_abrv), self.get_woeid_from_json(region[1])], country[0]])

        for item in country_table_list:
            # gets the index of the country name at idx 1 and appends the data at idx 0
            country_names = list(map(self.get_idx_0, self.country_csvs))
            self.country_csvs[country_names.index(item[1])][1].data.append(item[0])

        self.global_csv.data = global_table_list

    def create_region_tables(self, json_files):
        log('building region tables')
        i = 1
        for observation in json_files:
            if i % 20 == 0:
                print(i)
            i += 1
            for country in observation:
                country_abrv = self.get_saved_country_abrv(country[0])
                for region in country[1:]:# first index is name of the country
                    # gets the index of the redion name at idx 1 and appends the data at idx 0
                    region_names = list(map(self.get_idx_0, self.region_csvs))
                    datarows = self.__get_trend_datarows(region[1])
                    for row in datarows:
                        self.region_csvs[region_names.index(
                            self.get_region_table_name(region[0], country_abrv))][1].data.append(row)

    def __get_trend_datarows(self, json_path):
        json_file = self.get_json(json_path)
        datarows = []
        trends = json_file['trends']
        timestamp = json_file['created_at']
        for trend in trends:
            search = trend['name']
            if trend['tweet_volume'] is None:
                tweet_volume = 0
            else:
                tweet_volume = trend['tweet_volume']
            is_promoted_content = str(trend['promoted_content'])
            datarows.append([timestamp, search, tweet_volume, is_promoted_content])
        return datarows

    def dump_csvs(self, csvdir):
        # deletes all file before dumping in new information
        log('clearing csvdir')
        for file in get_only_files_in_dir(csvdir):
            os.remove(csvdir + dir_sep + file)

        log('dumping csvs')
        self.global_csv.save_to_path(csvdir, 'GLOBAL_TABLE')

        for csv in self.country_csvs:
            csv[1].save_to_path(csvdir, self.get_country_table_name(csv[0]))

        for csv in self.region_csvs:
            csv[1].save_to_path(csvdir, csv[0])

def run(datadir, csvdir):
    log_return()
    log('starting app')
    json_files = get_files(datadir)
    csvs = Csvs_Twitter_Trend_Data(json_files)
    csvs.create_global_and_country_tables(json_files)
    csvs.create_region_tables(json_files)
    csvs.dump_csvs(csvdir)


    log('done')
    log_return()



# i'll have a country table with references to tables for the individual counties
# those tables will have info on their different region tables
# those region tables will contain the actual trenddata



if __name__ == '__main__':
    #datadir = ROOTDIR + dir_sep + 'data' + dir_sep
    datadir = 'H:\\data\\twitter trend data\\'
    csvdir = ROOTDIR + dir_sep + 'data' + dir_sep + 'csv_output' + dir_sep
    run(datadir, csvdir)
