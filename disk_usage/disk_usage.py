
from pathlib import Path
import time
# import pandas as pd
import os
import sys
from rich.console import Console
from rich.table import Table
from timeit import default_timer as timer
from datetime import timedelta

from loguru import logger
from typing import List, Dict, Optional, Union, Tuple

# from queue import Queue
# from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue

from sqlmodel import Session
from sqlalchemy import select, func

from functools import partial
from datetime import datetime
import re

from .checksum import filehash
from .model import FileStats, engine, create_db_and_tables


console = Console()

# d = Path('/Users/prughani/Downloads')
d = '../test'


# logger.remove()

def add_db(results: List[FileStats], engine: engine) -> None:
    logger.debug(f'number of iteams in results {len(results)}')
    if len(results)>1:
        with Session(engine) as db:
            db.add_all(results)
            db.commit()

def convert_datetime(isotime):

   return datetime.fromtimestamp(isotime)


def file_info(f: Path, hasher: Union[None, filehash]) -> FileStats:
    
    stat = f.stat()
    fhash  = -1 ## default checksum values
    if hasher and f.is_file(): ## is
        fhash = hasher(str(f)) ## Get the hash of file
    res = dict(
        filename=f.name, file_size=stat.st_size, user=f.owner(), ctime=stat.st_ctime, 
        mtime=stat.st_mtime, parent=str(f.parent), file_suffix=f.suffix, is_file=f.is_file(), 
        filepath=str(f.resolve()), checksum=fhash)
    # logger.debug(f'Filestats: {res}')
    info = FileStats(**res)
    return info

def add_to_q(queue: Queue, path: Union[str, list]) -> None:
    """Add the directory or list of directories to the Queue"""
    if isinstance(path, list):
        for directory in path:
            queue.put(Path(directory))
    else:
        queue.put(Path(path))

def exclude_pattern(patterns: List[str]) -> re.compile:
    """
    Use regex to rejects to exclude files 
    """
    ##TODO: if slow, try: https://stackoverflow.com/questions/42742810/speed-up-millions-of-regex-replacements-in-python-3
    patt = '|'.join(patterns)
    logger.info(f'Excluding: {patt}')
    return re.compile(f"({patt})")

@logger.catch()
def iter_dir(queue: Queue, hasher: bool, exclude_regex: re.compile, exclude: Tuple[str]) -> None:
    """Iterate over the files in a directory. If a directory is encountered add it to the queue"""
    while True:
        if queue.empty():
            logger.debug('Queue empty, breaking out of loop')
            break
        directory = queue.get()
        if directory is None:
            break
            # return None
        if not directory.exists():
            ## in cases with file is deleted before reading
            logger.warning(f'Directory Not Found: {directory}')
            continue
        if not exclude is None:
            if directory.resolve() in exclude:
                logger.info(f'Excluded directory: {directory}')
                continue
        results = []
        for f in directory.iterdir():
            logger.debug(f)
            
            if not os.access(f, os.R_OK):
                logger.warning(f'No Read permission: {f}')
                continue
            try: ## TODO: I should remove this try-except block now that Read check is done first
                if f.is_symlink():
                    logger.debug(f'Symlink not followed:{f}')
                    continue
            except:
                logger.warning("Permission denied: {f}")
            if not exclude_regex is None:
                if exclude_regex.match(str(f)):
                    logger.debug(f'Excluding: {f}')
                    continue
            if f.is_dir():
                add_to_q(queue, f)
                logger.info(f'{f} added to Queue')
            if not f.exists():
                ## in cases with file is deleted before reading
                logger.warning(f'File Not Found: {f}')
                continue
            try:
                stats = file_info(f, hasher)
                results.append(stats)
            except:
                logger.warning(f'PermissionError {f}')
        # logger.debug(f'Results: {results}')
        add_db(results, engine)

def worker(threads, queue, **kwargs) -> List[Process]:
    workers = []
    iter_dir_p = partial(iter_dir, **kwargs)
    for _  in range(threads):
        w = Process(target=iter_dir_p, args=((queue),))
        # w.daemon = True
        w.start()
        # w.join()
        workers.append(w)
        time.sleep(5) ## give a time for queue to fill up
        
    return workers

def howlong(func):
    """A simply decorator to time functions"""
    def _inner(*args, **kwargs):
        start = timer()
        res = func(*args, **kwargs)
        end = timer()
        console.print(func.__name__, timedelta(seconds=end-start))
        return res
    return _inner



"""user 10.12s system 31% cpu 46.239 total 1thread
4.37s user 10.32s system 37% cpu 38.703 total 4 thread

1.07s user 0.26s system 59% cpu 2.237 total ##  4 thread NO checksum
4.46s user 10.21s system 32% cpu 45.022 total ## 1 thread Checksum Whole file
3.51s user 7.34s system 15% cpu 1:11.27 total ## 1 thread Checksum Jump 1
3.84s user 8.21s system 14% cpu 1:24.23 total ## 8 threas Checksum Jump
3.07s user 6.28s system 22% cpu 41.707 total
0.59s user 0.12s system 4% cpu 17.277 total ## 8 threas No Checksum
0.48s user 0.10s system 20% cpu 2.887 total ## 1 threads No Checksum

3.04s user 7.62s system 8% cpu 2:00.40 total ## 1 threads Checksum Jump
2.67s user 6.35s system 8% cpu 1:45.00 total ## 8 thread checksum Jump
"""
        



# def iterrate_dir(path: Path):
#     for i in path.iterdir():
#         if i.is_file():
#             yield i 
#         else:
#             print('is_dir',i)
#             yield iterrate_dir(i)
    
