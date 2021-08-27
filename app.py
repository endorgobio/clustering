import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from dash import no_update
from dash.dependencies import Input, Output, State
import plotly.express as px
from utilities import Node, Cluster, Solution, Instance
import optimiser as opti



# read data
df_clients = pd.read_csv(r'data\data_medium.csv')
#df = pd.read_csv('data_large.csv')
colors_df = pd.read_csv(r'data\colors.csv') # convierte la paleta de colores en lista
colors_list = colors_df['colors'].tolist()



# Define nodes
nodes = []
for row in range(len(df_clients.index)):
  node = Node(int(df_clients.loc[row, "id"]),
                  df_clients.loc[row, "latitude"],
                  df_clients.loc[row, "longitude"],
                  df_clients.loc[row, "demand"])
  nodes.append(node)



# Computes a dictionary of distances
from geopy.distance import distance
distances = {}
# computes the distance for each pair of nodes
for node1 in nodes:
  for node2 in nodes:
    d = distance((node1.lat, node1.long), (node2.lat, node2.long)).m
    key = (node1.id, node2.id)
    distances[key] = d

# Configura optimizador
solvername = 'glpk'
solverpath_exe = 'C:\\glpk-4.65\\w64\\glpsol'

# Define the stylesheets
external_stylesheets = [dbc.themes.BOOTSTRAP,
    #'https://codepen.io/chriddyp/pen/bWLwgP.css'
    'https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap',
    #'https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet'
]

# Creates the app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                external_scripts=['//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML',],
                title="Alternancia",
                suppress_callback_exceptions=True)


# need to run it in heroku
server = app.server

controls_model = dbc.Row([
        dbc.Col(
                [
                    dbc.FormGroup(
                        [
                            html.P("Número de clusters"),
                            dbc.Input(id="n_clusters", type="number", min=1, max=len(df_clients), step=1, value=int(len(df_clients)/10)),
                        ]
                    ),

                ],
                md=4
            ),
            dbc.Col(
                dbc.FormGroup(
                        [
                            html.P("Diferencia porcentual máxima de carga entre zonas"),
                            dbc.InputGroup(
                                [
                                    dbc.Input(id="bal_gen", type="number", min=0, max=100, step=1, value=50,
                                              placeholder="balance"),
                                    dbc.InputGroupAddon("%", addon_type="append"),
                                ],
                                className="mb-3",
                            ),
                        ]
                ),
                md=4
            ),
            dbc.Col([
                    dbc.FormGroup(
                        # dcc.Loading(
                        #     id="loading-1",
                        #     type="default",
                        #     children=dbc.Button("Resolver", id="resolver", className="mr-2", n_clicks=0)
                        # ),
                        dbc.Button("Resolver", id="resolver", className="mr-2", n_clicks=0)
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader("Detalle de la solución "),
                            dbc.ModalBody("No existe solución factible, intente otra combinación de "
                                          "parámetros"),
                            dbc.ModalFooter(
                                # dbc.Button(
                                #     "Close", id="close", className="ml-auto", n_clicks=0
                                # )
                            ),
                        ],
                        id="modal",
                        is_open=False,
                    ),

                    ],
                md=4
            )
    ]),

controls_card = dbc.Card(
                    dbc.CardBody(dbc.Row([
                        dbc.Col([
                                dbc.FormGroup([
                                        html.P("Número de clusters"),
                                        dbc.Input(id="n_clusters", type="number", min=1, max=len(df_clients), step=1, value=int(len(df_clients)/10)),
                                ]),
                                ],
                            md=4
                        ),
                        dbc.Col(
                            dbc.FormGroup([
                                        html.P("Diferencia porcentual máxima de carga entre zonas"),
                                        dbc.InputGroup(
                                            [
                                                dbc.Input(id="bal_gen", type="number", min=0, max=100, step=1, value=50,
                                                          placeholder="balance"),
                                                dbc.InputGroupAddon("%", addon_type="append"),
                                            ],
                                            className="mb-3",
                                        ),
                            ]),
                            md=4
                        ),
                        dbc.Col([
                            dbc.FormGroup(dbc.Button("Resolver", id="resolver", className="mr-2", n_clicks=0)),
                            dbc.Modal([
                                dbc.ModalHeader("Detalle de la solución "),
                                dbc.ModalBody("No existe solución factible, intente otra combinación de "
                                                      "parámetros"),
                                dbc.ModalFooter(
                                            # dbc.Button(
                                            #     "Close", id="close", className="ml-auto", n_clicks=0
                                            # )
                                ),
                                ],
                                id="modal",
                                is_open=False,
                            ),

                                ],
                            md=4
                        )
                    ]),)
                ),

PAGE_SIZE_cluster = 10
PAGE_SIZE_nodes = 10

tab1_content = dbc.Row([
    dbc.Container(controls_card, fluid=True),
    dbc.Container(dbc.Col(dcc.Graph(id="scattermap"), width=12),
                  fluid=True),
    dbc.Container(dbc.Row([
        dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [  # table of students
                            dash_table.DataTable(
                                id='datatable_clusters',
                                columns=[
                                    {"name": i, "id": i} for i in ['nombre', 'centro', 'clientes', 'carga']
                                ],
                                style_table={'overflowX': 'auto'},
                                css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
                                style_cell={
                                    'textAlign': 'left',
                                    'width': '{}%'.format(len(df_clients.columns)),
                                    'textOverflow': 'ellipsis',
                                    'overflow': 'hidden'
                                },
                                style_as_list_view=True,
                                page_current=0,
                                page_size=PAGE_SIZE_cluster,
                                page_action='custom'
                            ),
                        ]
                    )
                ),
            md=6
        ),
        dbc.Col(
            dbc.Card(
                    dbc.CardBody(
                        [  # table of students
                            dash_table.DataTable(
                                id='datatable_nodes',
                                columns=[
                                    {"name": i, "id": i} for i in ['id', 'latitude', 'longitude', 'demand', 'zona']
                                ],
                                style_table={'overflowX': 'auto'},
                                css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
                                style_cell={
                                    'textAlign': 'left',
                                    'width': '{}%'.format(len(df_clients.columns)),
                                    'textOverflow': 'ellipsis',
                                    'overflow': 'hidden'
                                },
                                style_as_list_view=True,
                                page_current=0,
                                page_size=PAGE_SIZE_nodes,
                                page_action='custom'
                            ),
                        ]
                    )
                ),
            md=6
        )
    ]))
])
# tab1_content_t = dbc.Row([
#     # dbc.Row(
#     #     dbc.Col(controls_model)),
#     dbc.Container(controls_card, fluid=True),
#     dbc.Container(
#         dbc.Row([
#             dbc.Col([
#                 dbc.Card(
#                     dbc.CardBody(
#                         [  # table of students
#                             dash_table.DataTable(
#                                 id='datatable_clusters',
#                                 columns=[
#                                     {"name": i, "id": i} for i in ['nombre', 'centro', 'clientes', 'carga']
#                                 ],
#                                 style_table={'overflowX': 'auto'},
#                                 css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
#                                 style_cell={
#                                     'textAlign': 'left',
#                                     'width': '{}%'.format(len(df_clients.columns)),
#                                     'textOverflow': 'ellipsis',
#                                     'overflow': 'hidden'
#                                 },
#                                 style_as_list_view=True,
#                                 page_current=0,
#                                 page_size=PAGE_SIZE_cluster,
#                                 page_action='custom'
#                             ),
#                         ]
#                     )
#                 ),
#                 dbc.Card(
#                     dbc.CardBody(
#                         [  # table of students
#                             dash_table.DataTable(
#                                 id='datatable_nodes',
#                                 columns=[
#                                     {"name": i, "id": i} for i in ['id', 'latitude', 'longitude', 'demand', 'zona']
#                                 ],
#                                 style_table={'overflowX': 'auto'},
#                                 css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
#                                 style_cell={
#                                     'textAlign': 'left',
#                                     'width': '{}%'.format(len(df_clients.columns)),
#                                     'textOverflow': 'ellipsis',
#                                     'overflow': 'hidden'
#                                 },
#                                 style_as_list_view=True,
#                                 page_current=0,
#                                 page_size=PAGE_SIZE_nodes,
#                                 page_action='custom'
#                             ),
#                         ]
#                     )
#                 )],
#                 md=5
#             ),
#             dbc.Col(dcc.Graph(id="scattermap"), width=7),
#         ]),
#         fluid=True
#     ),
#     dbc.Container(
#         dbc.Card(
#             dbc.CardBody([
#                 html.P("El modelo se implementó en python, haciendo uso de la libreria"
#                        "para modelación Pyomo")
#             ])
#         ),
#
#                   fluid=True),
#
#
# ])


# Define the layout
app.layout = dbc.Container([
        html.Div(
            children=[
                html.H1(
                    children="Alternancia escolar", className="header-title"
                ),
                html.P(["Optimización  de jornadas escolares",
                                     html.Br(),
                                     " Modelo de alternancia"],
                    className="header-description",
                ),
            ],
            className="header",
        ),
        dbc.Tabs(
            [
                dbc.Tab(label="La historia", tab_id="historia"),
                dbc.Tab(label="La solución", tab_id="solucion"),
                dbc.Tab(label="Los detalles", tab_id="detalles"),
            ],
            id="tabs",
            active_tab="historia",
        ),
        # Loading allows the spinner showing something is runing
        dcc.Loading(
            id="loading",
            # dcc.Store inside the app that stores the intermediate value
            children=[dcc.Store(id='data_solver_nodes'),
                      dcc.Store(id='data_solver_clusters')]
        ),
        dbc.Container(id="tab-content", className="p-4", fluid=True),
    ],
    fluid=True,
)



# Render the tabs depending on the selection
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
)
def render_tab_content(active_tab):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """
    if active_tab == "historia":
        return tab1_content
    elif active_tab == "solucion":
        return tab1_content
    elif active_tab == "detalles":
        return tab1_content

# Update table with nodes information
@app.callback(
    Output('datatable_nodes', 'data'),
    Input('datatable_nodes', "page_current"),
    Input('datatable_nodes', "page_size"),
    Input('data_solver_nodes', 'data'))
def update_table_nodes(page_current, page_size, jsonified_sol_data):
    data_solver = pd.read_json(jsonified_sol_data, orient='split')
    return data_solver.iloc[page_current*page_size:(page_current+ 1)*page_size].to_dict('records')

# Update table with clusters information
@app.callback(
    Output('datatable_clusters', 'data'),
    Input('datatable_clusters', "page_current"),
    Input('datatable_clusters', "page_size"),
    Input('data_solver_clusters', 'data'))
def update_table_clusters(page_current, page_size, jsonified_sol_data):
    data_solver = pd.read_json(jsonified_sol_data, orient='split')
    print(data_solver)
    return data_solver.iloc[page_current*page_size:(page_current+ 1)*page_size].to_dict('records')


@app.callback(Output('data_solver_nodes', 'data'),
              Output('data_solver_clusters', 'data'),
              Output('modal', 'is_open'),
              Input('resolver', 'n_clicks'),
              State('n_clusters', 'value'),
              State('bal_gen', 'value')
              )
def solve_model(clic_resolver, n_clusters, epsilon):
    instance = Instance(df_clients, nodes, n_clusters, epsilon/100)
    # create model
    model = opti.create_model(instance, distances)
    solution, opt_term_cond = opti.solve_model(instance, distances, model, solvername)
    if opt_term_cond == 'infeasible':
        return no_update, no_update, True
    else:
        data_nodes = solution.dfNodesAssign.to_json(date_format='iso', orient='split')
        data_clusters = solution.dfClustersInfo.to_json(date_format='iso', orient='split')
        print(data_clusters)
        return data_nodes, data_clusters, False


@app.callback(Output('scattermap', 'figure'),
              Input('data_solver_nodes', 'data')
              )
def update_graph(jsonified_sol_data):
    data_solver = pd.read_json(jsonified_sol_data, orient='split')
    zonas = sorted(data_solver['zona'].unique())

    # Draw graph
    map_clients = px.scatter_mapbox(data_solver,
                                 lat="latitude",
                                 lon="longitude",
                                 hover_name="demand",
                                 color="zona",
                                 category_orders={"zona": zonas},
                                 color_continuous_scale=px.colors.cyclical.Edge,
                                 size='demand',
                                 size_max=10,
                                 zoom=10,
                                 height=600)
    map_clients.update_layout(mapbox_style="open-street-map")
    return map_clients














# map_aten.update_traces(marker_color="#000000",
#                    #marker_symbol="star",
#                    selector=dict(type='scattermapbox'))

#map_aten.show()

# main to run the app
if __name__ == "__main__":
    app.run_server(debug=True)