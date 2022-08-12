

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
from dash import Dash, dcc, html, dash_table, Input, Output, callback
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import plotly.express as px
import pandas as pd
from reporting import * ## <== Stop being lazy



df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/c78bf172206ce24f77d6363a2d754b59/raw/c353e8ef842413cae56ae3920b8fd78468aa4cb2/usa-agricultural-exports-2011.csv')



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

   dbc.Row([
          html.H5('Largest files types', 
            className="p-2 mb-2 text-center")
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
    app.run_server(debug=True)