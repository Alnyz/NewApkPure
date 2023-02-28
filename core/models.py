from pydantic import BaseModel
from typing import List
import pandas as pd


class ItemList(pd.DataFrame):
    def __init__(self, **pd_data) -> None:
        super().__init__(**pd_data)

    
class URLS(BaseModel):
    urls: list = List[str]