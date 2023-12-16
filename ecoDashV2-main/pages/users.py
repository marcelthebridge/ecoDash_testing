import dash
from dash import Dash, html, dcc, dash_table, callback, Input, Output, callback_context
from data_utils import *
from datetime import datetime, date, timedelta

dash.register_page(__name__, path_template="/platform-users/<ecosystem>")


def layout(ecosystem=None):
    if not ecosystem:
        return (
            html.Div("Error connecting to database, contact support.")
        )
    return(
        html.Div([
            dcc.Location(id='user-page-url', refresh=False),
            dcc.Store(id='user-page-data'),

            html.Div(className='selector-bar', children=[
                dcc.Dropdown(
                    id='user-date-suggestion-selector',
                    className='dropdown-selector',
                    options=[{'label': date_key, 'value': DATE_PRESETS[date_key]} for date_key in DATE_PRESETS.keys()],
                    value=30,
                ),
                dcc.DatePickerRange(
                    id='user-date-picker-range',
                    className='date-picker',
                    start_date=date.today() - timedelta(days=28),  # Start on current day
                    end_date=date.today(),
                    display_format='MMM DD, YYYY',
                ),
            ]),
            html.Div(id='user-date-output', style={'display': 'none'}),
            html.Div([
                html.Div(id='user-scorecard', className="column one-half"),
                dcc.Graph(id='user-type-pie', className="eco-card pie-card",
                          config={'staticPlot': False, 'displayModeBar': False, 'responsive': True}),
            ], className="scorecard-row full"),

            html.Div([
                html.Div([
                    dcc.Graph(id='user-growth-graph', className="scorecard-row"),
                    html.Div(id='user-column-scorecard', className="column"),
                ], className="scorecard eco-row"),
            ], className="scorecard-row full"),

            html.Div(id='user-key-tables', children=[
                html.Div(id='user-audience-key-table'),
                html.Div(id='user-industries-key-table'),
                html.Div(id='user-org-cat-key-table'),
            ], className="scorecard-row one-third")
        ]),
    )

