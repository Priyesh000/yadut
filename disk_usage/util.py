from disk_usage.disk_usage import Console, Table, Optional
import pandas as pd
import os
from html.parser import HTMLParser
import requests
from dash import dash_table



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


def patch_file(file_path: str, content: bytes, extra: dict = None) -> bytes:
    """
    Patch HTML to save an office copy of the dashboard
    Sourced from: https://gist.github.com/exzhawk/33e5dcfc8859e3b6ff4e5269b1ba0ba4

    Args:
        filepath (str): output to index.html 
        content (bytes): html page
        extra (dict): addition script to embed into html  
    Returns:
        return (bytes): patched html 
    """

    if file_path == 'index.html':
        index_html_content = content.decode('utf8')
        extra_jsons = f'''
        var patched_jsons_content={{
        {','.join(["'/" + k + "':" + v.decode("utf8") + "" for k, v in extra.items()])}
        }};
        '''
        patched_content = index_html_content.replace(
            '<footer>',
            f'''
            <footer>
            <script>
            ''' + extra_jsons + '''
            const origFetch = window.fetch;
            window.fetch = function () {
                const e = arguments[0]
                if (patched_jsons_content.hasOwnProperty(e)) {
                    return Promise.resolve({
                        json: () => Promise.resolve(patched_jsons_content[e]),
                        headers: new Headers({'content-type': 'application/json'}),
                        status: 200,
                    });
                } else {
                    return origFetch.apply(this, arguments)
                }
            }
            </script>
            '''
        ).replace(
            'href="/',
            'href="'
        ).replace(
            'src="/',
            'src="'
        )
        return patched_content.encode('utf8')
    else:
        return content


def write_file(file_path: str, content: bytes, target_dir: str='target', ) -> None:
    """
    Write the pathed html file
    
    Args:
        file_path (str):
        content (bytes):
        target_dir (str): output folder
    Returns:
        return None
    """
    target_file_path = os.path.join(target_dir, file_path.lstrip('/').split('?')[0])
    target_leaf_dir = os.path.dirname(target_file_path)
    os.makedirs(target_leaf_dir, exist_ok=True)
    with open(target_file_path, 'wb') as f:
        f.write(content)
    pass

class ExternalResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources = []

    def handle_starttag(self, tag, attrs):
        if tag == 'link':
            for k, v in attrs:
                if k == 'href':
                    self.resources.append(v)
        if tag == 'script':
            for k, v in attrs:
                if k == 'src':
                    self.resources.append(v)


def make_static(base_url, target_dir='target'):
    index_html_bytes = requests.get(base_url).content
    json_paths = ['_dash-layout', '_dash-dependencies', ]
    extra_json = {}
    for json_path in json_paths:
        json_content = requests.get(base_url + json_path).content
        extra_json[json_path] = json_content

    patched_bytes = patch_file('index.html', index_html_bytes, extra=extra_json)
    write_file('index.html', patched_bytes, target_dir)
    parser = ExternalResourceParser()
    parser.feed(patched_bytes.decode('utf8'))
    extra_js = [
        '_dash-component-suites/dash/dcc/async-graph.js',
        '_dash-component-suites/dash/dcc/async-plotlyjs.js',
        '_dash-component-suites/dash/dash_table/async-table.js',
        '_dash-component-suites/dash/dash_table/async-highlight.js'
    ]
    for resource_url in parser.resources + extra_js:
        resource_url_full = base_url + resource_url
        print(f'get {resource_url_full}')
        resource_bytes = requests.get(resource_url_full).content
        patched_bytes = patch_file(resource_url, resource_bytes)
        write_file(resource_url, patched_bytes, target_dir)



##Callbacks:
## https://dash.plotly.com/advanced-callbacks

# def generate_table(dataframe, max_rows=10):
#     return html.Table([
#         html.Thead(
#             html.Tr([html.Th(col) for col in dataframe.columns])
#         ),
#         html.Tbody([
#             html.Tr([
#                 html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
#             ]) for i in range(min(len(dataframe), max_rows))
#         ])
#     ])

def make_table(df, iid):
    ##https://hellodash.pythonanywhere.com/adding-themes/datatable
    table = dash_table.DataTable(
    id=iid,
    columns=[{"name": i, "id": i, "deletable": True} for i in df.columns],
    data=df.to_dict("records"),
    page_size=10,
    editable=True,
    cell_selectable=True,
    filter_action="native",
    sort_action="native",
    style_table={"overflowX": "auto"},
    export_format="csv"
    )
    return table 