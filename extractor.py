import numpy as np
import json
import os
from bs4 import BeautifulSoup as bs4
import sys
import logging
from multiprocessing import Process, Manager, Pool, freeze_support
from util.argparsers import extractor_parser

def pool_job(datadir, html_json_file, logger_path):
    high_logger = my_custom_logger(logger_path)

    file_name = html_json_file.split('/')[-1].split('\\')[-1]
    site = file_name.split('_')[1]
    area = file_name.split('_')[0]
    with open(f"{html_json_file}", "r", encoding='utf-8') as f:
        jdata = json.load(f)
    statement = f'== Extracting text from {site} {area} htmls'
    print(statement)
    high_logger.warning(statement)

    platform_dict = {"platform": site, "area": area}
    platform_dict['pages'] = []

    for (page_key, page_info) in jdata['pages'].items():
        page_dict = {"page_id": page_key, "source": page_info['url']}

        page_soup = bs4(page_info['html'], features='lxml')
        text_elements = []
        for string in page_soup.strings:
            if not string.isspace():
                text_elements.append(f"{string}\n")

        page_dict['text'] = text_elements
        platform_dict['pages'].append(page_dict)


    output_file = f"{datadir}/all_text/{area}/{site}.json" 
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(platform_dict , f)
    statement = f"==== wrote to {output_file}"
    print(statement)
    high_logger.warning(statement)
                
    statement = f"== Completed {site} {area} text extraction"
    print(statement)
    high_logger.warning(statement)


def extract_text(datadir, pools, **kwargs):
    if pools:
        pool = Pool(pools)
    
    html_directory = f"{datadir}/all_htmls/"

    try:
        os.mkdir(f"{datadir}/all_text/")
    except FileExistsError:
        pass
    try:
        os.mkdir(f"{datadir}/all_text/AI")  # <== Add this line to create AI folder
    except FileExistsError:
        pass
    try:
        os.mkdir(f"{datadir}/logs/extractor/")
    except FileExistsError:
        pass


    logger_path = f"{datadir}/logs/extractor/prints.log"
    high_logger = my_custom_logger(logger_path)

    for file in os.listdir(f"{html_directory}"):
        if file.endswith('.json'):
            
            html_json_path = f"{html_directory}/{file}"

            if pools:
                pool.apply_async(pool_job, args=(datadir, html_json_path, logger_path), error_callback=pcb)
            else:
                pool_job(datadir, html_json_path, logger_path)

    if pools:
        pool.close()
        pool.join()

            
        
    statement = f"Completed Extraction for {datadir}"
    print(statement)
    high_logger.warning(statement)

def pcb(res):
    print(f'One of the jobs errored: {res}')

def my_custom_logger(logger_name, level=logging.WARNING):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    file_handler = logging.FileHandler(logger_name, mode='a')
    logger.addHandler(file_handler)
    return logger

if __name__ == "__main__":
    args = extractor_parser.parse_args()
    
    extract_text(**vars(args))
