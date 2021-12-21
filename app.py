import sys
import datetime
import pandas as pd

import dash
from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
df = pd.read_csv("./data/input.csv", header=0, sep=';', decimal=',',)

df.columns = ['datetime', 'ticker', 'ROI', 'close', 'timeframe', 'direction',
       'ff_datetime', 'ff', 'ff_price',
       'sf_datetime', 'sf', 'sf_price']

df_prefiltered = df[~df.direction.isna()]
prefiltered_columns = ["datetime", "ticker", "ROI", "timeframe", "direction"]
df_prefiltered = df_prefiltered[prefiltered_columns]

# force to replace Nan with empty string
df.loc[df.direction.isna(), "direction"] = ""

# Reason - String list with Nan, sort using pandas series
lst_direction = (df["direction"].sort_values().unique())
lst_roi = sorted(df["ROI"].unique())
lst_ticker = sorted(df["ticker"].unique())
lst_timeframe = sorted(df["timeframe"].unique())

PREFILTER_PAGE_SIZE = 10
PAGE_SIZE = 50

app.layout = html.Div([
                        html.Div([
                                html.Div([
                                    # Dropdown menu
                                    html.Div([
                                            'Direction: ',
                                            dcc.Dropdown(
                                                id='dropdown_direction',
                                                options = [{'label': e, 'value': e} for e in lst_direction],
                                                placeholder = 'Select Direction'
                                            ), 
                                        ]), 
                                    html.Div([
                                            'Superior POI',
                                            dcc.Dropdown(
                                                id='dropdown_roi',
                                                options = [{'label': e, 'value': e} for e in lst_roi],
                                                placeholder = 'Select Superior POI'
                                            ),
                                        ]),
                                    html.Div([
                                            'ticker',
                                            dcc.Dropdown(
                                                id='dropdown_ticker',
                                                options = [{'label': e, 'value': e} for e in lst_ticker],
                                                placeholder = 'Select ticker'
                                            ),
                                        ]),
                                    html.Div([ 
                                            'timeframe',
                                            dcc.Dropdown(
                                                id='dropdown_timeframe',
                                                options = [{'label': e, 'value': e} for e in lst_timeframe],
                                                placeholder = 'Select timeframe'
                                            ),   
                                        ]),
                                    # End of Dropdown
                                ], style={'display': 'inline-block', 'verticalAlign': 'top', 'width': '15vw', 'marginLeft': 10, 'marginRight': 10, 'marginTop': 10, 'marginBottom': 10,}),
                                html.Div([
                                    dash_table.DataTable(
                                        id='prefiltered-table-sorting-filtering',
                                        columns=[
                                            {'name': i, 'id': i, 'deletable': True} for i in (df_prefiltered.columns)
                                        ],
                                        page_current= 0,
                                        page_size= PREFILTER_PAGE_SIZE,
                                        page_action='custom',

                                        filter_action='custom',
                                        filter_query='',

                                        sort_action='custom',
                                        sort_mode='multi',
                                        sort_by=[]
                                    )
                                    ], style={'display': 'inline-block', 'verticalAlign': 'top', 'width': '82vw', 'marginLeft': 10, 'marginRight': 0, 'marginTop': 10, 'marginBottom': 10,}),
                            ]),
                        
                        

                        # Data Table
                        html.Div([

                            dash_table.DataTable(
                            id='table-sorting-filtering',
                            columns=[
                                {'name': i, 'id': i, 'deletable': True} for i in (df.columns)
                            ],
                            page_current= 0,
                            page_size= PAGE_SIZE,
                            page_action='custom',

                            filter_action='custom',
                            filter_query='',

                            sort_action='custom',
                            sort_mode='multi',
                            sort_by=[]
                        )
                        ], style={'width': '500'})
             ])
                

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                return name, operator_type[0].strip(), value

    return [None] * 3

def custom_filter_sort(dff, page_current, page_size, filtering_expressions, sort_by):
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    page = page_current
    size = page_size

    return dff.iloc[page * size: (page + 1) * size].to_dict('records')


@app.callback(
    [
        Output('prefiltered-table-sorting-filtering', 'data'),
        Output('table-sorting-filtering', 'data'),
    ],
    [
        Input('prefiltered-table-sorting-filtering', "page_current"),
        Input('prefiltered-table-sorting-filtering', "page_size"),
        Input('prefiltered-table-sorting-filtering', 'sort_by'),
        Input('prefiltered-table-sorting-filtering', 'filter_query'),

        Input('table-sorting-filtering', "page_current"),
        Input('table-sorting-filtering', "page_size"),
        Input('table-sorting-filtering', 'sort_by'),
        Input('table-sorting-filtering', 'filter_query'),

        Input('dropdown_direction', 'value'),
        Input('dropdown_roi', 'value'),
        Input('dropdown_ticker', 'value'),
        Input('dropdown_timeframe', 'value')
    ]
    )

def update_table(prefiltered_page_current, 
                prefiltered_page_size, 
                prefiltered_sort_by, 
                prefiltered_filter, 
                page_current,
                page_size,
                sort_by,
                filter,
                direction, 
                roi, 
                ticker, 
                timeframe):
    
    prefiltered_filtering_expressions = prefiltered_filter.split(' && ')
    filtering_expressions = filter.split(' && ')

    dff = df 
    dff_prefiltered = df_prefiltered
        
    if direction is not None:
        dff = dff[dff["direction"] == direction]
        dff_prefiltered  = dff_prefiltered[dff_prefiltered["direction"] == direction]
        
    if roi is not None:
        dff_prefiltered = dff_prefiltered[dff_prefiltered["ROI"] == roi]
        dff = dff[dff["ROI"] == roi]
        
    if ticker is not None:
        dff_prefiltered = dff_prefiltered[dff_prefiltered["ticker"] == ticker]
        dff = dff[dff["ticker"] == ticker]
    if timeframe is not None:
        dff_prefiltered = dff_prefiltered[dff_prefiltered["timeframe"] == timeframe]
        dff = dff[dff["timeframe"] == timeframe]



    
    dff_prefiltered = custom_filter_sort(dff_prefiltered, prefiltered_page_current, prefiltered_page_size, prefiltered_filtering_expressions, prefiltered_sort_by)
    dff             = custom_filter_sort(dff, page_current, page_size, filtering_expressions, sort_by)
    
    return [dff_prefiltered, dff]


if __name__ == '__main__':
    app.run_server()
