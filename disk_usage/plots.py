

## Example: https://hellodash.pythonanywhere.com/
## Cheatsheet: https://dashcheatsheet.pythonanywhere.com/

import os
import requests
from html.parser import HTMLParser
from dash import Dash, dcc, html, dash_table, Input, Output, callback
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

from disk_usage.reporting import * ## <== Stop being lazy


def card_contrainer(header, value, footer=None):
    style_header = dict(textAlign='center', fornSize='150%')
    style_body = dict(textAlign='center', fornSize='200%')
    card_header = dbc.CardHeader(header, style=style_header)
    card_body =  dbc.CardBody([
        html.H5(f'{value}',className='card-title', style=style_body),
        # html.P(
        #     f'ADD Footer text here {footer}', 
        #     className='cardText', style={'textAlign': 'centre'}
        # )
    ])
    return [card_header, card_body]

def disk_analyser(users: List[str]=None) -> px.sunburst:
    """
    A Sunburst plot that shows disk usage
    """
    sunburst_data, sb_col = folder_comp(users=users)
    fig = px.sunburst(
        sunburst_data, 
        path=sb_col,
        hover_data=['Size_GB'],
        values='Size')
    return fig
    
def largest_dir_plot(users: List[str]=None):
    xlargest_dir_df =  x_largest_directories(users=users)
    xlargest_dir_df1 = xlargest_dir_df.copy()
    xlargest_dir_df['Size_si'] = xlargest_dir_df.Size.apply(human_readable_bytes)
    xlargest_dir_df1['Size_GB'] = (xlargest_dir_df1.Size/1024**3).round(2)
    xlargest_dir_fig  = px.bar(xlargest_dir_df1, x='ParentDir', y='Size_GB', color='User', 
                                title="20 Largest Directories", 
                                labels={
                                    "Size_GB": "Size (GB)",
                                    "ParentDir": "Directories"
                                } )

    # xlargest_dir_tab1 = dbc.Tab([dcc.Graph(id='xlagest-dir', figure=xlargest_dir_fig)], label='Chart')
    # xlargest_dir_tab2 = dbc.Tab([make_table(xlargest_dir_df, '_xlargest-dir-table')], label='Table')
    return xlargest_dir_fig, make_table(xlargest_dir_df, '_xlargest_dir_table')

def sum_file_types_plot(users: List[str]=None):
    sum_file_types_df = sum_file_types(users=users)
    sum_file_types_df['Size_GB']  = (sum_file_types_df.Size/1024**3).round(2)
    fig_sum  = px.bar(sum_file_types_df, x='FileType', y='Size_GB', 
                                title="File types - Total file size", 
                                labels={
                                    "Size_GB": "Size (GB)",
                                    "FileType": "File type"
                                } )

    fig_counts  = px.bar(sum_file_types_df.query('FileType != ""'), x='FileType', y='Count', 
                                title="File types - Count", 
                                labels={
                                    "FileType": "File type"
                                } )

    return fig_sum, fig_counts, make_table(sum_file_types_df, '_file-type-table')

def user_usage_plot(users):
    df = user_usage_df(users=users)
    fig = px.pie(
        data_frame=df, 
        values='Size', 
        names='User', 
        title='Total Disks usage by user!')
    # df['Percentage'] = df.groupby('User')['Size'].sum()
    df['Size_si'] = df.Size.apply(human_readable_bytes)
    fig.update_traces(textinfo="percent").update_layout(title_x=0.5)
    return fig, make_table(df, 'user-usage-table')

def oldest_file_plot(users: List[str]=None):
    df = get_older_files(users=users)
    df['Path'] = df['ParentDir'] + "/"+ df['Filename']
    df['Size_si'] = df.Size.apply(human_readable_bytes)
    df.drop(['ParentDir', 'Filename'], axis =1, inplace=True)
    year_df = df.groupby('Year')['Size'].sum()
    year_df =year_df.reset_index()
    year_df['Size_si'] = year_df['Size'].apply(human_readable_bytes)
    year_df['Size_GB'] = year_df['Size']/1024**3
    
    fig = px.bar(year_df, x='Year', y='Size_GB',
                    title="Size of files by year", 
                    labels={
                        "Size_GB": "Size (GB)",
                    } ) 
    return fig, make_table(df, 'oldest-files')

def largest_files(users: List[str]):
    df = top_x_largest_files(users=users)
    df1 = df.copy()
    df1['Size_GB'] = df1.Size/1024**3 
    fig  = px.bar(
        df1, 
        x='Filename', 
        y='Size_GB',
        color='User', 
        title="20 Largest Files", 
        labels={
            "Size_GB": "Size (GB)",
            "Filename": "" } )
    dtable = make_table(df, 'largest-files-table_')
    return fig, dtable
