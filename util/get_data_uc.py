from selenium.common.exceptions import TimeoutException, WebDriverException, InvalidSessionIdException
from selenium.webdriver.support.wait import WebDriverWait
import undetected_chromedriver as uc 
from bs4 import BeautifulSoup as Soup

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

        self.driver = uc.Chrome(headless=True)
        self.cur_link = ''
        self.cur_page_source = ''

    def follow_redirect(self, link):
        tries = 1
        while tries <= self.RETRY_CUTOFF:
            try:
                self.driver.get(link)
                WebDriverWait(self.driver, timeout=5).until(
                    lambda webdriver: 
                        webdriver.execute_script('return document.readyState') == 'complete'
                )
                page_source = self.driver.page_source
                text = Soup(page_source, features='lxml').get_text()
            except (TimeoutException, WebDriverException, InvalidSessionIdException) as e:
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
        if link == (self.cur_link.split('?')[0].split('#')[0]): # the main pipeline also dropping this so have to match. 
            return self.cur_page_source
        else:
            # print(self.cur_link, link)
            raise Exception(f"Either you did not call follow-redirect first (sorry Jay) or Brennan did something wrong implementing the class. {self.cur_link} {link}")

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
