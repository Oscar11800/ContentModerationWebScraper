# import get_data
import pandas as pd
import json
import gzip


# INPUT:
#   row: a row from the links excel sheet (panda Series)
# OUTPUT:
#   a dictionary containing the raw html of each link in the row's platform
def build_obj(row, driver):
    raw = {
        'site_id': row[0],  # 'reddit'
        'site_name': row[1],  # 'reddit.com'
        'site_url': row[2],  # full URL
        'pages': driver.get_htmls(row[3:])  # list of URLs
    }
    return raw


def build_file(data, filename):
    with open(filename, 'a+') as fh:
        json.dump(data, fh)
        fh.write('\n')


def zip_file(filename):
    f_in = open(filename)
    f_out = gzip.open(filename + '.gz', 'wt')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()