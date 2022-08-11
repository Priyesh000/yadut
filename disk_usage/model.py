# from dataclasses import dataclass
# https: // docs.sqlalchemy.org/en/14/orm/tutorial.html

from typing import Optional, Union
from sqlmodel import Field, SQLModel, create_engine


class FileStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) ## ToDo: make id a checksum value 
    filename: str
    file_size: Optional[int] = None ## a folder could have a 0 size
    user: Optional[str] = None
    ctime: float
    mtime: float
    parent: Optional[str] = None
    file_suffix: Optional[str] = None 
    is_file: bool
    filepath: str
    checksum: Optional[str] = None ## useful for finding duplicated files

    def add_checksum(self, checksum):
        self.checksum = checksum


sqlite_file_name = "database2.db"  ## TODO: add to config file
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables(if_exists='replace') -> None:
    """ 
    if_exists : {'fail', 'replace', 'append'}, default 'fail'
        - fail: If table exists, do nothing.
        - replace: If table exists, drop it, recreate it, and insert data.
        - append: If table exists, insert data. Create if does not exist.
    """
    options = ['replace', 'append']
    ## defualt is append 
    if not if_exists.lower() in options:
        raise ValueError(f'{if_exists} is not valid for if_exists. Select from {options}')
    if if_exists == 'replace':
        SQLModel.metadata.drop_all(engine)
    if if_exists == 'fail':
        # SQLModel.metadata.is_bound()
        ## TODO: If table exists, do nothing.
        ## handle by the create_al
        pass 
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    """If the model.py is run then it will create all tables but not automatically if imported"""
    create_db_and_tables('append')

#