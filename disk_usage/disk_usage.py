
from pathlib import Path
import shutil
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

from sqlmodel import Session#, select, func, col, 
# from sqlalchemy import select, func

from functools import partial
from datetime import datetime
import re

from disk_usage.checksum import filehash
from disk_usage.model import FileStats, engine, create_db_and_tables, FileSystemUsage


console = Console()

# d = Path('/Users/prughani/Downloads')
d = '../test'
logger.remove()

def add_db(results: Union[List[FileStats], FileSystemUsage], engine: engine) -> None:
        commit =False
        with Session(engine) as db:
            if isinstance(results, FileSystemUsage):
                db.add(results)
                commit =True 
            elif isinstance(results, list) and len(results)>1:
                db.add_all(results)
                logger.debug(f'number of iteams in results {len(results)}') 
                commit =True 
            if  commit:        
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

def find_monutpoint(path: Union[str, Path])-> Path:
    """Finds mount point
    
    Args:
        path (str, Path): Path to directories
    Return:
        return (Path object): Path is reduced to the orignal mount point  
    """
    ## ref: https://stackoverflow.com/questions/4260116/find-size-and-free-space-of-the-filesystem-containing-a-given-file 

    path = Path(path).resolve()
    c =0
    while c< 20:
        if path.is_mount():
            return path
        path = path.parent
        c +=1
    return None 

def path_seen_before(current_path: str, previous_paths: List[str]):
    pass


def file_system_usage(path: Union[Path, str], engine)-> None:
    """Get the disk useage and add to db"""
    path = Path(path)
    if not path.exists():
        raise ValueError(f'{path}: Does not exists')
    if path.is_dir():
        # if any([]):
        mp =  find_monutpoint(path) 
        # seen.append(mp)
        if mp:
            logger.debug(f'Mount point {mp}')
            total, used, free = shutil.disk_usage(str(mp))
            logger.debug(f'Mount point {mp}, Total {total}, used {used}, free {free}')
            res  = FileSystemUsage(mountpoint=str(mp), total=total, used=used, free=free)
            add_db(res, engine)
        return res


    

def howlong(func):
    """A simply decorator to time functions"""
    def _inner(*args, **kwargs):
        start = timer()
        res = func(*args, **kwargs)
        end = timer()
        console.print(func.__name__, timedelta(seconds=end-start))
        return res
    return _inner
