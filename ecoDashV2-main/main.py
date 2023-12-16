from dash import Dash, dcc, html, callback, Input, Output
import dash
import callbacks

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server

dash.register_page(__name__, path='/')

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='landing-page'),
    dash.page_container
])

callbacks.register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)
