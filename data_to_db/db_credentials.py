

utf8er = lambda b_str: b_str.decode('UTF-8')



def get_pi_db_cred():
    config = {
        'user': 'tester',
        'passwd': 'mynamesql',
        'host': '192.168.178.178',
        'db': 'twitter_data',
        'use_unicode': True
    }
    return config