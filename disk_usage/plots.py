

# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# import dash
# import dash_core_components as dcc
# import dash_html_components as html
# from dash.dependencies import Input, Output


## Example: https://hellodash.pythonanywhere.com/
## Cheatsheet: https://dashcheatsheet.pythonanywhere.com/
from cProfile import label
from dash import Dash, dcc, html, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import plotly.express as px
import pandas as pd
from disk_usage.reporting import * ## <== Stop being lazy



df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/c78bf172206ce24f77d6363a2d754b59/raw/c353e8ef842413cae56ae3920b8fd78468aa4cb2/usa-agricultural-exports-2011.csv')

##Callbacks:
## https://dash.plotly.com/advanced-callbacks

def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])

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
    )
    return table 

## make it shine
# path=['day', 'time', 'sex'], values='total_bill

# sunburst_data, sb_col = folder_comp()

# sunburst_data.to_csv('sunburst.tsv')
# disk_stur_fig = px.sunburst(sunburst_data.head(100), path=[sb_col[:2]], values='Size')

# disk_stur_fig.show()



# tab1 = dbc.Tab([dcc.Graph(id="line-chart")], label="Line Chart")
# tab2 = dbc.Tab([dcc.Graph(id="scatter-chart")], label="Scatter Chart")


def dashing_board():

    xlargest_dir_df =  x_largest_directories()
    xlargest_dir_df1 = xlargest_dir_df.copy()
    xlargest_dir_df['Size_si'] = xlargest_dir_df.Size.apply(human_readable_bytes)
    xlargest_dir_df1['Size_GB'] = (xlargest_dir_df1.Size/1024**3).round(2)
    xlargest_dir_fig  = px.bar(xlargest_dir_df1, x='ParentDir', y='Size_GB', color='User', 
                                title="20 Largest Directories", 
                                labels={
                                    "Size_GB": "Size (GB)",
                                    "ParentDir": "Directories"
                                } )

    xlargest_dir_tab1 = dbc.Tab([dcc.Graph(id='xlagest-dir', figure=xlargest_dir_fig)], label='Chart')
    xlargest_dir_tab2 = dbc.Tab([make_table(xlargest_dir_df, 'xlargest-dir-table')], label='Table')
    xlargest_dir_tabs = dbc.Tabs([xlargest_dir_tab1, xlargest_dir_tab2])


    sum_file_types_df = sum_file_types()
    sum_file_types_df['Size_GB']  = (sum_file_types_df.Size/1024**3).round(2)
    sum_file_types_size_fig  = px.bar(sum_file_types_df, x='FileType', y='Size_GB', 
                                title="File types - Total file size", 
                                labels={
                                    "Size_GB": "Size (GB)",
                                    "FileType": "File type"
                                } )

    sum_file_types_count_fig  = px.bar(sum_file_types_df, x='FileType', y='Count', 
                                title="File types - Count", 
                                labels={
                                    "FileType": "File type"
                                } )


    sum_file_types_tab1 = dbc.Tab(
        [dcc.Graph(id="file-type-sum", figure=sum_file_types_size_fig)],
        label="File Size")
    sum_file_types_tab2 = dbc.Tab(
        [dcc.Graph(id="file-type-count",figure=sum_file_types_count_fig)],
        label="File Count")
    sum_file_types_tab3 = dbc.Tab(
        [make_table(sum_file_types_df, 'file-type-table')], 
        label="Table", className="p-4")
    file_types_tabs = dbc.Tabs([sum_file_types_tab1, sum_file_types_tab2, sum_file_types_tab3])


    # stylesheet with the .dbc class
    dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])

    header = html.H4(
        "Disk Utilisation", className="bg-primary text-white p-2 mb-2 text-center"
    )

    colors = {
        'background': '#111111',
        'text': '#7FDBFF'
    }


    user_usage_df = user_usage()
    users_fig = px.pie(
        data_frame=user_usage_df, 
        values='Size', 
        names='User', 
        title='Total Disks usage by user!')
    user_usage_df['Size'] = user_usage_df.Size.apply(human_readable_bytes)

    older_files_df = older_files()
    older_files_df['Path'] = older_files_df['ParentDir'] + "/"+ older_files_df['Filename']
    older_files_df['Size'] = older_files_df.Size.apply(human_readable_bytes)
    older_files_df.drop(['ParentDir', 'Filename'], axis =1, inplace=True)
    older_file_table = make_table(older_files_df, 'oldest-files-table ')

    app.layout = dbc.Container([
        header,
        # html.H1(
        #     children='Disk Usage', 
        #     style={
        #         'textAlign': 'center',
        #         'color': colors['text']
        #     }),

        dbc.Row([
            html.H5('User Utilisation', 
                className="p-2 mb-2 text-center")
        ]),
        
        dbc.Row([ 
            dbc.Col([
                dcc.Graph(id='user-pie', figure=users_fig),
                # generate_table(user_usage_df),

            ], width=6,
            style={"width": "600px", "margin-left": 10},
            ),
            
            dbc.Col([
                make_table(user_usage_df, 'users-table'),
            ], width=6,
            style={
                "width": "400px",
                "margin-left":10,
                "margin-top": 50
                }
            ),

        ], justify="center"),
    ## largest dir
    dbc.Row([
        html.H5('20 largest Directories', 
            className="p-2 mb-2 text-center")
        ]),
    dbc.Row([ 
        dbc.Col([xlargest_dir_tabs], width=12)
        # dbc.Col([
        #     dcc.Graph(id='xlagest-dir', figure=xlargest_dir_fig)], width=6
        # ), 
        # dbc.Col([
        #     make_table(xlargest_dir_df, 'xlargest-dir-table')], width=5)
    ]),
    ## 
    dbc.Row([
        html.H5('Largest files types', 
            className="p-2 mb-2 text-center")
        ]),
    dbc.Row([
        dbc.Col([file_types_tabs], width=12),
    ]),
    dbc.Row([
        html.H5('Oldest files', 
            className="p-2 mb-2 text-center")
        ]),
    dbc.Row([
        older_file_table], 
            align='centre'),
        #style={"font-family": "Arial", "font-size": "0.9em", "text-align": "center"},

    ])
    return app
# app = Dash(__name__)

# 

# # assume you have a "long-form" data frame
# # see https://plotly.com/python/px-arguments/ for more options
# df = pd.DataFrame({
#     "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
#     "Amount": [4, 1, 2, 2, 4, 5],
#     "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
# })

# fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

# fig.update_layout(
#     plot_bgcolor=colors['background'],
#     paper_bgcolor=colors['background'],
#     font_color=colors['text']
# )

# app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
#     html.H1(
#         children='Hello Dash',
#         style={
#             'textAlign': 'center',
#             'color': colors['text']
#         }
#     ),

#     html.Div(children='Dash: A web application framework for your data.', style={
#         'textAlign': 'center',
#         'color': colors['text']
#     }),

#     dcc.Graph(
#         id='example-graph-2',
#         figure=fig
#     )
# ])

if __name__ == '__main__':
    dashing_board().run_server(debug=True)