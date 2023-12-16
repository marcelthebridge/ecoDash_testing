import dash
from dash import Dash, html, dcc, dash_table, callback, Input, Output, callback_context
from data_utils import *
from datetime import datetime, date, timedelta

dash.register_page(__name__, path_template="/platform-assets/<ecosystem>")


def layout(ecosystem=None):
    if not ecosystem:
        return (
            html.Div("Error connecting to database, contact support.")
        )
    return(
        dcc.Loading([
            dcc.Location(id='asset-page-url', refresh=False),
            dcc.Store(id='asset-page-data'),

            html.Div(className='selector-bar', children=[
                dcc.Dropdown(
                    id='asset-date-suggestion-selector',
                    className='dropdown-selector',
                    options=[{'label': date_key, 'value': DATE_PRESETS[date_key]} for date_key in DATE_PRESETS.keys()],
                    value=30,
                ),
                dcc.DatePickerRange(
                    id='asset-date-picker-range',
                    className='date-picker',
                    start_date=date.today() - timedelta(days=28),  # Start on current day
                    end_date=date.today(),
                    display_format='MMM DD, YYYY',
                ),
            ]),
            dcc.Loading(id='asset-loading', children=[
                html.Div([
                    html.Div([
                        dcc.Graph(id='asset-growth-graph', className='asset-user-line-graph'),
                        html.Div(id='asset-column-scorecard', className='asset-user-scorecard'),
                    ], className="table-card scorecard-row"),
                ], className="scorecard-row full"),

                html.Div(id='asset-claimed-exclude-scorecard',
                         className="scorecard-row full"),
                html.Div(id='asset-key-table', children=[
                    html.Div(id='organization-key-table'),
                    html.Div(id='resource-key-table'),
                ], className="scorecard-row full"),

                html.Div(id='asset-sun-graphs', children=[
                    dcc.Graph(id='organization-origin-claim-sun', className="scorecard one-half",
                              style={'border-radius': '1rem', 'background-color': 'white'}),
                    dcc.Graph(id='resource-origin-claim-sun', className="scorecard one-half",
                              style={'border-radius': '1rem', 'background-color': 'white'}),
                ], className="scorecard-row full"),
            ], type='default', color='#1f77b4', fullscreen=False),
        ]),
    )
