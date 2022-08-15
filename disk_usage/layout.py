
from shutil import disk_usage
from symtable import SymbolTable
from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc
from disk_usage.reporting import x_largest_directories, sum_file_types
from disk_usage.plots  import *
from dash.exceptions import PreventUpdate


h3_header_style={
    'textAlign': 'center',
    'align':'center'
}

def card_contrainer(header, value, footer=None):
    style_header = dict(textAlign='center', fontSize='150%')
    style_body = dict(
        textAlign='center',
        fontSize='200%', 
        color='lightgrey')
    card_header = dbc.CardHeader(header, style=style_header)
    card_body =  dbc.CardBody([
        html.H5(f'{value}',className='card-title', style=style_body),
        html.P(
            f'ADD Footer text here {footer}', 
            className='cardText', style={'textAlign': 'centre'}
        )
    ])
    return [card_header, card_body]

def graph_contrainer(header, graph, width=12):
    dbc.Col([
            html.H3('File types'),
            
        ],width=6,style=h3_header_style)    

def selecting_options():

    headerstyle={'textAlign': 'center', 'fontSize': '100%'}
    bodystyle={'textAlign': 'center', 'fontSize': '75%', 
        # 'background-color':'lightgrey', 
        # 'border-style':'solid',
        # 'outline-color': 'blue',           
                }
    # header =dbc.CardHeader('Option',style=headerstyle)
    users_list, years_list = options_list()

    body = dbc.CardBody([
        html.Div([
            html.H6(['Options']),
            html.Br(),
            html.Label('Select Users'),
            dcc.Dropdown(users_list, multi=True, id='user-dropdown'),
            html.Br(),
            html.H6('Select years'),
            dcc.RangeSlider(
                # min=years_list[0],
                # max=years_list[-1],
                # step=1,
                marks={str(n):str(y) for n, y in enumerate(years_list)}
            ),
            html.Br(),
            html.Label('Minimum file size GB'),
            dcc.Slider(
                min=0,
                max=100,
                value=5,
                tooltip={"placement": "bottom", "always_visible": True}), 
                # style={
                #     # 'display': 'flex', 
                #     'flex-direction': 'row'
                # }
            dbc.Row([
                html.Br(),
                dbc.Col([
                    html.Button('Save offline', id='save', n_clicks=0),
                    html.Span('', id='saved')
                ], style={'align': 'left'}),
        ])]
                )
    ],style=bodystyle)
    return [body]

def dashingboard():
    dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])
    server = app.server
    app.layout = html.Div([
        dbc.Row([
            html.H1('Disk Anaylzer', 
                style={
                    'textAlign': 'center',
                    'fontSize': '200%'}),
            html.Br()
        ]),
        ## -- Total Disk user card -- ##
        dbc.Row([
            dbc.Col(selecting_options(),
            width=4),
            dbc.Col(card_contrainer('Total Disk usage', 'XXX Tb'),
            width=4),
            ]),
        ## -- File Type -- ##
        dbc.Row([
            ## -- Odest File -- ##
            dbc.Col([
                html.H3('Oldest files'),
                dbc.Tabs([
                    dbc.Tab(dcc.Graph(id='oldest-files-fig'), label='Chart'),
                    dbc.Tab(id='oldest-files-table',label='Table')
                ]),
            ],width=4,style=h3_header_style),
            ## -- User -- ##
            dbc.Col([
                html.H3('Users'),
                dbc.Tabs([
                    dbc.Tab(dcc.Graph(id='user-usage-fig'), label='Chart'),
                    dbc.Tab(id='user-usage-table',label='Table')
                ]),
                
            ],width=6, style=h3_header_style)
    
        ]),
        dbc.Row([
            ## -- Largest File -- ##
            html.H3('Largest files'),
            dbc.Tabs([
                dbc.Tab(dcc.Graph(id='largest-files-fig'), label='Chart'),
                dbc.Tab(id='largest-files-table',label='Table')
                ]),

        ], style=h3_header_style),
        dbc.Row([
            html.H3('File types'),
                dbc.Tabs([
                    dbc.Tab([
                        dcc.Graph(id="file-type-sum-fig")], label="File Size"),
                    dbc.Tab([
                        dcc.Graph(id="file-type-counts-fig")],label='File Counts'),
                    dbc.Tab(id='file-type-table',label="Table", className="p-4")
                    ]),

        ], style=h3_header_style),
        dbc.Row([
            ## -- Largest  directories
            html.H3('Largest directories'),
            dbc.Tabs([
                dbc.Tab([
                    dcc.Graph(id='xlargest-dir-fig')],label="Chart"),
                dbc.Tab(id='xlargest-dir-table', label='Table')
            ])
        ], style=h3_header_style),
        ## -- Disk exploser -- ##
        dbc.Row([
            html.H3('Disk Explorer'),
            dcc.Graph(id='disk-anaylser-fig')
        ], style=h3_header_style)

        ], style={
            'padding': 20,
            'margin-left': 25,
            'margin-top': 10,
            'margin-bottom': 10,
            'margin-left': 25,
            'margin-right': 25,
            'align': 'centre', 
            # 'border-style':'solid',
            'outline-color': 'lightgrey'}
            )

        ## -- End --


    @app.callback(
        Output('saved', 'children'),
        Input('save', 'n_clicks'),
        )
    def save_result(n_clicks):
        if n_clicks == 0:
            return 'not saved'
        else:
            make_static(f'http://127.0.0.1:8050/')
            return 'saved'

    @app.callback([
        Output(component_id='largest-files-fig', component_property='figure'),
        Output(component_id='largest-files-table', component_property='children')],
        Input(component_id='user-dropdown', component_property='value'),
        prevent_initial_call=False)
    def callback_largest_files(users):
        # if users is  None:
        #     raise PreventUpdate
        fig, dtable = largest_files(users=users)
        return fig, dtable

    @app.callback([
        Output(component_id='user-usage-fig', component_property='figure'),
        Output(component_id='user-usage-table', component_property='children')],
        Input(component_id='user-dropdown', component_property='value'),
        prevent_initial_call=False)
    def callback_user_usage(users):
        fig, dtable  = user_usage_plot(users)
        return fig, dtable


    @app.callback([
        Output(component_id='file-type-sum-fig', component_property='figure'),
        Output(component_id='file-type-counts-fig', component_property='figure'),
        Output(component_id='file-type-table', component_property='children')],
        Input(component_id='user-dropdown', component_property='value'),
        prevent_initial_call=False)
    def callback_user_usage(users):
        fig_sum,fig_count, dtable  = sum_file_types_plot(users)
        return fig_sum,fig_count, dtable


    @app.callback([
        Output(component_id='oldest-files-fig', component_property='figure'),
        Output(component_id='oldest-files-table', component_property='children')],
        Input(component_id='user-dropdown', component_property='value'),
        prevent_initial_call=False)
    def callback_oldest_files(users):
        fig, dtable  = oldest_file(users)
        return fig,dtable

    @app.callback(
        Output(component_id='disk-anaylser-fig', component_property='figure'),
        Input(component_id='user-dropdown', component_property='value'),
        prevent_initial_call=False)
    def callback_disk_analyser(users):
        return disk_analyser(users)

    @app.callback([
        Output(component_id='xlargest-dir-fig', component_property='figure'),
        Output(component_id='xlargest-dir-table', component_property='children')],
        Input(component_id='user-dropdown', component_property='value'),
        prevent_initial_call=False)
    def callback_largest_directories(users):
        fig, dtable  = largest_dir_plot(users)
        return fig, dtable

    return app
   
    