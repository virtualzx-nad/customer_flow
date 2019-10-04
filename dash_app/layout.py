# -*- coding: utf-8 -*-
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html


def get_layout(lat0, lon0, zoom0, pitch0, bearing0, tracker, controller):
    return html.Div(children=[
        html.H1('Global Customer Flow Monitor'),

        html.Div("A simple and scalable system based on Pulsar Functions"),

        html.Div(children=[

                html.Div(style={'width':'45%', 'display': 'inline-block'}, children=[
                    html.Div('Monitor Pipeline Performance'),
                    html.Div(
                         dcc.Graph(id='rate-graph')
                    ),
                    html.Div(
                         dcc.Graph(id='latency-graph')
                    ),
                    html.Div([
                        html.Div(
                            daq.NumericInput(id='multiplicity-input',
                                value=1, min=1, max=100,
                                label='multiplicity',
                                size=80,
                            ),              
                            style={'width':'25%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            daq.NumericInput(id='ingestion-rate-input',
                                value=1000, min=1, max=10000,
                                label='ingestion rate',
                                size=120,
                            ),
                            style={'width':'25%', 'display': 'inline-block'}
                        ),
                    ])
                    html.Div([
                        html.Div(
                            dcc.Button('Resume', id='resume-button'),
                            style={'width':'25%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            dcc.Button('Pause', id='pause-button'),
                            style={'width':'25%', 'display': 'inline-block'}
                        ),
                        html.Div(
                            daq.NumericInput(id='partitions-input',
                                value=1, min=1, max=64,
                                label='Partitions',
                                size=120,
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
            html.Div('', id='empty-div'),
            dcc.Interval(
                    id="update-ticker",
                    interval=1000,
                    n_intervals=0,
                ),
            dcc.Store(id='data-store', data={})
    ])

