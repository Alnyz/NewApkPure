from concurrent.futures import ThreadPoolExecutor
from threading import RLock as TRLock
from tqdm.auto import tqdm
from functools import partial
import base64
import os
import pathlib
from urllib.parse import unquote

class Download(object):
    def __init__(self, api) -> None:
        self.api = api

    def progress(self, r):
        fname = unquote(r.url).split('p=')[-1].split('&')[0].rstrip('=')
        fname = base64.b64decode(fname + '==').decode()
        fname = fname.replace('.', '_') + '.apk'
        path = pathlib.Path(str(self.api.temp_path).removesuffix('/') + '/apps/')
        path.mkdir(mode=os.O_WRONLY, parents=True, exist_ok=True)
        f = path / fname
        with tqdm.wrapattr(
            f.open("wb"), "write",
            desc=fname.split('.')[0],
            unit='B', unit_scale=True, unit_divisor=1024, miniters=1,
            total=int(r.headers.get('content-length', 0))
        ) as fout:
            for chunk in r.iter_content(chunk_size=4096):
                if not chunk:
                    break
                fout.write(chunk)
                
    def putjob(self, __data) -> None:
        # TODO: Make download in chunk
        vals = __data.reindex(columns=['download_url']).values
        val = [y for i in vals for y in i]
        reqs = self.api._Api__connection.create_connections(val, stream=True)
        tqdm.set_lock(TRLock())
        with ThreadPoolExecutor(thread_name_prefix='dl_worker') as p:
            p.map(partial(self.progress), reqs)
