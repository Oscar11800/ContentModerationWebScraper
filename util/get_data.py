'''
More minimal single page scraper. 

Used in fill.py script

Can be used for benchmarking, filling missing data, etc. 
'''

import undetected_chromedriver as uc_webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as Soup

def setup_driver():
    '''
    Creates a Selenium driver (Chrome)

    Returns:
        Selenium driver object
    '''

    options = Options()

    options.add_argument("--headless")
    options.add_argument('--log-level=3')
    options.add_argument("--enable-javascript")
    options.set_capability('unhandledPromptBehavior', 'dismiss')
    options.add_argument("--dns-prefetch-disable")
    options.add_argument('log-level=3')
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    driver = uc_webdriver.Chrome(
        options=options
    )

    return driver

def driver_wait(driver):
    try:
        WebDriverWait(driver, timeout=5).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, '//div[normalize-space(text())]')
            )
        )
    except:
        pass

def get_html(link: str, driver, retry: int):
    '''
    Gets raw HTML text from specified link. 
    Will retry if less than 1000 characters in HTML text
    10 retries max before giving up

    Args:
        link (str): link with HTML to get
        driver (WebDriver): Selenium driver to use

    Returns:
        Raw HTML string
    '''

    # Get HTML

    driver.get(link)
    driver_wait(driver)

    html = driver.page_source

    text = Soup(html, features='lxml').get_text()

    # Retries

    if len(text) < 1000 and retry < 10:
        return get_html(link, driver, retry+1)

    # Use Google Cache site if excessive retries
    if retry == 10:
        driver.get('https://webcache.googleusercontent.com/search?q=cache:' + link)
        text = Soup(driver.page_source, features='lxml').get_text()

    return driver.page_source

