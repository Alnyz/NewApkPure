from core.scrap import Scraping
from core.connection import Connection
from core.models import ItemList, URLS
from core.config import DEFAULT_PATH
from core.download import Download
from pandas import DataFrame
from typing import List

class Api(object):
    def __init__(self,
                 *,
                 temp_path: str = DEFAULT_PATH,
                 **connection_config: dict) -> None:
        self.config = connection_config
        self.__download = Download(self)
        self.__connection = Connection(**self.config)
        self.__scrap = Scraping(self.__connection)
        self.temp_path = temp_path
    
    @property
    def urls(self) -> URLS:
        """
        contains last urls have been search.
        
        if you call this before call `search` this will return empty list
        
        Returns:
            URLS: list of urls
        """
        return URLS(urls=self.scrap.list_apps)
    
    def download(self, __data: DataFrame, *, count: int = 0, index: List[int | None] = []) -> None:
        """download application/APK's from given data

        Parameters
        ----------
        __data (DataFrame): data that will be downloaded
        count (int, optional): how many app you want to download from data. Defaults to 0 mean all of them.
        index (List[int | None], optional): select which index you want to download. Defaults to [].
        
        
        Examples
        --------
        download all data
        >>> api = Api()
        >>> apps = api.search('vpn') #lets say this contain 10 rows data
        >>> api.download(apps) #<= this will download 10 apps
        
        downlooad only 5 data
        >>> api = Api()
        >>> apps = api.search('vpn') #lets say this contain 10 rows data
        >>> api.download(apps, count=5) #<= this will download 5 apps
            note: `count` cannot higher than lenght of rows
        
        download only specific row
        >>> api = Api()
        >>> apps = api.search('vpn') #lets say this contain 10 rows data
        >>> api.download(apps, index=[1,4,7]) #<= this will download only row 1, 4 and 7
        
        Also
        ----
        you downloaded files will be saved in /current working directory/apps/filename.apk .
        you can specific your directory using temp_path
        >>> api = Api(temp_path='/your/path')
        or
        >>> api = Api()
        >>> api.temp_path = '/your/path'
        """
        assert isinstance(index, list), 'index must be list'
        assert count <= __data.shape[1], 'count cannot higher than rows of data'
        data = __data
        data = data.iloc[index] if index else data.iloc[:]
        if count > 0:
            data = data.head(count)
        
        self.__download.putjob(data)
        
    def search(self, query: str, first: bool = True, all_page: bool = False) -> ItemList | DataFrame:
        """search application/APK's using query

        Parameters
        ----------
        query (str): query of app you want to get
        first (bool, optional): show only first app if True. Defaults to True.
        all_page (bool, optional): search through all pages. Defaults to False.
            
        Note
        ----
        you cannot set args `first` and `all_page` together
            
        Returns
        -------
        ItemList || DataFrame
        """
        _search = self.__scrap.search_page(query=query, first=first, all_page=all_page)
        get_details = self.__scrap.get_detail_search(_search)
        return ItemList(data=get_details)