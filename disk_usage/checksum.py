
import xxhash
from pathlib import Path
import os
from loguru import logger
from typing import Union


def filehash(filepath: Union[Path, str], blocksize: int = 1048576, maxbytes: int = None, hasher: xxhash = xxhash.xxh64, skipblocks: int = 0) -> Union[str, int]:
    """
    Obtain a Non-cryptographic checksum of the file.
    Args:
        filepath: Path to file
        blocksize: blocksize to read in chunks. default(1048576)
        maxbytes: Maximum number of bytes read for the start of the file
        hasher: hashing library to use: Given as object
        jump: skipping the number of blocks - (blocksize * jump). 
            This will read portions of the file to speed up hashing but will read the whole files
    Return:
        If filepath is directorty return -1
        If no primission return 0
        return: disgested hash
    """
    fpath = Path(filepath)
    if not fpath.exists() or fpath.is_dir():
        logger.debug(f'{filepath} is directory. Can not be hashed!')
        return -1
    if not os.access(filepath, os.R_OK):
        logger.warning(f'No read access: {filepath}')
        return 0 
    hasher = hasher()
    with open(filepath, 'rb') as fh:
        buffer = fh.read(blocksize)
        remaining_bytes = maxbytes
        total_bytes = 0
        if maxbytes is None and skipblocks == 0:
            logger.debug('Reading the whole read mode')
            ## read the whole file
            while len(buffer) > 0:
                hasher.update(buffer)
                buffer = fh.read(blocksize)

        elif skipblocks > 0:
            ## Skipping blocks
            logger.debug('Skipping blocks mode')
            while len(buffer) > 0:
                # c += 1
                hasher.update(buffer)
                fh.seek((blocksize * skipblocks), 1)
                buffer = fh.read(blocksize)
                # print(len(buffer),c)

        elif maxbytes >0:
            logger.debug('Hashing maxbytes mode')
            ## Keep reading file until no remaining_bytes
            while len(buffer) > 0 and remaining_bytes > 0: ## 
                buffer = buffer[:remaining_bytes]
                remaining_bytes -= len(buffer)
                hasher.update(buffer)
                if remaining_bytes > 0:
                    buffer = fh.read(blocksize)


    return hasher.hexdigest()

            
