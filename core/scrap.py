from core.connection import Connection
from core.exceptions import AppNotFoundException
from bs4 import BeautifulSoup
from threading import Thread, Lock
from humanfriendly import format_size
from typing import List, Dict, Callable
import re

SEARCH_URL = 'https://apkpure.com/search-page?q={}&t=app&begin={}'
BASE_URL = 'https://apkpure.com'

class Scraping(object):
    def __init__(self, connection: Connection):
        """a class that controlling webpage html for scraping

        Parameters
        -----------
        connection (Connection): to make connection to the website
        """
        self.con = connection
        self.list_apps = set()
        self.con_lock = Lock()
        self.stop_flag = False
        self.results_detail = []
    
    
    def create_thread(self, func: Callable, *args):
        threads = []
        for _ in range(1):
            t = Thread(target=func, args=args)
            threads.append(t)
            t.start()
            
        with self.con_lock:
            self.stop_flag = True
            
        for t in threads:
            t.join()
            
    def get_detail_search(self, urls: str | list) -> List[Dict]:
        with self.con_lock:
            reqs = self.con.create_connections(urls)
            for req in reqs:
                soup = BeautifulSoup(req.text, 'lxml')
                try:
                    app_name = soup.select_one('div.title-like').text.strip()
                except AttributeError:
                    app_name = soup.select_one('div.title_link').h1.text.strip()
                    
                version = soup.select_one('span[itemprop="version"]').text.strip()
                try:
                    size = format_size(
                        int(soup.select_one('div.ny-down')['data-dt-filesize'])
                    )
                except:
                    size = format_size(
                        int(soup.select_one('a[data-dt-file_size]')['data-dt-file_size'])
                    )

                update = soup.select_one('p.date').text.strip()
                package_name = [i for i in req.url.split('/') if i][-1]
                download_url = f'https://d.apkpure.com/b/APK/{package_name}?version=latest'
                data = {
                    'app_name': app_name,
                    'version': version,
                    'update': update,
                    'size': size,
                    'package_name': package_name,
                    'url': req.url,
                    'download_url': download_url,
                }
                self.results_detail.append(data)
        
    def search_page(self, query: str, first: bool = True, all_page: bool = False) -> List[str]:
        assert not all([first, all_page]), 'Cannot use all_page with first'
        if not all_page:
            req = self.con.single_connection(SEARCH_URL.format(query, 1))
            soup = BeautifulSoup(req.content, 'lxml')
            apps = soup.select('li')
            
            if not apps:
                raise AppNotFoundException(f'Cannot find any app with `{query}` query')
            
            if first:
                apps = [apps[0]]
            
            for app in apps:
                url_app = app.a['href']
                self.list_apps.add(BASE_URL + url_app)
        else:
            self.create_thread(self.__thread_search, (query,))

        return self.list_apps
    
    def __thread_search(self, query):
        page = 0
        while True:
            with self.con_lock:
                if self.stop_flag:
                    break
                req = self.con.single_connection(SEARCH_URL.format(query, page))
                soup = BeautifulSoup(req.content, 'lxml')
                apps = soup.select('li')
                if not apps:
                    raise AppNotFoundException(f'Cannot find any app with `{query}` query')
                    
                for app in apps:
                    url_app = app.a['href']
                    self.list_apps.add(BASE_URL + url_app)
                
                if not apps:
                    page = 0
                    break
                page += 10