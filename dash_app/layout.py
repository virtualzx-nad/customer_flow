# -*- coding: utf-8 -*-
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html


def get_layout(lat0, lon0, zoom0, pitch0, bearing0):
    return html.Div(children=[
        html.H2('Customer Flow Monitor'),

        html.Div("A scalable system based on Pulsar"),

        html.Div(children=[

                html.Div(style={'width':'50%', 'display': 'inline-block'}, children=[
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
                                value=1, min=1, max=100,
                                label='multiplicity',
                                size=60,
                            ),              
                            style={'width':'13%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            daq.NumericInput(id='ingestion-rate-input',
                                value=1000, min=1, max=10000,
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
                                value=1, min=1, max=64,
                                label='Parallelism',
                                size=150,
                            ),
                            style={'width':'35%', 'display': 'inline-block'}
                        )
                    ])
                ]),
                html.Div(style={'width':'45%', 'display': 'inline-block'}, children=[
                    html.Div(
                        dcc.Graph(
                            id='map-graph',
                            figure={
                                'data': [
                                    {'type': 'scattermapbox', 'name': 'main-map'},
                                ],
                                'layout': {
                                    'mapbox':{
                                        'style':  'light',
                                        'accesstoken': 'pk.eyJ1IjoidmlydHVhbHp4IiwiYSI6ImNrMTRra2s3ZDBsOTgzY3FkOG1ybnlodHQifQ.ggJkoaS_tOG6cPxB7BZ88w',
                                        'zoom': zoom0,
                                        'pitch': pitch0,
                                        'bearing':bearing0,
                                        'center': {'lat': lat0, 'lon': lon0}
                                        
                                    },
                                    'margin': {'l': 10, 'r':10, 'b':10, 't':30, 'pad':5},
                                    'automargin': True
                                }
                            }
                        ),
                        style={'border': '1px solid gray'}
                    ),
                    html.Div([
                        html.Div('Coord ({:.3f}, {:.3f})'.format(lat0, lon0), id='coordinate-display', 
                                 style={'width': '35%', 'align': 'left', 'padding': 0, 'display': 'inline-block'}),
                        html.Div('  Category',
                                 style={'width':'15%', 'align': 'right', 'padding': 0, 'display': 'inline-block'}),
                        html.Div(style={'width':'37%', 'align': 'left', 'padding': 0, 'display': 'inline-block'},
                                children=dcc.Dropdown(id='category-dropdown',
                                     options=[{'label': 'Restaurants', 'value': 'geo:Restaurants'}],
                                     value='geo:Restaurants')
                                )
                    ])
                ])

            ]),
            html.Div([
                    html.Div('', id='empty-div1'),
                    html.Div('', id='empty-div2'),
                    html.Div('', id='empty-div3'),
                    html.Div('', id='empty-div4'),
                    html.Div('', id='empty-div5'),
                ], id='empty-div'),
            dcc.Interval(
                    id="update-ticker",
                    interval=1000,
                    n_intervals=0,
                ),
            dcc.Store(id='data-store', data={})
    ])

