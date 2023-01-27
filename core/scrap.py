from core.connection import Connection
from bs4 import BeautifulSoup
from core.exceptions import AppNotFoundException
from threading import Thread, Lock
import re

SEARCH_URL = 'https://apkpure.com/search-page?q={}&t=app&begin={}'
BASE_URL = 'https://apkpure.com'

class Scraping(object):
    def __init__(self, **connection_config):
        self.con = Connection(**connection_config)
        self.list_apps = set()
        self.lock = Lock()
        self.stop_flag = False
    
    def get_download_url(self, url):
        if not url.endswith('download'):
            url = url + '/download'
            
        req = self.con.make_connection(url)
        soup = BeautifulSoup(req.content, 'lxml')
        url_dl = soup.select_one('div.download-box > a')['href']
        package_name = soup.find(string=re.compile('Package Name')).find_next('a').text.strip()
        return url_dl, package_name
    
    def get_detail_search(self, url):
        req = self.con.make_connection(url)
        soup = BeautifulSoup(req.content, 'lxml')
        info = soup.select_one('div.additional')
        vers_list = soup.select('div.version-list a')[:-1]
        app_name = soup.select_one('.title_link').text.strip()
        version = info.find(string='Latest Version').find_next('p').text.strip()
        sizes = ''.join([i.find('span', class_='size').text.strip() for i in vers_list \
            if 'XAPK' not in i['href'] and i['data-dt-version'] == version])
        update = info.find(string='Updated on').find_next('p').text.strip()
        req_android = info.find(string='Requires Android').find_next('p').text.strip()
        package_name = url.split('/')[-1]
        data = {
            'app_name': app_name,
            'version': version,
            'update': update,
            'requirement': req_android,
            'size': sizes,
            'package_name': package_name,
            'url': url
        }
        return data
    
    def __thread_search(self, query):
        page = 0
        while True:
            with self.lock:
                if self.stop_flag:
                    break
                req = self.con.make_connection(SEARCH_URL.format(query, page))
                soup = BeautifulSoup(req.content, 'lxml')
                apps = soup.select('li')
                for app in apps:
                    url_app = app.a['href']
                    if not app in self.list_apps:
                        self.list_apps.add(url_app)
                
                if not apps:
                    break
                page += 10

        
    def search_page(self, query, all_page=False):
        req = self.con.make_connection(SEARCH_URL.format(query, 1))
        soup = BeautifulSoup(req.content, 'lxml')
        apps = soup.select('li')
        if not apps:
            raise AppNotFoundException(f'Cannot find any app with `{query}` query')
        
        if not all_page:
            for app in apps:
                url_app = app.a['href']
                if not app in self.list_apps:
                    self.list_apps.add(url_app)
        else:
            threads = []
            for _ in range(1):
                t = Thread(target=self.__thread_search, args=(query,))
                threads.append(t)
                t.start()
                
            with self.lock:
                self.stop_flag = True
                
            for t in threads:
                t.join()
        print(len(self.list_apps))