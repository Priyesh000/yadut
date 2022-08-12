from disk_usage.disk_usage import Console, Table, Optional
import pandas as pd


def df2table(
    df: pd.DataFrame,
    rich_table: Table,
    show_index: bool = True,
    index_name: Optional[str] = None,
    human_readable: Optional[str] =None
) -> Table:
    """Convert a pandas.DataFrame obj into a rich.Table obj.

    Args:
        df (DataFrame): A Pandas DataFrame to be converted to a rich Table.
        rich_table (Table): A rich Table that should be populated by the DataFrame values.
        show_index (bool): Add a column with a row count to the table. Defaults to True.
        index_name (str, optional): The column name to give to the index column. Defaults to None, showing no value.
        human_readable (str, optional): Columns name of columns to convert number to human readable format (e.g., 1Kb 234Mb 2Gb)
    Returns:
        Table: The rich Table instance passed, populated with the DataFrame values."""
    df1 = df.copy()
    if show_index:
        index_name = str(index_name) if index_name else ""
        rich_table.add_column(index_name)

    for column in df1.columns:
        rich_table.add_column(str(column), style='cyan')

    if human_readable:
        df1[human_readable] = df1[human_readable].apply(lambda x: human_readable_bytes(x))
    for index, value_list in enumerate(df1.values.tolist()):
        row = [str(index)] if show_index else []

        row += [str(x) for x in value_list]
        rich_table.add_row(*row)
    return rich_table


def human_readable_bytes(size: float) -> str:
    """Convert bites to human readable format

    Args:
        size (float): A floating/interage number to converted to human readable number (str) 
    Returns:
        str: human readable number 
    """
    power = 1024
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]+'b'}"
