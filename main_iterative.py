import pandas as pd
import util.build_data as build_data
from util.get_data_uc import UC_Scraper
import os
from bs4 import BeautifulSoup
import logging
import selenium
import time
import re
from datetime import datetime, timedelta
import pytz
import tldextract
from urllib.parse import urljoin, urlparse
import sys
from multiprocessing import Process, Manager, Pool, freeze_support
from langdetect import detect as langdetect
from util.argparsers import main_iterative_parser as parser

CWD = os.getcwd()

def run_row(row, area, search_terms, date_time,  allow_block_dict, output_dir, sizecutoff, retrycutoff, webcache, iterations):
    
    driver = UC_Scraper(
        SIZE_CUTOFF=sizecutoff, 
        RETRY_CUTOFF=retrycutoff, 
        WEBCACHE=webcache)
    
    # breakpoint()

    errors = False

    pulled_sites = {}

    statement = f'Setting up logger for {row[1]}_{area}'
    print(statement)
    high_logger = my_custom_logger(f"{output_dir}/{date_time}/logs/scraper/{date_time}.log")
    high_logger.warning(statement)

    statement = f'Building initial data structures from Seed links sheet for {row[1]}_{area}'
    print(statement)
    high_logger.warning(statement)
    raw = build_data.build_obj(row, driver)

    filename = f"{area}_{raw['site_name'].replace('.', '_')}_{date_time}"
    logger = my_custom_logger(f"{output_dir}/{date_time}/logs/scraper/{filename}.log")

    if not raw['site_name'] in pulled_sites:
        pulled_sites[raw['site_name']] = {'AI': []}

    statement = f"== Conducting scraping for {area} on {raw['site_name']}"

    tic = time.perf_counter()
    print(statement)

    logger.warning(statement)
    high_logger.warning(statement)

    # add the first set of links downloaded
    # these are the seed links we got by hand
    if "site_url" in raw:
       redirected_url = driver.follow_redirect(raw["site_url"])  # Follow redirect first
    if not redirected_url:
        redirected_url = raw["site_url"]  # Use original URL if redirect fails

    try:
        raw['pages'][0] = {"url": redirected_url, "html": driver.get_html(redirected_url)}
    except Exception as e:
        print(f"Failed to scrape: {redirected_url}. Error: {e}")
        raw['pages'][0] = {"url": redirected_url, "html": "Failed"}



    for page in raw['pages'].values():
        pulled_sites[raw['site_name']][area].append(page['url'])

    # for every new platform, area combo, keep track of sites we visited and proved we dont need
    links_without_search_terms = []

    done = False
    iteration = 0

    # instead of looping through raw, loop through a set of a list which is first set to raw, then set to what is added to raw each iteration. 
    pages_to_check_for_more = raw['pages'].values()
    statement =  f'== Getting initial {len(pages_to_check_for_more)} pages in sheet'
    # print(statement)
    logger.warning(statement)
    lookup_time = datetime.now()

    while not done:
        statement = f'==== We are at iteration {iteration+1} (tree depth).'
        logger.warning(statement)


        new_links_with_search_terms = []

        # looks through the set of links for more, unused, relevant links
        page_count=0
        for page in pages_to_check_for_more:
            statement = f"====== We are on page {page_count+1} of {len(pages_to_check_for_more)}: {page['url']}"

            logger.warning(statement)
            # get all links in page body
            soup = BeautifulSoup(page['html'], features="lxml")
            if not soup:
                logger.warning(f"No soup? page:{page}")
            all_links = []
            all = soup.find_all('a', href=True)
            for a in all:
                ln = a.get('href')
                all_links.append(ln)

            if (len(all_links) == 0):
                logger.error('ERROR: Somehow this page has no links... ')
                errors = True

            statement = f'====== Number of Links on this Page: {len(all_links)}'
            logger.warning(statement)
            # keep new links that contain search terms
            link_count=0
            for raw_link in all_links:

                link = raw_link
                statement = f'======== We are on link {link_count+1} of {len(all_links)}'
                logger.warning(statement)

                statement = f'========== raw link {link}'
                logger.warning(statement)

                link = link.lstrip() # strip leading whitespace
                link = link.replace(" ", "")
                link = re.sub(r"(?<!:)/{2,}", r"/", link) # replaces all occurences of consecutive slashes with a single slash unless they are preceeded by a colon
                if link.startswith('#') or ('javascript:' in link) or ('mailto:' in link) or ('/' == link) or (len(link) == 0) or \
                   link.startswith("<!") or link.endswith(".pdf") or ('fb-messenger://' in link) or ('whatsapp://' in link):
                    statement = "========== dropped link (either fragment (\"#\"), js, mailto, comment, pdf, or empty)"
                    logger.warning(statement)
                    link_count+=1
                    continue

                link = link.rstrip() # strip following whitespace

                # drop leading periods
                if link.startswith('..'):
                    link = link[2:]
                elif link.startswith('.'):
                    link = link[1:]

                if (link.startswith("?")):
                    statement = f"============ Link starts with ?: joining {page['url']} and {link}"
                    logger.warning(statement)
                    link = f"{page['url']}{link}"

                # for relative links that dont start with / or ?, add one
                if ('.' not in link) and (not link.startswith('/')):
                    link = "/" + link
                    
                # beautiful soup may have parsed out a relative link, fix to make absolute 
                # checks if .tld is in the link, doesn't assume its relative if it is. e.g. /imgur.com/tos is not relative
                if link.startswith('/'):
                    if (f".{tldextract.extract(raw['site_url']).suffix}" not in link): # No domain. e.g. "/help/tos/"
                        statement = f"============ Found Relative: joining {page['url']} and {link}"
                        logger.warning(statement)
                        link = urljoin(page['url'], link)
                    elif (f"{urlparse(page['url']).scheme}://" in link): # Domain and scheme aready. e.g. "/help/login_redirect=http://www.linkedn.com/tos/"
                        statement = f"============ Found Relative: joining {page['url']} and {link}"
                        logger.warning(statement)
                        link = urljoin(page['url'], link)
                    else: # No schema, but domain already. e.g. "/imgur.com/tos"
                        statement = f"============ Prepended scheme."
                        logger.warning(statement)
                        link = f"{urlparse(page['url']).scheme}://{link}"
                        link = re.sub(r"(?<!:)/{2,}", r"/", link)  # fixes number of slashes

                # any of the allows are in the link and none of the blocks. must have at least one allow
                # also checks for allows/blocks after redirects
                if not any(x in link for x in allow_block_dict[raw['site_id']]['allows']) or any(y in link for y in allow_block_dict[raw['site_id']]['blocks']):
                    statement = f"========== dropped link {link}. Didn't pass first allows/blocks test."
                    
                    logger.warning(statement)
                    link_count+=1
                    continue

                statement = f"============ Checking for Redirections: {link}" 
                logger.warning(statement)               
                if ((datetime.now() - lookup_time) > timedelta(seconds=5)):
                    time.sleep((datetime.now() - lookup_time).seconds)
                rlink = driver.follow_redirect(link)
                lookup_time = datetime.now()
                if rlink:
                    if rlink != link:
                        statement = f"============ Followed Redirection to {rlink}" 
                        logger.warning(statement)
                        link = rlink
                    else:
                        pass
                        # redirection link and original link same
                else:
                    statement = f"========== dropped link {link}. Could not follow redirection (or it was a meaninglessly small page or bot blocked by sessionID)." # e.g. guardian sign in page
                    logger.warning(statement)
                    link_count+=1
                    continue
                # drop query strings and anchor links
                link = link.split('?')[0]
                link = link.split('#')[0]

                if link == raw_link:
                    statement =  "============ Link unchanged"
                    logger.warning(statement)
                else:
                    statement = f"============ Link after cleaning: {link}"
                    logger.warning(statement)

                # any of the allows are in the link and none of the blocks. must have at least one allow
                if any(x in link for x in allow_block_dict[raw['site_id']]['allows']) and not any(y in link for y in allow_block_dict[raw['site_id']]['blocks']):

                    # if not already accounted for
                    if (link not in pulled_sites[raw['site_name']][area]) and (link not in new_links_with_search_terms) and (link not in links_without_search_terms):
                        try: # scraping
                            statement = f"========== scraping {link}"
                            logger.warning(statement)
                            source_html = driver.get_html(link)
                        except (selenium.common.exceptions.WebDriverException, selenium.common.exceptions.TimeoutException) as e:
                            logger.error(f'Error: scraping {link} resulted in the following exception:\n{e}')
                            errors = True
                            link_count+=1
                            continue                     
                        # dont check for search terms if the page is not in english        
                        try:              
                            next_soup = BeautifulSoup(source_html, features="lxml")
                            page_text = next_soup.get_text()
                            is_english = (langdetect(page_text[:min(len(page_text)-1, 5000)]) == 'en')
                            # checks first 5000 characters or length of page if it is less to use for english check
                        except (Exception) as e:
                            statement = f'============ Checking {link} for language resulted in the following exception:\n{e}'
                            logger.warning(statement)

                        if is_english:
                            # instead of looking in source html, just look in text (but still download all html if search term found in text)
                            page_text = next_soup.get_text()
                            area_search_terms = search_terms["search_terms"].dropna()
                            # if includes this area's search terms
                            st_found = False
                            for st in area_search_terms:
                                # Treat copyright differently for a search term using the negative regexp
                                if 'copyright' in st.lower():
                                    # this looks for copyright matches only if it is not followed by a year (with 0-3 wildcard spaces in between)
                                    x = re.search("copyright(?!((.?){3}[12][0-9]{3}))", page_text, flags=re.IGNORECASE)
                                    if x:
                                        st_found = True
                                elif 'trust' in st.lower():
                                # this looks for trust matches only if not followed by key. "Trustkey" was giving false positives
                                    x = re.search("trust(?!(key))", page_text, flags=re.IGNORECASE)
                                    # x is none if no matches
                                    if x:
                                        st_found = True

                                # all other search terms just search for it in text normally. But make sure that it is not preceeded by a letter
                                else:
                                    my_re = "(?<![a-zA-Z])" + re.escape(st)
                                    x = re.search(my_re, page_text, flags=re.IGNORECASE)
                                    if x:
                                        st_found = True
                                # TODO: Switch back to if st_found
                                if True:   
                                    break # found a search term, dont need to keep checking
                            if True:
                                # build up list of new found sites 
                                statement = f"============ New link added. Search term ({st}) found on {link}."
                                logger.warning(statement)
                                statement = f"============== Page containing the link: {page['url']}"
                                logger.warning(statement)
                                new_links_with_search_terms.append(link)
                            else: # after checking all Search terms, if still not found, add link to blacklist (for this platform+area combo)
                                links_without_search_terms.append(link) 
                        else:
                            statement = f"============ link is not english."
                            logger.warning(statement)
                    else:
                        statement = "========== link already checked"
                        logger.warning(statement)
                else:
                    statement = f"============ Excluded based on allow/block list."
                    logger.warning(statement)
                link_count+=1

            page_count+=1

        # add round of missing sites to raw_addage
        raw_addage = driver.get_htmls(new_links_with_search_terms)

        # drop none retruns in case got none from get_html
        raw_addage_temp = {
            key: value for key, value in raw_addage.items()
            if value is not None
        }
        raw_addage = raw_addage_temp

        # update keys so doesn't overlap with existing keys in raw
        raw_addage = dict([(k+len(raw['pages']), v) for (k, v) in raw_addage.items()])
        # update pages to look at
        pages_to_check_for_more = raw_addage.values()
        # merge dicts
        # need to keep raw full for building file at end
        raw['pages'].update(raw_addage)
        # update record of sites pulled
        statement = f'==== Number of new pages added: {len(new_links_with_search_terms)}'
        # print(statement)
        pulled_sites[raw['site_name']][area].extend(new_links_with_search_terms)
        logger.warning(statement)

        # done criteria based on tree depth
        if iteration >= iterations - 1:
            # since its checkin one layer deeper, this is a tree depth of 2. 
            done = True

        if done:
            toc = time.perf_counter()
            statement = f"== Finished scraping {raw['site_name']}-{area} in {toc - tic:0.4f} seconds."
            print(statement)
            logger.warning(statement)
            high_logger.warning(statement)

        # for stopping at reached tree depth
        iteration += 1
    statement = f'== Writing to db file'
    # print(statement)
    logger.warning(statement)
    out_file = f"{output_dir}/{date_time}/all_htmls/{filename}.json"
    build_data.build_file(raw, out_file)
    statement = f'== Done ({out_file})'
    print(statement)
    logger.warning(statement)
    if errors:
        statement = f'== Completed with Errors, search for error in logs'
        print(statement)
        logger.error(statement)

    return f'Finished: ({out_file})'


# INPUT:
#   PATH: the path to the links excel file (str)
#   area: either 'copyright', 'misinformation', or 'hatespeech' (str)
# OUTPUT:
#   builds a file (and its zipped version) containing a list of json objects storing html data
#       also iterates on links within the html data, looks for the search terms in those nested links,
#       and adds them to the raw dataset if they include the search terms.
def main(links, search_terms, outdir, pools, sizecutoff, retrycutoff, webcache, iterations):
    if pools:
        pool = Pool(pools)
    # manager = Manager()  Dont need shared objects/data structures. 
    date_time = datetime.now(pytz.timezone('US/Central')).strftime('%m_%d_%y_%H_%M')
    os.makedirs(f"{outdir}/{date_time}/all_htmls/", exist_ok=True)
    os.makedirs(f"{outdir}/{date_time}/logs/scraper/", exist_ok=True)
    tick = time.perf_counter()

    high_logger = my_custom_logger(f"{outdir}/{date_time}/logs/scraper/{date_time}.log")
    with open(f"{outdir}/temp.txt", 'w') as f:
        f.writelines(f'{date_time}')

    statement = f'Using multiprocessing: {bool(pools)}'
    print(statement)
    high_logger.warning(statement)

    url_filter_dict = {}
    # OLD: need to make sure the allowlist and blocklists have same sites and IDs as all sheets!!
    df_ai = pd.read_excel(links, sheet_name="AI", engine="openpyxl")
    # No need for allow/block lists, only scrape AI-related sites
    url_filter_dict = {}
    for i in range(len(df_ai)):
        id = df_ai.loc[i][0]
        not_empty = (not pd.isnull(id)) and (str(id).strip() != '')

        if not_empty:
            allow_row = ['.']  # Default to allowing everything
            site_url_filter_dict = {'allows': allow_row, 'blocks': []}  # No block list
            url_filter_dict[id] = site_url_filter_dict
    

    search_terms = pd.read_csv(search_terms, names=["search_terms"], skiprows=1)
    jobs = []
    area = "AI"  # Only scrape AI-related content
    df = pd.read_excel(links, sheet_name="AI", engine="openpyxl")  # Read only the "AI" sheet

    # Loop through the AI sheet and process each site
    for i in range(len(df)):
        id = df.loc[i, "site_id"]  # Ensure correct column name
        not_empty = (not pd.isnull(id)) and (str(id).strip() != '')

        if not_empty:
            row = df.loc[i]
            print(f"spawning job for {area} on {row['site_name']}")
            if pools:
                jobs.append(pool.apply_async(run_row, args=(row, area, search_terms, date_time, url_filter_dict, outdir, sizecutoff, retrycutoff, webcache, iterations), callback=callback, error_callback=pcb))
            else:
                run_row(row, area, search_terms, date_time, url_filter_dict, outdir, sizecutoff, retrycutoff, webcache, iterations)


    if pools:
        for job in jobs:
            try:
                end = job.get()
            except (Exception) as e:
                end = e
            print(end)
            high_logger.warning(end)
        pool.close()       
        pool.join()
    print(f'Done full. Total time: {time.perf_counter() - tick:0.4f}', flush=True)

def callback(result):
    print('success', result)

def pcb(res):
    print(f'One of the jobs errored: {res}')


def sheet_row_to_list(row):
    ls = []
    for item in row:
        item = str(item).strip()
        if (item != 'nan') and (item != ''):
            ls.append(item)
    return ls

# apparently this is how you get a new log file for each loop iteration ... 
def my_custom_logger(logger_name, level=logging.WARNING):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    file_handler = logging.FileHandler(logger_name, mode='a', encoding="utf-8")
    logger.addHandler(file_handler)
    return logger

if __name__ == "__main__":

    args = parser.parse_args()

    if not os.path.isdir(args.outdir):
        os.mkdir(args.outdir)

    main(**vars(args))
