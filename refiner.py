import os
import pandas as pd
import re
import sys
import json
import spacy
import logging
from multiprocessing import Process, Manager, Pool, freeze_support
from util.argparsers import refiner_parser

def my_custom_logger(logger_name, level=logging.WARNING):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    # console_handler = logging.StreamHandler(sys.stdout)
    # logger.addHandler(console_handler)
    file_handler = logging.FileHandler(logger_name, mode='a')
    logger.addHandler(file_handler)
    return logger

def make_sentences(lines):
    nlp = spacy.load('en_core_web_sm')
    full_text = "".join(lines)
    full_text = " ".join(full_text.split("\n"))
    full_text = " ".join(full_text.split("\t"))
    full_text = " ".join(full_text.split())
    sentences = []

    if len(full_text) > nlp.max_length:
        return None

    for i in nlp(full_text).sents:
        sentences.append(i.text.strip()+'\n')
    return sentences

def pool_job(datadir, area, platform, output_dir, area_search_terms, plusminus, log_file_path):
    platform_dict = {"platform": platform, "area": area}
    pages = []
    high_logger = my_custom_logger(log_file_path)

    with open(f"{datadir}/all_text/{area}/{platform}", 'rb') as f:
        all_text_json = json.load(f)

    statement = f"refining {datadir}/all_text/{area}/{platform}"
    print(statement)
    high_logger.warning(statement)

    for page in all_text_json['pages']:
        page_num = page['page_id']
        lines = page['text']
        page = page['source']

        sentences = make_sentences(lines) # tokenize all lines into sentences
        if not sentences:
            statement = f'page {page_num} too long to parse by spacy. {area} {page}'
            print(statement)
            high_logger.warning(statement)
            continue

        page_dict = {"page_id": page_num, "source": page}
        passages = []

        print_buffer = ['']
        prev_right_lim = -1
        for line_num in range(len(sentences)):
            sts_found = []
            for st in area_search_terms:
                st_found = False
                sst = st.lower().strip()
                # Treat copyright differently for a search term using the negative regexp
                if 'copyright' in sst:
                    # this looks for copyright matches only if it is not followed by a year (with 0-3 wildcard spaces in between)
                    x = re.search("copyright(?!((.?){3}[12][0-9]{3}))", sentences[line_num], flags=re.IGNORECASE)
                    # x is none if no matches
                    if x:
                        st_found = True
                elif 'trust' in sst:
                    # this looks for trust matches only if not followed by key. "Trustkey" was giving false positives
                    x = re.search("trust(?!(key))", sentences[line_num], flags=re.IGNORECASE)
                    # x is none if no matches
                    if x:
                        st_found = True

                # all other search terms just search for it in text normally. 
                else:
                    # has to be start of a word
                    my_re = "(?<![a-zA-Z])" + re.escape(sst)
                    x = re.search(my_re,  sentences[line_num], flags=re.IGNORECASE)
                    if x:
                        st_found = True

                if st_found:    
                    sts_found.append(sst)

            if sts_found:    
                # print(sts_found)
                left_lim = max([line_num-plusminus, 0])
                right_lim = min([len(sentences)-1, line_num+plusminus+1])
                # print(left_lim, line_num, right_lim, prev_right_lim)

                # join with existing buffer
                if left_lim <= prev_right_lim:
                    print_buffer.extend(sentences[prev_right_lim+1:right_lim+1])
                    already_sts = print_buffer[0].split(' ')
                    already_sts.extend(sts_found)
                    all_sts = list(set(already_sts))
                    print_buffer[0] = ' '.join(all_sts)

                # start new passage
                else:
                    if (len(print_buffer) == 1) and (print_buffer[0] == ''):
                        # first time so dont have to print prev buffer
                        # add new to buffer
                        print_buffer = [' '.join(sts_found)]
                        print_buffer.extend(sentences[left_lim:right_lim+1])
                    else:
                        # print prev buffer
                        sts_to_print = print_buffer[0].split()
                        new_passage = {"terms": sts_to_print, "text": print_buffer[1:]}
                        passages.append(new_passage)

                        # add new to buffer
                        print_buffer = [' '.join(sts_found)]
                        print_buffer.extend(sentences[left_lim:right_lim+1])

                prev_right_lim = right_lim

        # include final buffer
        sts_to_print = print_buffer[0].split()
        new_passage = {"terms": sts_to_print, "text": print_buffer[1:]}
        passages.append(new_passage)
        
        if (len(passages) == 1) and (len(passages[0]['terms']) == 0):
            nothing_passages = ['No search terms found here. I am assuming this was included in your original list of links as a sort of index to other pages.', 'Or the page was scraped differently than it appears (Bot blockers, eg.)']
            passages = [{"terms": [], "text": nothing_passages}]

        page_dict["passages"] = passages
        pages.append(page_dict)

    platform_dict["pages"] = pages
    with open(f'{output_dir}/{platform}.json', 'w', encoding="utf-8") as f:
        json.dump(platform_dict, f)


def chunk_by_search_terms(datadir, search_terms, plusminus, pools, **kwargs):
    if pools:
        pool = Pool(5)
    
    if isinstance(search_terms, str):  
        search_terms = pd.read_csv(search_terms, names=["search_terms"], skiprows=1)

    try: 
        output_dir = f"{datadir}/passages/"
        os.makedirs(output_dir, exist_ok=True)
    except FileExistsError:
        pass

    try: 
        os.makedirs(f"{datadir}/logs/refiner/", exist_ok=True)
    except FileExistsError:
        pass

    log_file_path = f"{datadir}/logs/refiner/prints.log"

    for area in ['AI']:  
        if isinstance(search_terms, str):  
            search_terms = pd.read_csv(search_terms, names=["search_terms"], skiprows=1)

        area_search_terms = search_terms["search_terms"].dropna()

        try:
            os.makedirs(f"{datadir}/passages/{area}", exist_ok=True)  
        except FileExistsError:
            pass

        correct_path = os.path.abspath(f"{datadir}/all_text/{area}")
        print(f"Checking path: {correct_path}")  # Debugging line

        if not os.path.exists(correct_path):
            raise FileNotFoundError(f"Expected directory not found: {correct_path}")

        for platform in os.listdir(correct_path):
            if pools:
                pool.apply_async(pool_job, args=(datadir, area, platform, output_dir, area_search_terms, plusminus, log_file_path), error_callback=pcb)
            else:
                pool_job(datadir, area, platform, output_dir, area_search_terms, plusminus, log_file_path)

    if pools:
        pool.close()
        pool.join()
    
def pcb(res):
    print(f'One of the jobs errored: {res}')

if __name__ == "__main__":
    args = refiner_parser.parse_args()

    chunk_by_search_terms(**vars(args))
