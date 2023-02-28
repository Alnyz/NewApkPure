from typing import Generator, Any, List, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import RequestException
from core.exceptions import MaxRetriesExceed
from functools import partial
from numpy import ndarray
import cloudscraper
import requests
import time

class Connection(object):
    def __init__(self, **connection_config):
        """
            Parameters
            ----------
            connection_config: Optional arguments that ``requests`` takes.
            
            Examples:
            -------
            >>> con = Connection(headers={'user-agent':'python 3.11.1'}, timeout=10)
                
            or you can assign like this:
                
            >>> con = Connection()
            >>> con.config['headers'] = {'user-agent':'python 3.11.1'}
            >>> con.config['timeout'] = 10
            >>> con.config['proxies'] = {'http': 'yourproxy.com', 'https': 'yourproxy.com'}
        """
        self.worker = 4
        self.config = connection_config
        self.config['proxies'] = self.config.get('proxies', {})
        self.session = requests.Session()
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'android',
                'desktop': False
            }
        )
        
    def single_connection(self, url: str, **extra_conf):
        self.config['headers'] = {
            'user-agent': 'Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; SCH-I535 Build/KOT49H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
            'authority': 'apkpure.com',
            'referer': url,
        }
            
        self.config.update(**extra_conf)
        RETRIES = 1
        SLEEP_RETRIES = 0.5
        while True:
            try:
                web = self.scraper.get(url, **self.config)
                break
            except RequestException:
                RETRIES += 1
                SLEEP_RETRIES += 0.3
                if RETRIES > 10:
                    raise MaxRetriesExceed('Maximum retries exceed, please check your connection and try again.')

                time.sleep(SLEEP_RETRIES)
                continue

        RETRIES = 0
        SLEEP_RETRIES = 0
        return web

    def create_connections(self, urls: Union[List[str], Tuple[str], str], **extra_conf) -> Generator[Any, None, None]:
        assert isinstance(urls, (str, list, tuple, set, ndarray)), f'urls must be type `str`,`list`, `tuple` or `set` not {type(urls)}'
        urls = urls if isinstance(urls, (list, tuple, set, ndarray)) else [urls]
        with ThreadPoolExecutor(max_workers=self.worker) as executor:
            res = executor.map(partial(self.single_connection, **extra_conf), urls)
            return res
