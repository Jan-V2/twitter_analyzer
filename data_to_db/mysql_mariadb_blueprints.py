from my_utils.util_funcs import raise_custom_except as c_except



create_table_with_id = lambda tablename, coldefs, if_not_exists: 'CREATE TABLE ' + add_if_not_exist(if_not_exists) + tablename + '(Id INT PRIMARY KEY AUTO_INCREMENT, ' + coldefs + ')'

def add_if_not_exist(add):
    if add:
        return ' IF NOT EXISTS '
    else:
        return ''

def create_coldefs(col_plus_type):
    if type(col_plus_type) != list:
        c_except(TypeError, 'col_plus_type must be of type list')

    ret = ''
    for i in range(len(col_plus_type)):
        ret += str(col_plus_type[i][0]) + ' ' + str(col_plus_type[i][1])
        if i < len(col_plus_type) -1:
            ret += ', '
    return ret


class Data_Type:

    def __init__(self, type_with_size):
        if type(type_with_size) != str:
            c_except(TypeError, 'type_with_size must be a string')
        # todo add floating point support
        types = (
            'STRING'
            'INT'
            'FLOAT'
            'DATETIME'
            'DATETIME_T'
            'TIME'
        )
        for type in types:
            input_type = type_with_size[:len(type)-1]
            if input_type == type:
                if input_type == 'STRING':
                    size = self.__get_size(type_with_size, type)
                    if size is not None:
                        # todo this whore variable size thing seems dumb.
                        # maybe refactor it to just 4 types
                        if size < 256:
                            self.mysql = 'VARCHAR' + self.__in_braces(size)
                        elif size < 65536:
                            self.mysql = 'TEXT'
                        elif size < 16777216:
                            self.mysql = 'MEDIUMTEXT'
                        else:
                            self.mysql = 'LONGTEXT'
                    else:
                        self.mysql = 'TEXT'

                elif input_type == 'INT':
                    size = self.__get_size(type_with_size, type)
                    if size is not None:
                        self.mysql = 'placeholder' # todo
                elif input_type == 'FLOAT':
                    self.__no_type_exept(type)
                elif input_type == 'DATETIME':
                    self.__no_type_exept(type)
                elif input_type == 'DATETIME_T':
                    self.__no_type_exept(type)
                elif input_type == 'TIME':
                    size = self.__get_size(type_with_size, type)
                else:
                    self.__no_type_exept(type)

    def __in_braces(self, str):
        return '(' + str + ')'

    def __no_type_exept(self, type):
        c_except(ValueError, type + ' type not implemented')

    def __get_size(self, type_with_size, type):
        pass
        #todo

