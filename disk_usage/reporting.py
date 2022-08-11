

from disk_usage.disk_usage import *
import pandas as pd


def human_readable_bytes(size: float) -> str:
    """convert bites to human readable format"""
    power = 1024
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]+'b'}"


# https: // stackoverflow.com/questions/1052148/group-by-count-function-in-sqlalchemy
# session.query(Table.column, func.count(
#     Table.column)).group_by(Table.column).all()

# statement = select([
#     readerBook.c.reader_status, func.count(readerBook.c.book_id).label("count")
# ])
# .select_from(readerBook)
# .group_by(readerBook.c.reader_id)
def total_folder_size(savepath: str=None):
    """
    Print table with parent folder, num files, aggrated files size in Gb 
    ## TODO: Add export to csv or dashboard
    """
    with Session(engine) as session:
        # myquery = select(FileStats.file_size).where(
        #     FileStats.is_file == 1)#.group(FileStats.parent)

        # results = session.exec(myquery).all()

        # print(results)
        # console.print(f'Total size: [red]{sum(results)/1024**3:.0f}Gb[/red]')

        filecount_size = session.exec(
            select(
                FileStats.parent,
                func.count(FileStats.parent).label('Count'), 
                func.sum(FileStats.file_size).label('Total') #/1024**3  ## in Gb
                ).where(FileStats.is_file == 1).group_by(FileStats.parent)
            ).all()

        table = Table()
        header = ['Folder', 'Count', "TotalSize"]
        for col in header:
            table.add_column(col, style='cyan')
        for res in filecount_size:
            table.add_row(*list(map(str, [*res[:2], human_readable_bytes(res[2])])))
        console.print(table)
        
        if savepath:
            df = pd.DataFrame(filecount_size, columns=header)   
            df.to_csv(savepath, index=False)


def top_x_largest_files(head: int):
    """
    print the largest 20 files
    Args:
        head: top X largest files to show
    """
    pass     


def top_x_largest_directies(head: int):
    """
    print the largest 20 directies
    Args:
        head: top X largest directies to show
    """
    pass   

def user_usage():
    """Total usage by users"""
    ## Groupby users count, sum
    pass

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
    pass