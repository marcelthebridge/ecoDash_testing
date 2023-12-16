import dash
from dash import Dash, html, dcc, dash_table, callback, Input, Output, callback_context
from data_utils import *
from datetime import datetime, date, timedelta

dash.register_page(__name__, path="/internalFeed/")

ecosystems = get_ecosystems()
ecosystems = ecosystems.sort_values(by='ecosystem')


def layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='supa-data'),
        dcc.Store(id='datasets'),
        html.Div([
            dcc.Dropdown(
                id='ecosystem-selector',
                className='dropdown-selector',
                options=[{'label': ecosystem, 'value': ecosystem} for ecosystem in ecosystems['ecosystem']],
                value='Select Ecosystem',
            ),
            dcc.Dropdown(
                id='date-suggestion-selector',
                className='dropdown-selector',
                options=[{'label': date_key, 'value': DATE_PRESETS[date_key]} for date_key in DATE_PRESETS.keys()],
                value=30,
            ),
            dcc.DatePickerRange(
                id='internal-activity-date-picker-range',
                className='date-picker',
                start_date=date.today() - timedelta(days=28),  #  Start on current day
                end_date=date.today(),
                display_format='MMM DD, YYYY',
            ),
        ], id='bar-graph-selector-bar', className='selector-bar'),
        html.Div([
            html.Div(id='internal-stacked-bar', className='internal-charts'),
        ], id='internal-stacked-bar-container', className='graph-container'),
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='data-selector',
                    
                    className='dropdown-selector',
                    options=[{'label': datatype, 'value': datatype} for datatype in ASSET_TYPES],
                    value=['Resources', 'Organizations'],
                    multi=True,
                ),
                dcc.Dropdown(
                    id='internal-activity-selector',
                    className='dropdown-selector',
                    options=[{'label': activity, 'value': activity} for activity in ACTIVITY_TYPES],
                    value=ACTIVITY_TYPES,
                    multi=True,
                )
            ], id='internal-asset-dropdown-bar', className='selector-bar'),
            html.Div(id='internal-asset-table-container', className='internal-tables'),
        ], id='internal-asset-dropdown-table-container', className='graph-container'),
        html.Div([
            dcc.Dropdown(
                id='key-type-selector',
                className='dropdown-selector',
                #options=[{'label': datatype, 'value': datatype} for datatype in KEY_TYPES],
                #value=['Audience', 'Industries', 'Organization Categories', 'General Tags', 'Resource Type'],
                multi=True,
            ),
            html.Div(id='internal-key-table-container', className='internal-tables'),
        ], id='internal-dropdown-key-table-container', className='graph-container')
    ], id='internal-feed-container', className='page-container')
