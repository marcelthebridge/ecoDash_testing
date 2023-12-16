import plotly.express as px
import plotly.graph_objs as go

color_sequence = px.colors.qualitative.Prism
from dash import Dash, html, dcc, callback, callback_context, dash_table
import dash
from dash.dependencies import Input, Output
from data_utils import *
from datetime import datetime
import json
from datetime import datetime, date, timedelta

"""
Start Callbacks
"""


def register_callbacks(app: Dash):
    @app.callback(Output('landing-page', 'children'),
                  Input('url', 'pathname'))
    def update_landing_page(pathname):
        if pathname == '/':
            return (
                html.H1('Multi-page app with Dash Pages'),
                html.Div([
                    html.Div(
                        dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"])
                    ) for page in dash.page_registry.values()
                ]),
            )
        else:
            return None

    """ Internal Retrieval Callbacks """

    # Internal Feed Callbacks
    @app.callback(
        Output('datasets', 'data'),
        [Input('ecosystem-selector', 'value'),
         Input('internal-activity-date-picker-range', 'start_date'),
         Input('internal-activity-date-picker-range', 'end_date'),
         Input('supa-data', 'data')])
    def retrieve_data_dropdown(ecosystem, start_date, end_date, datasets):
        if ecosystem:
            activity = query_sql(ecosystem, start_date, end_date)
            activity = activity.fillna('')
            datasets = json.loads(datasets)
            datasets['activity'] = activity.to_json(orient='split')
            return json.dumps(datasets)
        else:
            return None

    @app.callback(
        Output('supa-data', 'data'),
        Input('ecosystem-selector', 'value')
    )
    def retrieve_supa_data(ecosystem):
        if ecosystem:
            assets = query_supa(ecosystem, 'platform_assets')
            keywords = query_supa(ecosystem, 'platform_keys')
            users = query_supa(ecosystem, 'platform_users')
            supa_data = {
                'assets': assets.to_json(orient='split'),
                'keywords': keywords.to_json(orient='split'),
                'users': users.to_json(orient='split')
            }

            return json.dumps(supa_data)
        else:
            return None

    """
    Internal Feed Callbacks
    """

    @app.callback(
        [Output('internal-activity-date-picker-range', 'start_date'),
         Output('internal-activity-date-picker-range', 'end_date')],
        Input('date-suggestion-selector', 'value')
    )
    def update_date_range(date_suggestion):
        if date_suggestion == 'Custom Range':
            return None, None
        if date_suggestion:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=date_suggestion)
            return start_date, end_date
        else:
            # return None, None
            pass

    @app.callback(
        Output('internal-stacked-bar', 'children'),
        [Input('internal-activity-date-picker-range', 'start_date'),
         Input('internal-activity-date-picker-range', 'end_date'),
         Input('datasets', 'data'),
         ])
    def update_internal_stacked_bar(start_date, end_date, datasets):
        dataframes = return_dataframes(datasets, ['activity'])
        activity_df = dataframes['activity']
        if len(activity_df) == 0:
            return html.Div("No data available for this ecosystem.")
        activity_df['createdDate'] = pd.to_datetime(activity_df['createdDate'])
        activity_df = activity_df[activity_df['dataType'].isin(['Resources', 'Organizations'])]
        activity_df = activity_df[activity_df['activityType'].isin(ACTIVITY_TYPES)]
        mask = (activity_df['createdDate'] > start_date) & (activity_df['createdDate'] <= end_date)
        activity_df = activity_df.loc[mask]

        df_grouped = activity_df.groupby(['createdDate', 'activityType']).size() \
            .reset_index(name='count').sort_values(by='createdDate').dropna()

        fig = px.bar(df_grouped, x='createdDate', y='count', color='activityType', title='Internal Activity over Time')
        return dcc.Graph(figure=fig)

    @app.callback(
        Output('internal-asset-table-container', 'children'),
        [Input('internal-activity-date-picker-range', 'start_date'),
         Input('internal-activity-date-picker-range', 'end_date'),
         Input('datasets', 'data'),
         Input('data-selector', 'value'),
         Input('internal-activity-selector', 'value')
         ])
    def update_internal_asset_table(start_date, end_date, datasets, data_types, selected_activity):
        dataframes = return_dataframes(datasets, ['activity', 'assets'])
        activity_df = dataframes['activity']
        assets_df = dataframes['assets']
        if len(activity_df) == 0:
            return html.Div("No data available for this ecosystem.")
        activity_df = activity_df[
            (activity_df['dataType'].isin(data_types)) & (activity_df['activityType'].isin(selected_activity))]
        mask = (activity_df['createdDate'] > start_date) & (activity_df['createdDate'] <= end_date)
        activity_df = activity_df.loc[mask]

        df_grouped = activity_df.groupby(['dataType', 'dataObject']).size() \
            .reset_index(name='count').dropna()
        df_grouped = pd.merge(df_grouped, assets_df, left_on='dataObject', right_on='platformID', how='left')

        df_grouped = df_grouped.sort_values(by='count', ascending=False)
        df_grouped['keywords'] = df_grouped['keywords'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        assetTable = dash_table.DataTable(
            id='internal-asset-table',
            data=df_grouped[['name', 'keywords', 'dataType', 'count']].to_dict('records'),
            export_format='csv',
            export_headers='display',
            columns=[{'name': 'Name', 'id': 'name'},
                     {'name': 'Asset Type', 'id': 'dataType'},
                     {'name': 'Keywords', 'id': 'keywords'},
                     {'name': 'Engagement Count', 'id': 'count'}],
            style_table={'height': '300px', 'overflowY': 'auto'},
            fixed_rows={'headers': True},
            style_cell={
                'fontSize': '12px',
                'padding': '12px',
                'font-family': 'Inter',
                'border': 'none',
                'height': '50px',
                'minWidth': '100px', 'width': '150px', 'maxWidth': '200px',
                'whiteSpace': 'normal',
                'textAlign': 'left',
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'keywords'},
                    'textOverflow': 'ellipsis',
                    'overflow': 'hidden',
                    'whiteSpace': 'nowrap',
                    'maxWidth': '150px',
                },
                {'if': {'row_index': 'odd'},
                 'backgroundColor': '#F4F5F7'},
                {"if": {"state": "selected"},
                 "backgroundColor": "inherit !important",
                 "border": "inherit !important"}
            ],
            style_header={
                'backgroundColor': '#EBEDF2',
                'fontWeight': 'bold',
                'fontSize': '12px',
                'padding': '12px',
                'textAlign': 'left',
                'font-family': 'Inter'
            },
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_size=10,
        )
        return assetTable

    @app.callback(
        [Output('key-type-selector', 'options'),
         Output('key-type-selector', 'value')],
        [Input('datasets', 'data')])
    def update_internal_key_dropdown(datasets):
        dataframes = return_dataframes(datasets, ['keywords'])
        key_df = dataframes['keywords']
        if len(activity_df) == 0:
            return ['None'], ['None']
        key_options = [{'label': key, 'value': key} for key in key_df['type'].unique()]
        top_keys = key_df.groupby(['type']).size().reset_index(name='count').sort_values(by='count', ascending=False)[
            'type'].head(5)

        return key_options, top_keys

    @app.callback(
        Output('internal-key-table-container', 'children'),
        [Input('internal-activity-date-picker-range', 'start_date'),
         Input('internal-activity-date-picker-range', 'end_date'),
         Input('datasets', 'data'),
         Input('key-type-selector', 'value')])
    def update_internal_key_table(start_date, end_date, datasets, key_types):
        dataframes = return_dataframes(datasets, ['activity', 'assets', 'keywords'])
        activity_df = dataframes['activity']
        assets_df = dataframes['assets']
        key_df = dataframes['keywords']
        if len(activity_df) == 0:
            return html.Div("No data available for this ecosystem.")
        activity_df = activity_df[activity_df['dataType'].isin(['Resources', 'Organizations'])]
        mask = (activity_df['createdDate'] > start_date) & (activity_df['createdDate'] <= end_date)
        activity_df = activity_df.loc[mask]

        df_grouped = activity_df.groupby(['createdDate', 'dataType', 'dataObject']).size() \
            .reset_index(name='count').sort_values(by='createdDate').dropna()
        df_grouped = pd.merge(df_grouped, assets_df, left_on='dataObject', right_on='platformID', how='left')

        keywords_df = df_grouped.copy()
        keywords_df = keywords_df.explode('keywords')
        keywords_df = pd.merge(keywords_df, key_df, left_on='keywords', right_on='name', how='left')
        keywords_df = keywords_df[keywords_df['type'].isin(key_types)]

        # Calculate the engagement counts per keyword for resources and organizations
        keywords_df['resources'] = keywords_df.apply(
            lambda row: row['name_x'] if row['dataType'] == 'Resources' else '', axis=1)
        keywords_df['organizations'] = keywords_df.apply(
            lambda row: row['name_x'] if row['dataType'] == 'Organizations' else '', axis=1)

        aggregated_df = keywords_df.groupby(['keywords', 'type', 'dataType']).agg({
            'resources': lambda names: '; '.join(filter(None, names.unique())),
            'organizations': lambda names: '; '.join(filter(None, names.unique())),
            'count': 'sum'
        }).reset_index()

        resdf = aggregated_df[aggregated_df['dataType'] == 'Resources'].drop(columns=['organizations', 'dataType']) \
            .rename(columns={'count': 'resource_engagement'}).copy()
        orgdf = aggregated_df[aggregated_df['dataType'] == 'Organizations'].drop(columns=['resources', 'dataType']) \
            .rename(columns={'count': 'organization_engagement'}).copy()
        keywords_df = pd.merge(resdf, orgdf, on=['keywords', 'type'], how='outer')
        keywords_df['resources'] = keywords_df['resources'].fillna('')
        keywords_df['organizations'] = keywords_df['organizations'].fillna('')
        keywords_df['resource_engagement'] = keywords_df['resource_engagement'].fillna(0)
        keywords_df['organization_engagement'] = keywords_df['organization_engagement'].fillna(0)

        keyTable = dash_table.DataTable(
            id='internal-key-table',
            data=keywords_df[['keywords', 'resources', 'organizations',
                              'resource_engagement', 'organization_engagement', 'type']].to_dict('records'),
            export_format='csv',
            export_headers='display',
            columns=[{'name': 'Keyword', 'id': 'keywords'},
                     {'name': 'Keyword Type', 'id': 'type'},
                     {'name': 'Resources', 'id': 'resources'},
                     {'name': 'Resource Engagement', 'id': 'resource_engagement'},
                     {'name': 'Organizations', 'id': 'organizations'},
                     {'name': 'Organization Engagement', 'id': 'organization_engagement'}],
            fixed_rows={'headers': True},
            style_table={'height': '300px', 'overflowY': 'auto'},
            style_cell={
                'fontSize': '12px',
                'padding': '12px',
                'font-family': 'Inter',
                'border': 'none',
                'maxHeight': '50px',
                'minWidth': '100px', 'width': '150px', 'maxWidth': '200px',
                'whiteSpace': 'normal',
                'textAlign': 'left',
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'resources'},
                    'if': {'column_id': 'organizations'},
                    'textOverflow': 'ellipsis',
                    'overflow': 'hidden',
                    'whiteSpace': 'nowrap',
                    'maxWidth': '150px',
                },
                {'if': {'row_index': 'odd'},
                 'backgroundColor': '#F4F5F7'},
                {"if": {"state": "selected"},
                 "backgroundColor": "inherit !important",
                 "border": "inherit !important"}
            ],
            tooltip_data=[
                {column: {'value': str(value), 'type': 'markdown'}
                 for column, value in row.items()}
                for row in keywords_df.to_dict('records')
            ],
            tooltip_duration=2,
            style_header={
                'backgroundColor': '#EBEDF2',
                'fontWeight': 'bold',
                'fontSize': '12px',
                'padding': '12px',
                'textAlign': 'left',
                'font-family': 'Inter'
            },
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_size=10,
        )
        return keyTable

    """
    External Feed Callbacks
    """

    @app.callback(
        Output('external-datasets', 'data'),
        [Input('external-activity-url', 'pathname'),
         Input('external-activity-date-picker-range', 'start_date'),
         Input('external-activity-date-picker-range', 'end_date'),
         Input('external-supa-data', 'data')])
    def retrieve_external_data(ecosystem, start_date, end_date, supa_data):
        if ecosystem:
            ecosystem = ecosystem.split('/')[-1].replace('%20', ' ')
            activity = query_sql(ecosystem, start_date, end_date)
            activity = activity.fillna('')
            datasets = json.loads(supa_data)
            datasets['activity'] = activity.to_json(orient='split')
            return json.dumps(datasets)

    @app.callback(
        Output('external-supa-data', 'data'),
        Input('external-activity-url', 'pathname')
    )
    def retrieve_supa_data(ecosystem):
        if ecosystem:
            ecosystem = ecosystem.split('/')[-1].replace('%20', ' ')
            assets = query_supa(ecosystem, 'platform_assets')
            keywords = query_supa(ecosystem, 'platform_keys')
            users = query_supa(ecosystem, 'platform_users')
            supa_data = {
                'assets': assets.to_json(orient='split'),
                'keywords': keywords.to_json(orient='split'),
                'users': users.to_json(orient='split')
            }
            return json.dumps(supa_data)

    @app.callback(
        [Output('external-activity-date-picker-range', 'start_date'),
         Output('external-activity-date-picker-range', 'end_date')],
        Input('external-activity-date-suggestion-selector', 'value')
    )
    def update_date_range(date_suggestion):
        if date_suggestion:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=date_suggestion)
            return start_date, end_date
        else:
            # return None, None
            pass

    @app.callback(
        Output('graphs-and-tables', 'children'),
        [Input('external-data-selector', 'value'),
         Input('external-datasets', 'data')])
    def update_admin_graphs_and_tables(data_types, external_data):
        dataframes = return_dataframes(external_data, ['activity', 'assets', 'keywords'])
        activity_df = dataframes['activity']
        assets_df = dataframes['assets']
        key_df = dataframes['keywords']
        activity_df = activity_df[activity_df['dataType'].isin(data_types)]

        line_grouped = activity_df.groupby(['createdDate', 'activityType']).size() \
            .reset_index(name='count').sort_values(by='createdDate').dropna()

        fig = px.bar(line_grouped, x='createdDate', y='count',
                     color='activityType', title=f"Breakdown of Daily User Engagement",
                     labels={'createdDate': 'Date', 'count': '# of Engagements'}
                     )
        df_grouped = pd.merge(activity_df, assets_df, left_on='dataObject', right_on='platformID', how='left')
        df_grouped = df_grouped.dropna(subset=['name'])
        df_grouped = pd.merge(df_grouped, key_df, left_on='dataObject', right_on='platform_id', how='left')
        df_grouped['keywords'] = df_grouped['keywords'].apply(lambda x: ' | '.join(x))
        df_grouped = df_grouped.groupby(['name_x', 'assetType', 'keywords', 'activityType']).size().reset_index(
            name='count')
        df_grouped = df_grouped.pivot_table(index=['name_x', 'assetType', 'keywords'], columns='activityType',
                                            values='count', fill_value=0).reset_index()

        df_grouped.reset_index(inplace=True)
        for act_type in ACTIVITY_TYPES:
            if act_type not in df_grouped:
                df_grouped[act_type] = 0
        table = html.Div([
            dash_table.DataTable(
                id=f"external-engagement-table",
                data=df_grouped[['name_x', 'assetType', 'keywords', 'Viewed', 'Visited', 'Saved']].to_dict('records'),
                export_format='csv',
                export_headers='display',
                columns=[{'name': 'Name', 'id': 'name_x'},
                         {'name': 'Asset Type', 'id': 'assetType'},
                         {'name': 'Keywords', 'id': 'keywords'},
                         {'name': 'Viewed', 'id': 'Viewed'},
                         {'name': 'Visited', 'id': 'Visited'},
                         {'name': 'Saved', 'id': 'Saved'}],
                style_table={'height': '100%', 'overflowY': 'auto'},
                fixed_rows={'headers': True},
                style_cell={
                    'fontSize': '12px',
                    'padding': '12px',
                    'font-family': 'Inter',
                    'border': 'none',
                    'height': '50px',
                    'maxWidth': '200px',
                    'whiteSpace': 'normal',
                    'textAlign': 'left',
                },
                style_data_conditional=[{
                    'if': {'column_id': 'keywords'},
                    'textOverflow': 'ellipsis',
                    'overflow': 'hidden',
                    'whiteSpace': 'nowrap',
                    'maxWidth': '150px'},
                    {'if': {'row_index': 'odd'},
                     'backgroundColor': '#F4F5F7'},
                    {"if": {"state": "selected"},
                     "backgroundColor": "inherit !important",
                     "border": "inherit !important"},
                    {'if': {'column_id': 'name_x'},
                     'width': '20%'},
                    {'if': {'column_id': 'assetType'},
                     'width': '10%'},
                    {'if': {'column_id': 'Viewed'},
                     'width': '10%',
                     'textAlign': 'right'},
                    {'if': {'column_id': 'Visited'},
                     'width': '10%',
                     'textAlign': 'right'},
                    {'if': {'column_id': 'Saved'},
                     'width': '10%',
                     'textAlign': 'right'},
                ],
                style_header={
                    'backgroundColor': '#EBEDF2',
                    'fontWeight': 'bold',
                    'fontSize': '12px',
                    'padding': '12px',
                    'textAlign': 'left',
                    'font-family': 'Inter',
                },
                style_header_conditional=[
                    {'if': {'column_id': 'Viewed'},
                     'textAlign': 'right',
                     'padding-right': '4px'},
                    {'if': {'column_id': 'Visited'},
                     'textAlign': 'right',
                     'padding-right': '4px'},
                    {'if': {'column_id': 'Saved'},
                     'textAlign': 'right',
                     'padding-right': '4px'},
                ],
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_size=10,
            )], className='table-container')

        return html.Div([
            dcc.Loading(dcc.Graph(figure=fig, className='graph-container'), type='default', color='#3323CC',
                        fullscreen=False),
            dcc.Loading(table, type='default', color='#3323CC', fullscreen=False)
        ], className='external-graph-table-container')

    @app.callback(
        Output('external-scorecards', 'children'),
        [Input('external-datasets', 'data')]
    )
    def external_scorecards(datasets):
        dataframes = return_dataframes(datasets, ['activity'])
        activity_df = dataframes['activity']
        score_counts = {"total_views": len(activity_df[activity_df['activityType'] == 'Viewed']),
                        "total_visits": len(activity_df[activity_df['activityType'] == 'Visited']),
                        "total_saves": len(activity_df[activity_df['activityType'] == 'Saved']),
                        "total_engagement": len(activity_df)}

        return generate_external_scorecards(score_counts, activity_df)

    @app.callback(
        Output('external-user-engagement-table', 'children'),
        Input('external-datasets', 'data'))
    def update_external_user_engagement_table(datasets):
        dataframes = return_dataframes(datasets, ['activity', 'assets'])
        activity_df = dataframes['activity']
        assets_df = dataframes['assets']
        filtered_df = pd.merge(activity_df, assets_df, left_on='dataObject', right_on='platformID', how='left')

        filtered_df = filtered_df.groupby(['name', 'assetType', 'activityType', 'email_x']).size().reset_index(
            name='count')
        grouped_df = filtered_df.groupby(['email_x', 'activityType', 'assetType']).agg(
            names=('name', lambda x: ' | '.join(x)),
            total_count=('count', 'sum')
        ).reset_index()
        grouped_df = grouped_df.pivot_table(index=['email_x', 'assetType', 'names'], columns='activityType',
                                            values='total_count', fill_value=0).reset_index()
        grouped_df.reset_index(inplace=True)
        for act_type in ACTIVITY_TYPES:
            if act_type not in grouped_df:
                grouped_df[act_type] = 0
        table = html.Div([
            dash_table.DataTable(
                id='external-user-engagement-table',
                data=grouped_df[['email_x', 'assetType', 'names', 'Viewed', 'Visited', 'Saved']].to_dict('records'),
                export_format='csv',
                export_headers='display',
                columns=[{'name': 'User', 'id': 'email_x'},
                         {'name': 'Asset Type', 'id': 'assetType'},
                         {'name': 'Assets', 'id': 'names'},
                         {'name': 'Viewed', 'id': 'Viewed'},
                         {'name': 'Visited', 'id': 'Visited'},
                         {'name': 'Saved', 'id': 'Saved'}],
                tooltip_data=[
                    {column: {'value': str(value), 'type': 'markdown'}
                     for column, value in row.items()}
                    for row in grouped_df.to_dict('records')
                ],
                tooltip_duration=None,
                style_table={'height': '100%', 'overflowY': 'auto'},
                fixed_rows={'headers': True},
                style_cell={
                    'fontSize': '12px',
                    'padding': '12px',
                    'font-family': 'Inter',
                    'border': 'none',
                    'height': '50px',
                    'maxWidth': '150px',
                    'whiteSpace': 'normal',
                    'textAlign': 'left',
                },
                style_data_conditional=[{
                    'if': {'column_id': 'names'},
                    'textOverflow': 'ellipsis',
                    'overflow': 'hidden',
                    'whiteSpace': 'nowrap'},
                    {'if': {'row_index': 'odd'},
                     'backgroundColor': '#F4F5F7'},
                    {"if": {"state": "selected"},
                     "backgroundColor": "inherit !important",
                     "border": "inherit !important"},
                    {'if': {'column_id': 'email_x'},
                     'width': '15%'},
                    {'if': {'column_id': 'assetType'},
                     'width': '10%'},
                    {'if': {'column_id': 'Viewed'},
                     'width': '10%',
                     'textAlign': 'right'},
                    {'if': {'column_id': 'Visited'},
                     'width': '10%',
                     'textAlign': 'right'},
                    {'if': {'column_id': 'Saved'},
                     'width': '10%',
                     'textAlign': 'right'}
                ],
                style_header={
                    'backgroundColor': '#EBEDF2',
                    'fontWeight': 'bold',
                    'fontSize': '12px',
                    'padding': '12px',
                    'textAlign': 'left',
                    'font-family': 'Inter'
                },
                style_header_conditional=[
                    {'if': {'column_id': 'Viewed'},
                     'textAlign': 'right'},
                    {'if': {'column_id': 'Visited'},
                     'textAlign': 'right'},
                    {'if': {'column_id': 'Saved'},
                     'textAlign': 'right'},
                ],
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_size=10,
            )], className='table-container')
        return table

    """
    Users Page Callbacks
    """

    @app.callback(
        Output('user-page-data', 'data'),
        Input('user-page-url', 'pathname')
    )
    def retrieve_user_data(pathname):
        if pathname:
            ecosystem = pathname.split('/')[-1]
            assets = query_supa(ecosystem, 'platform_assets')
            keywords = query_supa(ecosystem, 'platform_keys')
            users = query_supa(ecosystem, 'platform_users')
            supa_data = {
                'assets': assets.to_json(orient='split'),
                'keywords': keywords.to_json(orient='split'),
                'users': users.to_json(orient='split')
            }
            return json.dumps(supa_data)

    @app.callback(
        [Output('user-date-picker-range', 'start_date'),
         Output('user-date-picker-range', 'end_date')],
        Input('user-date-suggestion-selector', 'value')
    )
    def update_user_date_range(date_suggestion):
        if date_suggestion:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=date_suggestion)).strftime('%Y-%m-%d')
            return start_date, end_date
        else:
            # return None, None
            pass

    @app.callback(
        Output('user-growth-graph', 'figure'),
        [Input('user-page-data', 'data'),
         Input('user-date-picker-range', 'start_date'),
         Input('user-date-picker-range', 'end_date')]
    )
    def user_growth_graph(data, start_date, end_date):
        fig = go.Figure()

        dataframes = return_dataframes(data, ['users'])
        user_df = dataframes['users']
        user_df['platform_created_date'] = pd.to_datetime(user_df['platform_created_date'])

        user_df = user_df.explode('user_types').dropna(subset=['user_types'])
        user_df = user_df[user_df['user_types'].isin(['Verified User', 'Community Admin', 'Admin'])]

        # Convert start and end dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Filter the DataFrame to include records up to the end_date
        filtered_df = user_df[user_df['platform_created_date'] <= end_date]

        # Define the frequency based on the date difference
        date_difference = (end_date - start_date).days
        date_frequency = 'W' if date_difference > 21 else 'D'

        # Define a full date range with the appropriate frequency
        date_range = pd.date_range(start=start_date, end=end_date, freq=date_frequency)

        # For each user type, add a line to the graph
        for user_type in ['Verified User', 'Community Admin', 'Admin']:
            subset = filtered_df[filtered_df['user_types'] == user_type]

            # Set the date as the index, resample, then take the cumulative sum
            grouped = subset.set_index('platform_created_date').resample(date_frequency).size().cumsum().reset_index(
                name='counts')

            # Reindex the grouped data with the full date range
            grouped.set_index('platform_created_date', inplace=True)
            grouped = grouped.reindex(date_range, method='ffill').reset_index()
            grouped.rename(columns={'index': 'platform_created_date'}, inplace=True)

            fig.add_trace(go.Scatter(x=grouped['platform_created_date'],
                                     y=grouped['counts'],
                                     mode='lines',
                                     name=user_type))

        # Update layout
        fig.update_layout(title='User Growth Over Time',
                          title_font=dict(size=18, family="Inter, bold", color="#333333"),
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
                          )
        return fig

    @app.callback(
        Output('user-scorecard', 'children'),
        [Input('user-page-data', 'data'),
         Input('user-date-picker-range', 'end_date')])
    def update_user_scorecard(data, end_date):
        dataframes = return_dataframes(data, ['users'])
        user_df = dataframes['users']
        total_users = len(user_df)
        user_df['platform_created_date'] = pd.to_datetime(user_df['platform_created_date'])
        user_df = user_df[user_df['platform_created_date'] <= end_date]
        last_week = datetime.today() - timedelta(days=7)

        verified_users = len(user_df[
                                 user_df['user_types'].apply(lambda x: 'Verified User' in x)])
        percentage = (verified_users / len(user_df)) * 100

        on_talent_true_count = len(user_df[user_df['on_talent'] == True])
        public_profile_count = len(user_df[user_df['public_profile'] != False])
        new_users_this_week = len(user_df[user_df['platform_created_date'] > last_week])
        users_connected_to_orgs = len(user_df[user_df['associated_orgs'].astype(bool)])

        return (
            html.Div([
                html.Div([
                    html.P(f"Total Users", className="metric-title"),
                    html.H3(f"{total_users}", className="metric-number"),
                    html.P(f"", className="metric-helper"),
                ], className="scorecard"),
                html.Div([
                    html.P(f"Verified Users:", className="metric-title"),
                    html.P(f"{verified_users}", className="metric-number"),
                    html.P(f"{percentage:.2f}% of users", className="metric-helper"),
                ], className="scorecard"),
            ], className="scorecard-row"),

            # Bottom left scorecards
            html.Div([
                html.Div([
                    html.P(f"New Users This Week", className="metric-title"),
                    html.P(f"{new_users_this_week}", className="metric-number"),
                    html.P(f"", className="metric-helper"),
                ], className="scorecard one-half"),
                html.Div([
                    html.P(f"Users Connected to Organizations", className="metric-title"),
                    html.P(f"{users_connected_to_orgs}", className="metric-number"),
                    html.P(f"{(users_connected_to_orgs / total_users) * 100:.2f}% of users", className="metric-helper"),
                ], className="scorecard one-half"),
            ], className="scorecard-row"),

            html.Div([
                html.Div([
                    html.P(f"Users On Talent Portal", className="metric-title"),
                    html.P(f"{on_talent_true_count}", className="metric-number"),
                    html.P(f"{(on_talent_true_count / total_users) * 100:.2f}% of users", className="metric-helper"),
                ], className="scorecard one-half"),
                html.Div([
                    html.P(f"Users with Public Profiles:", className="metric-title"),
                    html.P(f"{public_profile_count}", className="metric-number"),
                    html.P(f"{(public_profile_count / total_users) * 100:.2f}% of users",
                           className="metric-helper"),
                ], className="scorecard one-half"),
            ], className="scorecard-row"),
        )

    @app.callback(Output('user-type-pie', 'figure'),
                  [Input('user-page-data', 'data'),
                   Input('user-date-picker-range', 'end_date')]
                  )
    def user_type_pie(data, end_date):
        dataframes = return_dataframes(data, ['users'])
        user_df = dataframes['users']
        user_df['platform_created_date'] = pd.to_datetime(user_df['platform_created_date'])
        user_df = user_df[user_df['platform_created_date'] <= end_date]

        user_df = user_df[pd.isna(user_df['user_types']) == False]
        user_df = user_df.explode('user_types')
        user_df = user_df[user_df['user_types'].isin(['Verified User', 'Community Admin', 'Admin'])]
        counts = user_df['user_types'].value_counts().sort_values(ascending=False)

        fig = {
            'data': [
                {
                    'labels': counts.index,
                    'values': counts.values,
                    'type': 'pie',
                    'hole': 0.3,
                    'startangle': 315,
                    'rotation': 315,
                    'marker': {
                        # 'colors': color_sequence,
                        'colors': [user_color_dict[label] for label in counts.index],
                        'line': {'color': 'black', 'width': 2}
                    }
                },
            ],
            'layout': {
                # 'title': f"User Types on Ecosystem",
                'xaxis': {'showgrid': False},
                'yaxis': {'showgrid': False},
                'margin': {'l': 12, 'r': 12, 't': 12, 'b': 12},
                'autosize': True,
                'legend': {'size': '30', 'orientation': 'h'},
                'showlegend': True,
                'height': 450
            }
        }

        return fig

    @app.callback(
        Output('user-key-tables', 'children'),
        [Input('user-page-data', 'data'),
         Input('user-date-picker-range', 'end_date')]
    )
    def user_keyword_tables(user_data, end_date):
        dataframes = return_dataframes(user_data, ['users', 'keywords'])
        key_df = dataframes['keywords']
        user_df = dataframes['users']
        filtered_df = user_df[user_df['platform_created_date'] <= end_date].copy()
        filtered_df = filtered_df.explode('keywords').dropna(subset=['keywords']).copy()

        user_keys = pd.merge(filtered_df, key_df, left_on='keywords', right_on='platform_id', how='outer')

        def get_counts(dataframe, keyword_type):
            dataframe = dataframe[dataframe['type'] == keyword_type].copy()
            dataframe = dataframe.rename(columns={'name': 'Keyword'})
            dataframe = dataframe.groupby(['keywords', 'Keyword']).size().reset_index(name='Users')
            return dataframe[['Keyword', 'Users']].sort_values(by='Users', ascending=False)

        audience_keys = get_counts(user_keys, 'Audience')
        industries_keys = get_counts(user_keys, 'Industries')
        org_cat_keys = get_counts(user_keys, 'Organization Category')

        return html.Div(className="scorecard-row", children=[
            create_table(audience_keys, 'user-audience-key-table', 'Top Audiences'),
            create_table(industries_keys, 'user-industries-key-table', 'Top Industries'),
            create_table(org_cat_keys, 'user-org-cat-key-table', 'Top Organization Categories')
        ])

    """
    Asset Page Callbacks
    """

    @app.callback(
        Output('asset-page-data', 'data'),
        Input('asset-page-url', 'pathname')
    )
    def retrieve_user_data(pathname):
        if pathname:
            ecosystem = pathname.split('/')[-1]
            assets = query_supa(ecosystem, 'platform_assets')
            keywords = query_supa(ecosystem, 'platform_keys')
            users = query_supa(ecosystem, 'platform_users')
            supa_data = {
                'assets': assets.to_json(orient='split'),
                'keywords': keywords.to_json(orient='split'),
                'users': users.to_json(orient='split')
            }
            print('check')
            return json.dumps(supa_data)

    @app.callback(
        [Output('asset-date-picker-range', 'start_date'),
         Output('asset-date-picker-range', 'end_date')],
        [Input('asset-date-suggestion-selector', 'value')]
    )
    def update_asset_date_range(date_suggestion):
        if date_suggestion:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=date_suggestion)).strftime('%Y-%m-%d')
            return start_date, end_date
        else:
            # return None, None
            pass

    @app.callback(
        Output('asset-growth-graph', 'figure'),
        [Input('asset-page-data', 'data'),
         Input('asset-date-picker-range', 'start_date'),
         Input('asset-date-picker-range', 'end_date')]
    )
    def asset_growth_graph(datasets, start_date, end_date):
        dataframes = return_dataframes(datasets, ['assets'])
        assets_df = dataframes['assets']
        assets_df['platformCreatedDate'] = pd.to_datetime(assets_df['platformCreatedDate'])

        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Calculate the difference in days between start_date and end_date
        date_difference = (end_date - start_date).days

        # Define the frequency based on the date difference
        if date_difference > 21:
            date_frequency = 'W'
        else:
            date_frequency = 'D'

        # Filter the data based on the end_date
        filtered_df = assets_df[assets_df['platformCreatedDate'] <= end_date]

        # Define a full date range with the calculated frequency
        date_range = pd.date_range(start=start_date, end=end_date, freq=date_frequency)
        fig = go.Figure()

        # Calculate the cumulative counts for each assetType
        for asset_type in filtered_df['assetType'].unique():
            subset = filtered_df[filtered_df['assetType'] == asset_type]
            grouped = (
                subset
                .set_index('platformCreatedDate')
                .resample(date_frequency)
                .size()
                .cumsum()
                .reset_index(name='counts')
            )

            # Reindex the grouped data with the full date range and fill forward
            grouped = (
                grouped
                .set_index('platformCreatedDate')
                .reindex(date_range)
                .fillna(method='ffill')
                .reset_index()
                .rename(columns={'index': 'platformCreatedDate'})
            )

            color = asset_color_dict.get(asset_type, '#000000')
            fig.add_trace(go.Scatter(x=grouped['platformCreatedDate'], y=grouped['counts'],
                                     line=dict(color=color),
                                     mode='lines', name=asset_type))

        # Calculate the cumulative counts for all assets combined
        total_grouped = (
            filtered_df
            .set_index('platformCreatedDate')
            .resample(date_frequency)
            .size()
            .cumsum()
            .reset_index(name='counts')
        )

        # Reindex the total_grouped data with the full date range and fill forward
        total_grouped = (
            total_grouped
            .set_index('platformCreatedDate')
            .reindex(date_range)
            .fillna(method='ffill')
            .reset_index()
            .rename(columns={'index': 'platformCreatedDate'})
        )

        total_color = asset_color_dict.get('All Assets', '#000000')
        fig.add_trace(
            go.Scatter(x=total_grouped['platformCreatedDate'], y=total_grouped['counts'], mode='lines',
                       name='All Assets',
                       line=dict(color=total_color, dash='dash')))

        # Update layout
        fig.update_layout(title='Cumulative Asset Growth Over Time',
                          title_font=dict(size=18, family="Inter, extra-bold", color="#333333"),
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
                          )
        return fig

    @app.callback(
        Output('asset-column-scorecard', 'children'),
        [Input('asset-page-data', 'data'),
         Input('asset-date-picker-range', 'start_date'),
         Input('asset-date-picker-range', 'end_date')])
    def update_asset_scorecard(data, start_date, end_date):
        dataframes = return_dataframes(data, ['assets'])
        asset_df = dataframes['assets']
        total_assets = len(asset_df)
        filtered_df = asset_df[asset_df['platformCreatedDate'] <= end_date]

        asset_info = []

        for asset_type in ['Organization', 'Resource', 'Event', 'Job', 'News']:
            asset_count, percent, new_this_period = get_asset_count_percent(filtered_df, asset_type, total_assets,
                                                                            start_date, end_date)
            asset_info.append({
                'asset_type': asset_type,
                'count': asset_count,
                'percent': percent,
                'new_this_period': new_this_period
            })

        return generate_asset_scorecard_layout(asset_info)

    @app.callback(
        Output('asset-claimed-exclude-scorecard', 'children'),
        [Input('asset-page-data', 'data'),
         Input('asset-date-picker-range', 'end_date')]
    )
    def asset_claimed_exclude_scorecard(data, end_date):
        dataframes = return_dataframes(data, ['assets', 'users', 'keywords'])
        asset_df = dataframes['assets']
        filtered_df = asset_df[asset_df['platformCreatedDate'] <= end_date]

        def claimed_exclude_cards(asset_type):
            total_asset = len(filtered_df[filtered_df['assetType'] == asset_type])
            claimed_asset = len(
                filtered_df[(filtered_df['claimed'] == True) & (filtered_df['assetType'] == asset_type)])
            exclude_asset = len(
                filtered_df[(filtered_df['excludeFromUpdate'] == True) & (filtered_df['assetType'] == asset_type)])
            active_asset = len(
                filtered_df[(filtered_df['activityStatus'] == 'Active') & (filtered_df['assetType'] == asset_type)])

            percent_claimed = claimed_asset / total_asset * 100  # Note: This calculates % based on the asset type
            percent_exclude = exclude_asset / total_asset * 100  # Same here.
            percent_active = active_asset / total_asset * 100

            return html.Div(children=[
                html.P(f"{asset_type}s:", className="metric-header"),
                html.P(f"Claimed", className="metric-title"),
                html.P(f"{claimed_asset}", className="metric-number"),
                html.P(f"{percent_claimed:.2f}% of total", className="metric-helper"),
                html.P(f"Auto-Updates Paused", className="metric-title"),
                html.P(f"{exclude_asset}", className="metric-number"),
                html.P(f"{percent_exclude:.2f}% of total", className="metric-helper"),
                html.P(f"Active", className="metric-title"),
                html.P(f"{active_asset}", className="metric-number"),
                html.P(f"{percent_active:.2f}% of total", className="metric-helper")
            ], className="scorecard one-half metric-container")

        return html.Div(children=[
            claimed_exclude_cards('Organization'),
            claimed_exclude_cards('Resource'),
        ], className="scorecard-row full")

    @app.callback(
        Output('asset-key-table', 'children'),
        [Input('asset-page-data', 'data'),
         Input('asset-date-picker-range', 'end_date')]
    )
    def asset_keyword_tables(data, end_date):
        dataframes = return_dataframes(data, ['assets', 'keywords'])
        asset_df = dataframes['assets']
        key_df = dataframes['keywords']
        filtered_df = asset_df[asset_df['platformCreatedDate'] <= end_date].copy()
        filtered_df = filtered_df.explode('keyDCI').dropna(subset=['keyDCI'])

        asset_keys = pd.merge(filtered_df, key_df, left_on='keyDCI', right_on='dciID', how='right',
                              suffixes=('_asset', '_keyword'))

        def get_counts(dataframe, asset_type):
            count_field_name = f"{asset_type}s"
            dataframe = dataframe[dataframe['assetType'] == asset_type]
            dataframe = dataframe.groupby(['name_keyword', 'dciID_keyword', 'type']) \
                .size().reset_index(name=count_field_name). \
                rename(columns={'name_keyword': 'Keyword', 'type': 'Keyword Type'})
            return dataframe[['Keyword', 'Keyword Type', count_field_name]]. \
                sort_values(by=count_field_name, ascending=False)

        resource_keys = get_counts(asset_keys, 'Resource')
        organization_keys = get_counts(asset_keys, 'Organization')

        return html.Div(children=[
            create_table(organization_keys, 'organization-key-table', 'Top Organization Keywords'),
            create_table(resource_keys, 'resource-key-table', 'Top Resource Keywords'),
        ], className="scorecard-row full")

    @app.callback(
        [Output('organization-origin-claim-sun', 'figure'),
        Output('resource-origin-claim-sun', 'figure')],
        [Input('asset-page-data', 'data'),
         Input('asset-date-picker-range', 'end_date')]
    )
    def generate_org_sun_graphs(asset_page_data, end_date):
        dataframes = return_dataframes(asset_page_data, ['assets'])
        assets_df = dataframes['assets']
        filtered_df = assets_df[assets_df['platformCreatedDate'] <= end_date]

        return create_sunburst_figure(filtered_df, 'Organization'), create_sunburst_figure(filtered_df, 'Resource')


"""
Functions
"""


def json_to_df(df):
    df = json.loads(df)
    df = pd.DataFrame(df, orient='split')
    return df


def return_dataframes(datasets, data_list):
    datasets = json.loads(datasets)
    assets_df, key_df, user_df, activity_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if 'assets' in data_list and 'assets' in datasets:
        assets_df = time_fixer(pd.read_json(datasets['assets'], orient='split'))

    if 'keywords' in data_list and 'keywords' in datasets:
        key_df = time_fixer(pd.read_json(datasets['keywords'], orient='split'))

    if 'users' in data_list and 'users' in datasets:
        user_df = time_fixer(pd.read_json(datasets['users'], orient='split'))

    if 'activity' in data_list and 'activity' in datasets:
        activity_df = time_fixer(pd.read_json(datasets['activity'], orient='split'))
        if 'createdDate' in activity_df.columns:
            activity_df['createdDate'] = pd.to_datetime(activity_df['createdDate']).dt.strftime('%Y-%m-%d')
        activity_df = pd.merge(activity_df, pd.read_json(datasets['users'], orient='split')[['platformID', 'email']],
                               left_on='user', right_on='platformID')
        activity_df = fill_anonymous_email(activity_df, 'platformID_y', 'email')
        activity_df = activity_df[~activity_df['email'].str.contains('ecomap', na=False)]

    return {
        'assets': assets_df,
        'keywords': key_df,
        'users': user_df,
        'activity': activity_df
    }


def return_dataframes_old(datasets):
    datasets = json.loads(datasets)
    assets_df = time_fixer(pd.read_json(datasets['assets'], orient='split'))
    key_df = time_fixer(pd.read_json(datasets['keywords'], orient='split'))
    user_df = time_fixer(pd.read_json(datasets['users'], orient='split'))

    if 'activity' in datasets:
        activity_df = time_fixer(pd.read_json(datasets['activity'], orient='split'))
        if 'createdDate' in activity_df.columns:
            activity_df['createdDate'] = pd.to_datetime(activity_df['createdDate']).dt.strftime('%Y-%m-%d')
        activity_df = pd.merge(activity_df, user_df[['platformID', 'email']], left_on='user', right_on='platformID')
        activity_df = fill_anonymous_email(activity_df, 'platformID_y', 'email')
        activity_df = activity_df[~activity_df['email'].str.contains('ecomap', na=False)]
        return activity_df, assets_df, key_df, user_df
    else:
        return assets_df, key_df, user_df


def time_fixer(df):
    for col in df.columns:
        try:
            if 'date' in col.lower():  # Check if 'date' is in the column name
                df[col] = pd.to_datetime(df[col], unit='ms')
        except Exception as e:
            continue
            # print(e)
    return df


def fill_anonymous_email(df, id_col, email_col):
    df[email_col] = df.apply(
        lambda row: f"Anonymous {str(row[id_col])[-5:]}" if pd.isna(row[email_col]) or row[email_col] == '' else row[
            email_col], axis=1)
    return df


def generate_graph_and_table(df, data_type, assets, keys):
    df_filtered = df[df['dataType'] == data_type]
    df_grouped = df_filtered.groupby(['createdDate', 'activityType', 'dataObject']).size() \
        .reset_index(name='count').sort_values(by='createdDate').dropna()

    df_grouped = pd.merge(df_grouped, assets, left_on='dataObject', right_on='platformID', how='left')
    df_grouped = df_grouped[df_grouped['name'] != '']

    fig = px.bar(df_grouped, x='createdDate', y='count',
                 color='activityType', title=f"Engagement for {data_type} over Time",
                 hover_data=['name', 'count'])

    df_grouped = pd.merge(df_grouped, keys, left_on='dataObject', right_on='platform_id', how='left')
    df_grouped['keywords'] = df_grouped['keywords'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

    table = html.Div([
        dash_table.DataTable(
            id=f"{data_type}",
            data=df_grouped[['name_x', 'keywords', 'count']].to_dict('records'),
            export_format='csv',
            export_headers='display',
            columns=[{'name': 'Name', 'id': 'name_x'},
                     {'name': 'Keywords', 'id': 'keywords'},
                     {'name': 'Engagement Count', 'id': 'count'}],
            style_table={'height': '100%', 'overflowY': 'auto'},
            fixed_rows={'headers': True},
            style_cell={
                'fontSize': '12px',
                'padding': '12px',
                'font-family': 'Inter',
                'border': 'none',
                'height': '50px',
                'minWidth': '100px', 'width': '150px', 'maxWidth': '200px',
                'whiteSpace': 'normal',
                'textAlign': 'left',
            },
            style_data_conditional=[{
                'if': {'column_id': 'keywords'},
                'textOverflow': 'ellipsis',
                'overflow': 'hidden',
                'whiteSpace': 'nowrap',
                'maxWidth': '150px'}],
            style_header={
                'backgroundColor': '#EBEDF2',
                'fontWeight': 'bold',
                'fontSize': '12px',
                'padding': '12px',
                'textAlign': 'left',
                'font-family': 'Inter'
            },
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_size=10,
        )], className='internal-tables')

    return html.Div([
        dcc.Graph(figure=fig),
        html.Hr(),
        table
    ], className='graph-container')


def generate_external_scorecards(score_counts, activity_df):
    grouped_df = activity_df.groupby(['activityType', 'dataType']).size().reset_index(name='count')
    fig = px.sunburst(
        grouped_df,
        path=['dataType', 'activityType'],
        values='count',
        color_discrete_sequence=px.colors.qualitative.Prism,
        branchvalues='total'
    )
    title_text = "Engagement Breakdown by Asset Type"
    fig.update_layout(title_text=title_text,
                      title_font=dict(size=18, family="Inter, bold", color="#333333"))
    fig.update_traces(textinfo='label+percent parent', marker_line=dict(color='black', width=2))

    return (
        html.Div([
            html.Div([
                html.P(f"Total Views", className="metric-title"),
                html.P(f"{score_counts['total_views']}", className="metric-number"),
                html.P(f"Profile Page Views", className="metric-helper"),
            ], id='external-total-view-score', className="scorecard one-half external-metrics"),
            html.Div([
                html.P(f"Total Visits", className="metric-title"),
                html.P(f"{score_counts['total_visits']}", className="metric-number"),
                html.P(f"Click-throughs to Website", className="metric-helper"),
            ], id='external-total-visit-score', className="scorecard one-half external-metrics"),
            html.Div([
                html.P(f"Total Saves", className="metric-title"),
                html.P(f"{score_counts['total_saves']}", className="metric-number"),
                html.P(f"Assets Saved to Lists", className="metric-helper"),
            ], id='external-total-save-score', className="scorecard one-half external-metrics"),
            html.Div([
                html.P(f"Total Engagement", className="metric-title"),
                html.P(f"{score_counts['total_engagement']}", className="metric-number"),
                html.P(f"Views + Visits + Saves", className="metric-helper"),
            ], id='external-total-engagement-score', className="scorecard one-half external-metrics"),
        ], className='scorecard-clear one-half card-wrap'),
        html.Div([
            dcc.Graph(figure=fig, id='external-activity-sunburst',
                      style={'border-radius': '1rem', 'background-color': 'white'})
        ], className='sunburst-graph one-half'),
    )


def get_asset_count_percent(filtered_df, asset_type, total_assets, start_date, end_date):
    assets_of_type = filtered_df[filtered_df['assetType'] == asset_type]
    asset_count = len(assets_of_type)

    if asset_count == 0:
        return asset_count, 0, 0

    new_this_period = len(assets_of_type[(assets_of_type['platformCreatedDate'] > start_date) &
                                         (assets_of_type['platformCreatedDate'] <= end_date)])

    return asset_count, (asset_count / total_assets) * 100, new_this_period


def generate_asset_scorecard_layout(asset_data):
    def generate_component(data):
        return dcc.Loading(
            children=[
                html.P(f"{data['asset_type']}", id=f"{data['asset_type']}", className='chart_legend ', ),
                html.P(f"New this period: {data['new_this_period']}", className="chart-label-new"),
                html.P(f"{data['count']}", className="chart-label-count full"),
            ],
            className="chart-label-container", type='default', color='#3323CC', fullscreen=False
        )

    scorecard_components = [generate_component(data) for data in asset_data]

    return html.Div(children=scorecard_components,
                    className="column chart-labels-column")


def create_sunburst_figure(df, asset_type):
    df['origin'] = ['User Generated' if not item or item.strip() == '' else 'EcoMap' for item in df['dciID']]
    filtered_data = df[df['assetType'] == asset_type].copy()
    filtered_data['claimed'] = filtered_data['claimed'].apply(lambda x: 'Claimed' if x else 'Unclaimed')
    filtered_data = filtered_data.groupby(['assetType', 'origin', 'claimed']).size().reset_index(name='count')

    fig = px.sunburst(filtered_data,
                      path=['assetType', 'origin', 'claimed'],
                      values='count',
                      color_discrete_sequence=color_sequence
                      )

    title_text = f"{asset_type} Record Origin and Ownership"
    fig.update_layout(title_text=title_text, title_font=dict(size=18, family="Inter, semi-bold", color="#333333"),
                      xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    fig.update_traces(marker_line=dict(color='black', width=2))

    return fig


def create_table(dataframe, id_name, title):
    base_style = "table-card "
    if title in ['Top Resource Keywords', 'Top Organization Keywords']:
        style_choice = base_style + "one-half"
    else:
        style_choice = base_style + "one-third"

    return html.Div([
        html.H5(title, className="metric-header"),
        dcc.Loading(
            dash_table.DataTable(
                id=id_name,
                columns=[{"name": i, "id": i} for i in dataframe.columns],
                data=dataframe.to_dict('records'),
                export_format='csv',
                export_headers='display',
                style_cell={'textAlign': 'left',
                            'fontSize': '12px',
                            'padding': '12px',
                            'font-family': 'Inter',
                            'border': 'none'},
                style_cell_conditional=[{'if': {'column_id': 'Count'}, 'width': '60px', 'text-align': 'right'},
                                        {'if': {'column_id': 'Users'}, 'width': '80px', 'text-align': 'right'},
                                        {'if': {'column_id': 'Organizations'}, 'width': '120px', 'text-align': 'right'},
                                        {'if': {'column_id': 'Resources'}, 'width': '100px', 'text-align': 'right'},
                                        {'if': {'column_id': 'Keyword'}, 'width': 'auto'}],
                style_header={
                    'backgroundColor': '#EBEDF2',
                    'fontWeight': 'bold',
                    'fontSize': '12px',
                    'padding': '12px',
                    'textAlign': 'left',
                    'font-family': 'Inter'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'},
                     'backgroundColor': '#F4F5F7'},
                    {"if": {"state": "selected"},
                     "backgroundColor": "inherit !important",
                     "border": "inherit !important"}
                ],
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current=0,
                page_size=10,
                fixed_rows={'headers': True},
            ), type='default', color='#3323CC', fullscreen=False),
    ], className=style_choice)
