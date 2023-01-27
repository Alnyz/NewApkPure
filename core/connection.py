from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import RequestException
import cloudscraper
import requests
import time
from typing import Generator, Any

class Connection(object):
    def __init__(self, **connection_config):
        """
            :param ``connection_config``: Optional arguments that ``request`` takes.
            
            example:
                Connection(headers={'user-agent':'python 3.11.1'}, stream=True)
        """
        self.config = connection_config
        self.session = requests.Session()
        self.scraper = cloudscraper.create_scraper()
    
    def make_connection(self, url):
        RETRIES = 0
        while True:
            try:
                web = self.scraper.get(url, **self.config)
                break
            except RequestException:
                RETRIES += 1
                if RETRIES > 5:
                    web = None
                
                time.sleep(2)
                continue
        return web

    def create_connections(self, urls) -> Generator[Any, None, None]:
        urls = urls if isinstance(urls, (list, tuple)) else [urls]
        with ThreadPoolExecutor(max_workers=4) as executor:
            res = executor.map(self.make_connection, urls)
            return res
