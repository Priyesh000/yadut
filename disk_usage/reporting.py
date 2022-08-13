

import pandas as pd
from sqlalchemy import desc 
from datetime import datetime

from disk_usage.util import *
from disk_usage.disk_usage import *



# https: // stackoverflow.com/questions/1052148/group-by-count-function-in-sqlalchemy
# session.query(Table.column, func.count(
#     Table.column)).group_by(Table.column).all()

# statement = select([
#     readerBook.c.reader_status, func.count(readerBook.c.book_id).label("count")
# ])
# .select_from(readerBook)
# .group_by(readerBook.c.reader_id)

def total_folder_size(savepath: str=None) -> pd.DataFrame:
    """
    Print table with parent folder, num files, aggrated files size in Gb 
    ## TODO: Add export to csv or dashboard
    """
    with Session(engine) as session:

        filecount_size = session.exec(
            select(
                FileStats.parent,
                func.count(FileStats.parent).label('Count'), 
                func.sum(FileStats.file_size).label('Total') #/1024**3  ## in Gb
                ).where(FileStats.is_file == 1).group_by(FileStats.parent)
            ).all()

        table = Table()
        header = ['Folder', 'Count', "Size"]
        for col in header:
            table.add_column(col, style='cyan')
        for res in filecount_size:
            table.add_row(*list(map(str, [*res[:2], human_readable_bytes(res[2])])))
        console.print(table)
        
        df = pd.DataFrame(filecount_size, columns=header)   
        if savepath:
            df.to_csv(savepath, index=False)
    return df

def x_largest_directories(head: int=20) -> pd.DataFrame:
    """
    print the largest 20 files

    Args:
        head (int=20): Top X largest directories to show
    Returns: 
        return (pd.DataFrame): Ordered by Size in desc [User, ParentDir, Count, Size(bites)]
    """
    with Session(engine) as session:
        results = session.exec(
                    (select(
                        FileStats.user,
                        FileStats.parent,
                        func.count(FileStats.parent).label('Count'), 
                        func.sum(FileStats.file_size).label('Size')
                        ).where(FileStats.is_file==1)
                        .group_by(FileStats.parent)
                        .order_by(desc('Size'))
                        .limit(head)
                    )
                    ).all()
    df=  pd.DataFrame(results, columns=['User', 'ParentDir', 'Count',  "Size"])
    table = Table()
    console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df

def top_x_largest_files(head: int=20) -> pd.DataFrame:
    """
    print the largest 20 file
    Args:
        head (int=20): top X largest files to show
    Returns: 
        return (pd.DataFrame): Ordered by Size in desc [User, ParentDir, Filename, Size(bites)]
    """
    with Session(engine) as session:
        results = session.exec(
                    (select(
                        FileStats.user,
                        FileStats.parent,
                        FileStats.filename,
                        FileStats.file_size) #/1024**3  ## in Gb
                        ).where(FileStats.is_file==1)
                        .order_by(desc('Size'))
                        .limit(head)
                    ).all()
    df=  pd.DataFrame(results, columns=['User', 'ParentDir', 'Filename' "Size"])
    table = Table()
    console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df

def sum_file_types(head: int=20):
    with Session(engine) as session:
        results = session.exec(
                    (select(
                        FileStats.file_suffix,
                        func.count(FileStats.parent).label('Count'), 
                        func.sum(FileStats.file_size).label('Size')
                        ).where(FileStats.is_file==1)
                        .group_by(FileStats.file_suffix)
                        .order_by(desc('Size'))
                        .limit(head)
                    )
                    ).all()
    df=  pd.DataFrame(results, columns=['FileType', 'Count',  "Size"])
    
    table = Table()
    console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df    

def user_usage():
    """Total usage by users"""
    ## Groupby users count, sum
    with Session(engine) as session:
        results = session.exec(
            (select(
                FileStats.user,
                func.count(FileStats.parent).label('Count'), 
                func.sum(FileStats.file_size).label('Size') #/1024**3  ## in Gb
                ).where(FileStats.is_file==1)
                .group_by(FileStats.user)
                .order_by(desc('Size'))
            )
        ).all()
    df=  pd.DataFrame(results, columns=['User', 'Count', "Size"])
    table = Table()
    console.print(df2table(df, table, show_index=False, human_readable='Size'))
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

def older_files():
    """Show the oldest files with ctime"""
    with Session(engine) as session:
        myquery = (select(
                    FileStats.mtime,
                    FileStats.user,
                    FileStats.filename,
                    FileStats.parent,
                    FileStats.file_size,
                ).where(FileStats.is_file==True)
                .order_by(desc(FileStats.file_size))
                .order_by(desc(FileStats.mtime))
                .limit(100)
            )
        results = session.exec(myquery).all()
    df=  pd.DataFrame(results, columns=['Date', "User",'Filename', "ParentDir", "Size"])
    df['Date'] = df.Date.apply(lambda x: 
        datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M'))
    df["Date"] = pd.to_datetime(df.Date)
    df = df.sort_values('Date')
    table = Table()
    console.print(df2table(df, table, show_index=False, human_readable='Size'))
    return df

def folder_comp(levels: int=4) ->Tuple[pd.DataFrame, list]:
    """
    Folder for composition for sunburst plot
    
    Args: 
        levels (int=4): Directory levels to report as sunburst plot
    Returns:
        return list(df, list(colnames)): dataframe, list of columns as directory levels 
    """
    df = total_folder_size()
    df = df.drop('Count', axis=1)
    colnames  = [f'level_{i}' for i in range(levels+1)]
    df[colnames] = df.Folder.str.split('/', levels, expand=True)
    colnames.pop(0)
    df.drop('level_0', axis=1, inplace=True) ## dropped first col bacuase is blank 
    df1 = df.groupby(colnames)['Size'].sum().reset_index()
    df1['Size_GB'] = df.Size.apply(lambda x: x/1024 **3)
    df1 = df1.fillna('')
    return (df1, colnames)


if __name__ == "__main__":
    # user_usage()
    # older_files()
    folder_comp()