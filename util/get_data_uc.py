import time
import os
import random
from selenium.common.exceptions import TimeoutException, WebDriverException, InvalidSessionIdException
from urllib3.exceptions import ReadTimeoutError
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup as Soup
from fake_useragent import UserAgent
import tempfile
from pathlib import Path
import shutil
from selenium.webdriver.chrome.service import Service




class UC_Scraper: 

    def __init__(self, SIZE_CUTOFF=1000, RETRY_CUTOFF=10, WEBCACHE=True):
        '''
        Creates a Selenium driver (Chrome)

        Returns:
            driver (WebDriver): Selenium driver object
        '''
        self.SIZE_CUTOFF = SIZE_CUTOFF
        self.RETRY_CUTOFF = RETRY_CUTOFF
        self.WEBCACHE = WEBCACHE

        #original
        #chrome_driver_path = "/usr/local/bin/chromedriver"
        #chrome_binary_path = "/usr/bin/google-chrome"

        #hardcoded paths
        chrome_driver_path = "/home/zaynacheema/ContentModerationWebScraper/chromedriver_136/chromedriver-linux64/chromedriver"
        chrome_binary_path = "/home/zaynacheema/ContentModerationWebScraper/chrome_136/chrome-linux64/chrome"

        #force correct Chrome binary at runtime
        os.environ["GOOGLE_CHROME_BIN"] = chrome_binary_path

        
        options = webdriver.ChromeOptions()
        options.headless = True  
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        #options.add_argument(f"user-agent={UserAgent().random}")  # Random user-agent
        options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
        options.add_argument("--blink-settings=imagesEnabled=false")  # disables images
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")


        #create a guaranteed unique temp profile
        self.temp_profile = tempfile.mkdtemp(prefix="chrome-profile-")
        options.add_argument(f"--user-data-dir={self.temp_profile}")
            
        #self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        #FOR TESTING PURPOSESS
        service = Service(executable_path=chrome_driver_path)
        os.environ["CHROME_BINARY"] = chrome_binary_path  # <-- force env for subprocess
        options.binary_location = chrome_binary_path
        self.driver = webdriver.Chrome(service=service, options=options)

        

        self.cur_link = ''
        self.cur_page_source = ''
    
    def __del__(self):
        try:
            shutil.rmtree(self.temp_profile, ignore_errors=True)
        except Exception as e:
            pass

    def follow_redirect(self, link):
        #sanitize malformed urls
        #link = link.replace("??", "?").strip()
        
        tries = 1
        while tries <= self.RETRY_CUTOFF:
            try:
                self.driver.get(link)
                WebDriverWait(self.driver, timeout=15).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                time.sleep(random.randint(3,5)) # make sure JS loads
                page_source = self.driver.page_source
                text = Soup(page_source, features='lxml').get_text()
            except (TimeoutException, WebDriverException, InvalidSessionIdException, ReadTimeoutError) as e:
                print("Connection Error")
                return None
            
            if len(text) > self.SIZE_CUTOFF:
                self.cur_link = self.driver.current_url 
                self.cur_page_source = page_source
                return self.cur_link
            
            # on the last try, it tries google's webcache
            if self.WEBCACHE and tries == self.RETRY_CUTOFF - 1:
                link = 'https://webcache.googleusercontent.com/search?q=cache:' + link

            tries = tries + 1
            
        return None

    # INPUT:
    #   link: link to retrieve html page source from (str)
    # OUTPUT: 
    #   html page source (str)
    def get_html(self, link: str):
        if link == (self.cur_link.split('?')[0].split('#')[0]): 
            return self.cur_page_source
        else:
            print(f"Warning: Calling get_html() on {link} without follow_redirect(). Attempting fallback.")
            self.follow_redirect(link)  # Try following redirect again
            return self.cur_page_source if self.cur_page_source else "Failed"

# INPUT:
#   in_links: an array of links for each platform, which may contain empty values
# OUTPUT: 
#   a dictionary of the raw html responses for each link
    def get_htmls(self, in_links):
        # get rid of empty cells in in_links
        links_arr = []
        for in_link in in_links:
            in_link = str(in_link).strip()
            if (in_link != 'nan') and (in_link != ''):
                links_arr.append(in_link)

        links = {}
        for i in range(len(links_arr)):
            rlink = self.follow_redirect(links_arr[i])
            if rlink:
                link = {'url': rlink,
                        'html': self.get_html(rlink.split('?')[0].split('#')[0])}
            else: 
                link = {'url': links_arr[i],
                        'html': 'Failed'}
            links[i] = link
        return links
