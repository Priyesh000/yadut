
import pandas as pd
# from sqlalchemy import desc, intersect
from datetime import datetime

from disk_usage.util import *
from disk_usage.disk_usage import *
from sqlmodel import desc, and_, or_, intersect_all, intersect, col, select, func

# https: // stackoverflow.com/questions/1052148/group-by-count-function-in-sqlalchemy
# session.query(Table.column, func.count(
#     Table.column)).group_by(Table.column).all()

# statement = select([
#     readerBook.c.reader_status, func.count(readerBook.c.book_id).label("count")
# ])
# .select_from(readerBook)
# .group_by(readerBook.c.reader_id)

def total_folder_size(savepath: str=None, users: List[str]=None) -> pd.DataFrame:
    """
    Print table with parent folder, num files, aggrated files size in Gb 
    ## TODO: Add export to csv or dashboard
    """

    ## in_ clause: https://github.com/tiangolo/sqlmodel/issues/294#issuecomment-1133493088

    if users:
        myquery = (
            select(
                FileStats.parent,
                func.count(FileStats.parent).label('Count'), 
                func.sum(FileStats.file_size).label('Total') #/1024**3  ## in Gb
                ).where(FileStats.is_file == 1).where(col(FileStats.user).in_(users))
                .group_by(FileStats.parent)
        )
    else:
        myquery = (
            select(
                FileStats.parent,
                func.count(FileStats.parent).label('Count'), 
                func.sum(FileStats.file_size).label('Total') #/1024**3  ## in Gb
                ).where(FileStats.is_file == 1).group_by(FileStats.parent)
        )

    with Session(engine) as session:

        filecount_size = session.exec(myquery).all()

        table = Table()
        header = ['Folder', 'Count', "Size"]
        for _column in header:
            table.add_column(_column, style='cyan')
        for res in filecount_size:
            table.add_row(*list(map(str, [*res[:2], human_readable_bytes(res[2])])))
        console.print(table)
        
        df = pd.DataFrame(filecount_size, columns=header)   
        if savepath:
            df.to_csv(savepath, index=False)
    return df

def x_largest_directories(head: int=20, users: List[str]=None) -> pd.DataFrame:
    """
    print the largest 20 files

    Args:
        head (int=20): Top X largest directories to show
    Returns: 
        return (pd.DataFrame): Ordered by Size in desc [User, ParentDir, Count, Size(bites)]
    """

    if users:
        myquery=(select(
                        FileStats.user,
                        FileStats.parent,
                        func.count(FileStats.parent).label('Count'), 
                        func.sum(FileStats.file_size).label('Size')
                        ).where(FileStats.is_file==1).where(col(FileStats.user).in_(users))
                        .group_by(FileStats.parent)
                        .order_by(desc('Size'))
                        .limit(head)
                    )
    else:
        myquery =(select(
                        FileStats.user,
                        FileStats.parent,
                        func.count(FileStats.parent).label('Count'), 
                        func.sum(FileStats.file_size).label('Size')
                        ).where(FileStats.is_file==1)
                        .group_by(FileStats.parent)
                        .order_by(desc('Size'))
                        .limit(head)
                    )
    with Session(engine) as session:
        results = session.exec(myquery).all()
    df=  pd.DataFrame(results, columns=['User', 'ParentDir', 'Count',  "Size"])
    # table = Table()
    # console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df

def top_x_largest_files(head: int=20, users: List[str]=None) -> pd.DataFrame:
    """
    print the largest 20 file
    Args:
        head (int=20): top X largest files to show
    Returns: 
        return (pd.DataFrame): Ordered by Size in desc [User, ParentDir, Filename, Size(bites)]
    """
    if users:
        myquery = (select(
                        FileStats.user,
                        FileStats.parent,
                        FileStats.filename,
                        FileStats.file_size)
                        .where(FileStats.is_file==1).where(col(FileStats.user).in_(users))
                        .order_by(desc(FileStats.file_size))
                        .limit(head))
    else:
        myquery = (select(
                        FileStats.user,
                        FileStats.parent,
                        FileStats.filename,
                        FileStats.file_size)
                        .where(FileStats.is_file==1)
                        .order_by(desc(FileStats.file_size))
                        .limit(head))

    with Session(engine) as session:
        results = session.exec(myquery).all()
    df= pd.DataFrame(results, columns=['User', 'ParentDir', 'Filename', "Size"])
    df['Size_si'] = df.Size.apply(human_readable_bytes)
    df['Filepath'] = df.ParentDir + "/" + df.Filename

    df.drop('ParentDir', axis=1,  inplace=True)
    # table = Table()
    # console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df

def sum_file_types(head: int=20, users: List[str]=None) ->pd.DataFrame:
    with Session(engine) as session:
        if users:
            myquery = (select(
                        FileStats.file_suffix,
                        func.count(FileStats.parent).label('Count'), 
                        func.sum(FileStats.file_size).label('Size')
                        ).where(FileStats.is_file==1).where(col(FileStats.user).in_(users))
                        .group_by(FileStats.file_suffix)
                        .order_by(desc('Size'))
                        .limit(head)
                    )
        else:
             myquery = (select(
                        FileStats.file_suffix,
                        func.count(FileStats.parent).label('Count'), 
                        func.sum(FileStats.file_size).label('Size')
                        ).where(FileStats.is_file==1)
                        .group_by(FileStats.file_suffix)
                        .order_by(desc('Size'))
                        .limit(head)
                    )

        results = session.exec(myquery).all()
    df=  pd.DataFrame(results, columns=['FileType', 'Count',  "Size"])
    
    # table = Table()
    # console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df    

def user_usage_df(users: List[str]=None):
    """Total usage by users"""
    ## Groupby users count, sum
    if users:
        myquery = (select(
                FileStats.user,
                func.count(FileStats.parent).label('Count'), 
                func.sum(FileStats.file_size).label('Size') #/1024**3  ## in Gb
                ).where(FileStats.is_file==1).where(col(FileStats.user).in_(users))
                .group_by(FileStats.user)
                .order_by(desc('Size'))
            )
    else:
        myquery = (
            select(
                FileStats.user,
                func.count(FileStats.parent).label('Count'), 
                func.sum(FileStats.file_size).label('Size') #/1024**3  ## in Gb
                ).where(FileStats.is_file==1)
                .group_by(FileStats.user)
                .order_by(desc('Size'))
            )

    with Session(engine) as session:
        results = session.exec(myquery).all()
    df=  pd.DataFrame(results, columns=['User', 'Count', "Size"])
    # total = df.groupby('User')['Size'].sum()

    # table = Table()
    # console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df
    
def duplicated_files():
    """
    Duplicated files
    ## Groupby checksum
    """
    """
    SELECT filename
    FROM filestats
    WHERE is_file == 1
    GROUP BY checksum
    ORDER BY count(*) DESC;
    """
    pass

def get_older_files(users: List[str]=None):
    """Show the oldest files with ctime"""

    if users:
        myquery = (
            select(
                    FileStats.ctime,
                    FileStats.user,
                    FileStats.filename,
                    FileStats.parent,
                    FileStats.file_size,
                ).where(FileStats.is_file==True).where(col(FileStats.user).in_(users))
                .order_by(desc(FileStats.file_size))
                .order_by(desc(FileStats.ctime))
                .limit(100)
            )
    else:
        myquery = (
            select(
                    FileStats.ctime,
                    FileStats.user,
                    FileStats.filename,
                    FileStats.parent,
                    FileStats.file_size,
                ).where(FileStats.is_file==True)
                .order_by(desc(FileStats.file_size))
                .order_by(desc(FileStats.ctime))
                .limit(100)
            )
    with Session(engine) as session:
        results = session.exec(myquery).all()
    df=  pd.DataFrame(results, columns=['Date', "User",'Filename', "ParentDir", "Size"])
    df['Date'] = df.Date.apply(lambda x: 
        datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M'))
    df["Date"] = pd.to_datetime(df.Date)
    df['Year'] = df["Date"].dt.year
    df = df.sort_values('Date')
    # table = Table()
    # console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df

def folder_comp(levels: int=4, users: List[str]=None) ->Tuple[pd.DataFrame, list]:
    """
    Folder for composition for sunburst plot
    
    Args: 
        levels (int=4): Directory levels to report as sunburst plot
    Returns:
        return list(df, list(colnames)): dataframe, list of columns as directory levels 
    """
    df = total_folder_size(users=users)
    df = df.drop('Count', axis=1)
    colnames  = [f'level_{i}' for i in range(levels+1)]
    df[colnames] = df.Folder.str.split('/', levels, expand=True)
    colnames.pop(0)
    df.drop('level_0', axis=1, inplace=True) ## dropped first col bacuase is blank 
    df1 = df.groupby(colnames)['Size'].sum().reset_index()
    df1['Size_GB'] = df.Size.apply(lambda x: x/1024 **3)
    df1 = df1.fillna('')
    return (df1, colnames)

def options_list()->Tuple[List[str],List[int]]:
    ""
    with Session(engine) as session:
        users = session.exec(
            select(col(FileStats.user).distinct()
            )).all()
        dates = session.exec(
            select(FileStats.ctime)
            ).all()

# datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M'))
    years = set(datetime.utcfromtimestamp(x).strftime('%Y') for x in dates)

    return (users, sorted(list(map(int,years))))


def export_table(users: List[str]=None) -> pd.DataFrame:

    if users:
        myquery = (
            select(
                    FileStats.ctime,
                    FileStats.mtime,
                    FileStats.user,
                    FileStats.parent,
                    FileStats.filename,
                    FileStats.file_size
                ).where(FileStats.is_file==True).where(col(FileStats.user).in_(users))
                .order_by(desc(FileStats.file_size))
                .order_by(desc(FileStats.ctime))
                # .limit(100)
            )
    else:
        myquery = (
            select(
                    FileStats.ctime,
                    FileStats.mtime,
                    FileStats.user,
                    FileStats.parent,
                    FileStats.filename,
                    FileStats.file_size,
                ).where(FileStats.is_file==True)
                .order_by(desc(FileStats.file_size))
                # .order_by(desc(FileStats.ctime))
                # .limit(100)
            )
    with Session(engine) as session:
        results = session.exec(myquery).all()
    
    df = pd.DataFrame(results, columns=['Ctime','Mtime', 'User', 'ParentDir', 'Filename', 'Size'])
    df['Size_si'] = df.Size.apply(human_readable_bytes)
    df['DateCreate'] = df.Ctime.apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M'))
    df['DateModified'] = df.Mtime.apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M'))
    df.drop(['Ctime', 'Mtime'], axis=1, inplace=True)
    return df
    
def report_mountpoint():
    with Session(engine) as session:
        myquery = (
            select(
                FileSystemUsage.mountpoint,
                FileSystemUsage.total,
                FileSystemUsage.used,
                FileSystemUsage.free
                )
        )
        results = session.exec(myquery).all()
    df = pd.DataFrame(results, columns=['MountPoint', 'Total', 'Used', 'Free'])
    df = df.sort_values('Used', ascending=False)
    df['%Used'] = df.apply(lambda x: f"{(100 * (x['Used']/x['Total'])):.2f}%", axis=1)
    for i in [ 'Total', 'Used', 'Free']:
        df[i] = df[i].apply(human_readable_bytes)
    return df
# if __name__ == "__main__":
    # user_usage()
    # older_files()
    # x_largest_directories()
    # folder_comp()