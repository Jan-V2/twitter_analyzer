import csv
from pprint import pprint
import os
from my_utils.my_logging import log_message as log, log_return
from data_to_db import mysql_mariadb_blueprints as msql_q
import MySQLdb
from dateutil import parser as timestamp_parser
from my_utils.util_funcs import raise_custom_except as c_except
import _mysql_exceptions
from past.builtins import raw_input
from data_to_db.db_credentials import get_pi_db_cred
from my_utils.platfowm_vars import ROOTDIR, dir_sep
from multiprocess.pool import Pool


def init_db():
    config = get_pi_db_cred()
    db = MySQLdb.connect(**config)
    db.autocommit(False)
    db_cursor = db.cursor()
    return db_cursor, db

def get_typedict(tablename):
    types_dict = None
    if 'REGION' in tablename:
        types_dict = region_table_types
    elif 'COUNTRY' in tablename:
        types_dict = country_table_types
    elif tablename == 'GLOBAL_TABLE':
        types_dict = global_table_types
    else:
        c_except(ValueError, tablename + ' does not appear to be a valid table_name')
    return types_dict

def get_coldefs(header, types_dict):
    coldefs = []
    for colname in header:
        coldefs.append([colname, types_dict[colname]])
    return coldefs


def build_queries(header, data, tablename, delete_old):
    queries = []
    if delete_old:
        queries.append(['one', "DROP TABLE IF EXISTS " + tablename])


    queries.append(['one', msql_q.create_table_with_id(tablename,
                                               msql_q.create_coldefs(
                                                   get_coldefs(header, get_typedict(tablename))))])

    val_ins_string, names_string = unroll_header(header)
    queries.append(['many', "INSERT INTO " + tablename +" (" + names_string + ") VALUES (" + val_ins_string + ")", data])
    return queries

def cast_data(header, tablename, data):
    typedict = get_typedict(tablename)
    type_casters = []
    for i in range(len(header)):
        sql_type = typedict[header[i]]
        if sql_type == text_type:
            type_casters.append(lambda str: str.encode('UTF-8'))
            #type_casters.append(lambda passer: passer)
        elif sql_type == int_type:
            type_casters.append(int)
        elif sql_type == date_type:
            type_casters.append(timestamp_parser.parse)

    log('casting data for ' + str(len(data)) + " rows")
    def cast_line(dataln):
        cast_line = []
        for col_id in range(len(dataln)):
            cast_line.append(type_casters[col_id](dataln[col_id]))
        return cast_line

    tpool = Pool(processes=6)
    ret = tpool.map(cast_line, data)
    tpool.close()
    return ret

def unroll_header(header):
    val_ins_string = ""
    names_string = ""
    for i in range(len(header)):
        names_string += header[i]
        val_ins_string += '%s'
        if i < len(header) - 1:
            val_ins_string += ', '
            names_string += ', '
    return val_ins_string, names_string

def run_queries(queries):
    for line in queries:
        log('executeing: ' + line[1])
        if line[0] == 'one':
            db_cursor.execute(line[1])
        elif line[0] == 'many':
            db_cursor.executemany(line[1], line[2])
        else:
            log('could not execute query')
        log('Query ok')
    db.commit()


def run(is_test):
    for filename in os.listdir(tables_dir):
        if filename == 'COUNTRY_UNITED_STATES.csv' or not is_test:
            log('dumping data for ' + filename)
            with open(tables_dir + filename, 'r', encoding='UTF-8') as file:
                reader = csv.reader(file)
                data = []
                for row in reader:
                    data.append(row)

            header = data[0]
            data = data[1:]
            if is_test:
                data = data[:100]
            for i in range(len(header)):
                header[i] = header[i].replace(" ", "_")
            tablename = filename.replace(".csv", '').replace(" ", "_").replace('-', '_').replace('.', "")
            data = cast_data(header, tablename, data)
            q = build_queries(header, data, tablename, False)
            run_queries(q)


def start_cli():
    while True:
        try:
            db_cursor.execute(raw_input("Enter query "))
            r = db_cursor.fetchall()
            pprint(r)
            db.commit()
        except _mysql_exceptions.ProgrammingError as e:
            print(str(e))


tables_dir = ROOTDIR +dir_sep + 'csv_done' + dir_sep
# todo make slightly faster my having seperate query and preparing threads

int_type = "INT"
text_type = 'TINYTEXT'
date_type = 'DATETIME'

region_table_types = {'timestamp': date_type, 'search': text_type, 'tweet_volume': int_type, 'is_promoted_contend': text_type}
global_table_types = {'country_table': text_type}
country_table_types = {'region_table': text_type, 'woeid': int_type}


db_cursor, db = init_db()

if __name__ == '__main__':
    log_return()
    log('starting app')
    run(False)
    start_cli()