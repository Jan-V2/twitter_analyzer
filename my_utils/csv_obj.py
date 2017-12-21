from collections import defaultdict
from utils.my_logging import log_message, log_exept

class Csv:
    # todo add collum methode
    # todo make this gud

    def __init__(self, header=None, data_array=None):
        if header is None:
            if data_array is None:
                log_exept('either the header data argument needs to contain data. they can\'t both be None')
                raise TypeError
            else:
                if type(data_array) is not list:
                    log_exept('data must be list type')
                    raise TypeError
        else:
            if type(header) is not list:
                log_exept('header must be list type')
                raise TypeError
            if type(data_array) is not list or type(None):
                log_exept('data must be list type')
                raise TypeError

        if header is None:
            self.header = None
        else:
            self.header = defaultdict(str)
            for i in range(len(header)):
                self.header[header[i]] = i

        if data_array is None:
            self.data = []
        else:
            self.data = data_array

    def get_header_list(self):
        return self.header.keys()# todo does this work?

    def add_row_primitive(self, row):
        # todo make it so you can use col keys like in a database
        # this just adds a row to the data array
        self.data.append(row)

    def save_to_path(self, path):
        