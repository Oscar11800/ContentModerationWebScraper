'''
Script to fill in HTMLs for scrapes that failed during the main pipeline

Argument parser throws errors if required directories/files don't exist. 
'''

import os
from json import load, dumps
from random import shuffle
from get_data import *
from time import time
from find_empties import find_empties
from argparsers import fill_parser as parser, ArgumentError

def fill(site: str, area: str, pid: int, source: str, driver) -> None:
    '''
    Fill HTML for one page. 
    Prints log messages. 

    Args:
        site: page site (ie instagram)
        area: search area (ie copyright)
        pid: page id
        source: page source link
        driver: Selenium driver
    '''

    prefix = area + '_' + site
    filename = next(path for path in os.listdir() if path.startswith(prefix))

    with open(filename, 'r') as f:
        htmls = load(f)

    page = htmls['pages'][pid]

    old_len = len(page['html'])

    source = source[source.rindex('http'):]

    new_html = get_html(source, driver, 0)

    if old_len > len(new_html): return

    page['html'] = new_html
    page['url'] = source

    with open(filename, 'w') as f:
        f.write(dumps(htmls))
        
    print(area)
    print(site)
    print(pid)
    print(source)
    print(f"{old_len} > {len(new_html)}")
    print()

def fill_dir(empties: list, htmls_path: str) -> None:
    '''
    Run fill() on an entire directory of HTMLs. 
    Prints log messages. 

    Args:
        empties: list of empty scrapes
        htmls_path: path to directory containing HTMls
    '''

    start_time = time()
    old_dir = os.getcwd()
    os.chdir(htmls_path)

    driver = setup_driver()

    i = 0  # ✅ Initialize i before the loop

    for i, (site, area, pid, source) in enumerate(empties):
        print(i)
        try:
            fill(site, area, pid, source, driver)
        except Exception as error:
            print(error, '\n')

    print(f'Done. {i} pages filled. {time() - start_time} elapsed')  # ✅ Now i is always defined

    os.chdir(old_dir)

if __name__ == '__main__':
    args = parser.parse_args()

    passages_path = os.path.join(args.datadir, 'passages')
    if not os.path.isdir(passages_path):
        raise ArgumentError('No passages directory')

    htmls_path = os.path.join(args.datadir, 'all_htmls')
    if not os.path.isdir(htmls_path):
        raise ArgumentError('No all_htmls directory')

    empties = find_empties(passages_path)

    shuffle(empties)

    fill_dir(empties, htmls_path)
