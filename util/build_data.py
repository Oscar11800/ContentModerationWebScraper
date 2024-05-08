# import get_data
import pandas as pd
import json
import gzip


# INPUT:
#   row: a row from the links excel sheet (panda Series)
# OUTPUT:
#   a dictionary containing the raw html of each link in the row's platform
def build_obj(row, driver):
    # print(row)
    # print(type(row))
    # print(row[3:])
    raw = {'site_id': int(row[0]),
           'site_name': row[1],
           'site_url': row[2],
           'pages': driver.get_htmls(row[3:])}

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