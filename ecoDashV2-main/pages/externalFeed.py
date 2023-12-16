import dash
from dash import Dash, html, dcc, dash_table, callback, Input, Output, callback_context
import pandas as pd
from data_utils import *
from datetime import datetime, date, timedelta
import plotly.express as px

dash.register_page(__name__, path_template="/externalFeed/<ecosystem>")


def layout(ecosystem=None):
    if not ecosystem:
        return (
            html.Div("Error connecting to database, contact support.")
        )

    return html.Div([
        dcc.Location(id='external-activity-url', refresh=False),
        dcc.Store(id='external-datasets'),
        dcc.Store(id='external-supa-data'),
        html.H1(f"Activity in {ecosystem.replace('%20', ' ')}"),
        html.Div([
            dcc.Dropdown(
                id='external-activity-date-suggestion-selector',
                className='dropdown-selector',
                options=[{'label': date_key, 'value': DATE_PRESETS[date_key]} for date_key in DATE_PRESETS.keys()],
                value=30,
            ),
            dcc.DatePickerRange(
                id='external-activity-date-picker-range',
                className='date-picker',
                start_date=date.today() - timedelta(days=28),  # Start on current day
                end_date=date.today(),
                display_format='MMM DD, YYYY',
            ),
        ], id='bar-graph-selector-bar', className='selector-bar'),
        dcc.Loading([
            html.Div(id='external-scorecards', className='scorecard-outer-container full'),
        ]),
        html.Div(
            dcc.Dropdown(
                id='external-data-selector',
                className='dropdown-selector',
                options=[{'label': datatype, 'value': datatype} for datatype in ASSET_TYPES],
                value=['Resources', 'Organizations'],
                multi=True,
            ), id='external-asset-selector-bar', className='selector-bar'),
        html.Div(id='graphs-and-tables'),
        html.Div(id='external-user-engagement-table', className='internal-tables'),
    ])

