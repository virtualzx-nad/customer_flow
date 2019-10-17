# -*- coding: utf-8 -*-
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html


background = '#111116'

def get_layout(lat0, lon0, zoom0, pitch0, bearing0):
    return html.Section(style={'width': '100%', 'height': '100%', 'margin': 0, 'padding':0}, children=[
            html.Div(style={'width':'100%', 'background': background,'color': '#fff', 'vertical-align': 'top'}, children=[
                html.Div(style={'display':'table', 'width': '100%'},children=[
                    html.Div(style={'width': '40%', 'display': 'table-cell'}, children=[
                        html.H2('  Avoid-the-Line', style={'margin': 8}),
                        html.Div('  Global realtime monitor of busy businesses', style={'margin': 8}),
                        html.Div([
                            html.Div('Tracking', style={'display': 'inline-block', 'margin': 6}),
                            html.Div('', id='category-count-div', style={'display': 'inline-block', 'margin': 6}),
                            html.Div('', id='category-name-div', style={'display': 'inline-block', 'margin': 6}),
                            ], style={'margin': 4})
                    ]),
                    html.Div(style={'width': '40%', 'display': 'table-cell', 'margin': 20}, children=[
                        'Colors show the current number of visitors compared to recent records. '
                        'Red indicates high numbers close to the maximum capacity, and blue the opposite.'
                        'Green indicate a place that is usually crowded but less so today.'
                        'Size of the markers indicate the popularity of an establishment, i.e. maximum number of visitors '
                        'in recent months.'
                        ]),
                    html.Div('',style={'width': '15%', 'display': 'table-cell'})
                ]),
                    html.Div(
                        dcc.Graph(
                            id='map-graph',
                            figure={
                                'data': [
                                    {'type': 'scattermapbox', 'name': 'main-map'},
                                ],
                                'layout': {
                                    'mapbox':{
                                        'style':  'mapbox://styles/mapbox/navigation-preview-night-v4',
                                        'accesstoken': 'pk.eyJ1IjoidmlydHVhbHp4IiwiYSI6ImNrMTRra2s3ZDBsOTgzY3FkOG1ybnlodHQifQ.ggJkoaS_tOG6cPxB7BZ88w',
                                        'zoom': zoom0,
                                        'pitch': pitch0,
                                        'bearing':bearing0,
                                        'center': {'lat': lat0, 'lon': lon0}
                                        
                                    },
                                    'plot_bgcolor': background, 
                                    'paper_bgcolor': background,
                                    'font': {  'color': '#fff', 'font-weight': 'bold'  },
                                    'margin': {'l': 10, 'r':10, 'b':10, 't':30, 'pad':5},
                                    'automargin': True
                                }
                            }
                        ),
                        style={'width': '100%'}
                    ),
                    html.Div([
                        html.Div('Coord ({:.3f}, {:.3f})'.format(lat0, lon0), id='coordinate-display', 
                                 style={'width': '35%', 'align': 'left', 'padding': 0, 'display': 'inline-block'}),
                        html.Div('  Category',
                                 style={'width':'15%', 'align': 'right', 'padding': 0, 'display': 'inline-block'}),
                        html.Div(style={'width':'37%', 'align': 'left', 'padding': 0, 'display': 'inline-block', 'color': 'black' }, 
                            children=dcc.Dropdown(id='category-dropdown',
                                     options=[{'label': 'Restaurants', 'value': 'geo:Restaurants'}],
                                     value='geo:Restaurants')
                                )
                    ])
                ]),

        html.Div(style={'width':'100%', 'height':'100%', 'vertical-align': 'top'},
            id='metrics-panel',
            children=[

                html.Div([
                    html.H1('Performance Metrics', style={'height': '2cm', 'display':'inline-block', 'vertical-align': 'bottom', 'align':'center', 'width': '45%'}),
                    html.Div('',id='pulsar-connected',
                             style={'color':'green', 'font-weight':'bold', 'display': 'inline-block', 'vertical-align': 'bottom', 'align':'center', 'width': '50%'})
                ]),
                    html.Div(
                         dcc.Graph(id='rate-graph')
                    ),
                    html.Div(
                         dcc.Graph(id='latency-graph')
                    ),
                    html.Div([
                        html.Div('Ingestion Control',style={'width':'14%', 'display': 'inline-block'}),
                        html.Div(
                            daq.NumericInput(id='multiplicity-input',
                                value=1, min=1, max=10000,
                                label='multiplicity',
                                size=60,
                            ),              
                            style={'width':'13%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            daq.NumericInput(id='ingestion-rate-input',
                                value=3000, min=1, max=10000,
                                label='ingestion rate',
                                size=110,
                            ),
                            style={'width':'23%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            html.Button('Resume', id='resume-button', style={'width': '70'}),
                            style={'width':'23%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            html.Button('Pause', id='pause-button', style={'width': '70'}),
                            style={'width':'23%', 'display': 'inline-block'}
                        ),
                    ]),
                    html.Div([
                        html.Div('Processing Control',style={'width':'30%', 'display': 'inline-block'}),
                        html.Div(
                            daq.NumericInput(id='partitions-input',
                                value=6, min=1, max=10,
                                label='Parallelism',
                                size=150,
                            ),
                            style={'width':'35%', 'display': 'inline-block'}
                        )
                    ]),
                    html.Div([
                            html.Div('', id='empty-div1', style={'display': 'none'}),
                            html.Div('', id='empty-div2', style={'display': 'none'}),
                            html.Div('', id='empty-div3', style={'display': 'none'}),
                            html.Div('', id='empty-div4', style={'display': 'none'}),
                        html.Div('', id='empty-div5', style={'display': 'none'}),
                        html.Div('', id='empty-div6', style={'display': 'none'}),
                    ], id='empty-div', style={'display': 'none'}),
                    dcc.Interval(
                            id="update-ticker",
                            interval=2000,
                            n_intervals=0,
                        ),
                    html.Div('', id='interval-count', style={'display':'none'}),
                ]),
    ])

