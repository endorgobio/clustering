import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from dash import no_update
from dash.dependencies import Input, Output, State
import plotly.express as px
from plotly import graph_objs as go
from utilities import Node, Cluster, Solution, Instance
import optimiser as opti
from geopy.distance import distance
import os
import json


# read data
df_clients = pd.read_csv(r'https://raw.githubusercontent.com/endorgobio/clustering/master/data/data_medium.csv')
#df_clients = pd.read_csv('data/data_large.csv')

# Define nodes
nodes = []
for row in range(len(df_clients.index)):
    node = Node(int(df_clients.loc[row, "id"]),
                  df_clients.loc[row, "latitude"],
                  df_clients.loc[row, "longitude"],
                  df_clients.loc[row, "demand"])
    nodes.append(node)

# Computes a dictionary of distances

distances = {}
# computes the distance for each pair of nodes
for node1 in nodes:
    for node2 in nodes:
        d = distance((node1.lat, node1.long), (node2.lat, node2.long)).m
        key = (node1.id, node2.id)
        distances[key] = d

# Set up optimiser
solvername = 'glpk'
solverpath_exe = 'C:\\glpk-4.65\\w64\\glpsol'
solverpath_exe = 'D:\\glpk-4.65\\w64\\glpsol'

# Define the stylesheets
external_stylesheets = [dbc.themes.BOOTSTRAP,
    #'https://codepen.io/chriddyp/pen/bWLwgP.css'
    'https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap',
    #'https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet'
]

# Creates the app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                external_scripts=['//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML',],
                title="Zonificación",
                suppress_callback_exceptions=True)


# needed to run it in heroku
server = app.server

# narratives
filepath = os.path.split(os.path.realpath(__file__))[0]
# narrative tab1
historia_text = open(os.path.join(filepath, "laHistoria.md"), "r").read()
# narrative tab3
detalles_text = open(os.path.join(filepath, "losDetalles.md"), "r").read()
# modelo
f = open('modelo.json', )
# returns JSON object as
# a dictionary
data = json.load(f)

# creates control for tab2
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
                                        html.P("Número de zonas"),
                                        dbc.Input(id="n_clusters", type="number", min=1, max=len(df_clients), step=1, value=int(len(df_clients)/10)),
                                ]),
                                ],
                            md=4
                        ),
                        dbc.Col(
                            dbc.FormGroup([
                                        html.P("% de diferencia de carga entre zonas"),
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
                            dbc.FormGroup(dbc.Button("Resolver", id="resolver", className="mr-2", n_clicks=0)),


                                ],
                            align="end",
                            md=4
                        )
                    ]),)
                ),

# tab contents
tab1_content = dbc.Row([
        dbc.Col(dcc.Markdown(historia_text, dangerously_allow_html=True), md=8),
        dbc.Col(html.Div([
            #html.Img(src="/assets/images/banner_blue_text.png", className='banner_subsection'),
            html.Div(
                html.P("Los retos", className="header-description"),
                #className="header_subsection1"
            ),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "Visualizar la asignación de pacientes por zona en un mapa",
                        style={'textAlign': 'justify'},
                        className="card-text",
                    ),
                ])
            ]),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "Crear un modelo que asigne zonas a los terapeutas balanceando las"
                        "cargas de trabajo",
                        style={'textAlign': 'justify'},
                        className="card-text",
                    ),
                ])
            ]),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "Resolver el modelo con un optimizador no comercial",
                        style={'textAlign': 'justify'},
                        className="card-text",
                    ),
                ])
            ]),
        ]),
            md=4),
    ]
)

# number of rows per page in datatables
PAGE_SIZE_cluster = 10
PAGE_SIZE_nodes = 10
tab2_content = dbc.Row([
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

tab3_content = dbc.Row([
    dbc.Col(
        html.Div(id='static', children=[
            html.P("Detras de la zonificación de los pacientes para ser asignados al personal"
                   "asistencial hay un modelo  matemático que genera información que ayuda a "
                   "tomar dicha decisión. Este es el modelo:"),
            dbc.Card([
                # dbc.CardImg(src="https://source.unsplash.com/daily", top=True),
                # dbc.CardImg(src="/assets/images/banner_blue.png", top=True),
                dbc.CardBody([
                    dcc.Markdown('''
                        Sea `P` el conjunto de pacientes, cada uno de ellos con una demanda estimada de
                         tiempo de servicio `t`. Considere la distancia `d` entre cada par de pacientes y `k` 
                         como el número de zonas que deben crearse. La carga de trabajo estimada para cada zona
                         puede calcularse como la suma total de las cargas `t` sobre el número de zonas `k`. Considere
                         ademas &epsilon; como el porcentaje máximo tolerable de diferencia entre la carga de trabajo de
                         una zona y la carga promedio esperada.  

                        Asumiremos que cada una de las zonas se crea entorno a uno de los pacientes. Para ello, 
                        considere la variable `y` que indica si un paciente dado es el centro de una de las `k`
                        zonas; la variable `x` determina a cual de las zonas creadas es asignado cada paciente
                    '''),
                    dcc.Markdown(''' La función busca crear zonas compactas minimizando la suma de  la distancia  de los 
                    pacientes al centro de sus zonas. '''),
                    data['objetivo'],
                    dcc.Markdown(''' Garantizando que: '''),
                    dcc.Markdown(''' Cada paciente es asignado a una zona. '''),

                    data['restriccion1'],
                    dcc.Markdown(''' Se crean tantas zonas cómo indica el parámetro `k` '''),
                    data['restriccion2'],
                    dcc.Markdown(''' Se identifica la localización de un paciente como el centro de cada zona y los pacientes 
                        se asignan solo a dichas zonas'''),
                    data['restriccion3'],
                    dcc.Markdown(''' La carga de trabajo de cada zona solo puede desviarse un &epsilon; % del valor promedio
                    de la carga '''),
                    data['restriccion4'],
                    data['restriccion5'],
                ])
            ]),
        ]),
        md=8),
    dbc.Col(
        [
            dbc.Card(
                dbc.CardBody([
                    html.P("El modelo se implementó en python, haciendo uso de la libreria "
                           "para modelación Pyomo")
                ])
            ),
            dbc.Card(
                dbc.CardBody([
                    html.P("El solver empleado para resolver el modelo fue glpk, cuyo uso  para "
                           "fines no comerciales esta regulado the por el acuerdo 'GNU General Public License'")
                ])
            ),
            dbc.Card(
                dbc.CardBody([
                    html.P("La visualización de los resultados del modelo se implemento haciendo uso del framework "
                           "dash soportado plotly para las gráficas y visualizaciones'")
                ])
            )
        ],
        md=4
    ),
]
)


tabs_styles = {
    'height': '44px',
    'align-items': 'center'
}

tab_label_style = {
    'color' : 'black'
}

activetab_label_style = {
    'color': '#FD6E72',
    'fontWeight': 'bold'
}


# Define the layout
app.layout = dbc.Container([
        dbc.Row(html.Img(src='assets/images/imagenBanner_Zonificacion1.jpg', style={'width':'100%'})),
        # html.Div(
        #     children=[
        #
        #         html.H1(
        #             children="Zonificación", className="header-title"
        #         ),
        #         html.P(["Creación de zonas para personal médico domiciliario",
        #                              html.Br(),
        #                              " Balance de carga"],
        #             className="header-description",
        #         ),
        #     ],
        #     # style={'background-image': 'assets/IMAGES/imagenBanner_Zonificacion1.jpg'},
        #     className="header",
        # ),
        dbc.Tabs(
            children=[
                dbc.Tab(label="La historia", tab_id="historia", label_style=tab_label_style, active_label_style=activetab_label_style),
                dbc.Tab(label="La solución", tab_id="solucion", label_style=tab_label_style, active_label_style=activetab_label_style),
                dbc.Tab(label="Los detalles", tab_id="detalles",  label_style=tab_label_style, active_label_style=activetab_label_style),
            ],
            id="tabs",
            active_tab="historia",
            style=tabs_styles
        ),
        # Loading allows the spinner showing something is runing
        dcc.Loading(
            id="loading",
            # dcc.Store inside the app that stores the intermediate value
            children=[dcc.Store(id='data_solver_nodes'),
                      dcc.Store(id='data_solver_clusters')]
        ),
        dbc.Container(id="tab-content", className="p-4", fluid=True),
        dbc.Row(html.Img(src='assets/images/footnote.png', style={'width':'100%'})),
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
        return tab2_content
    elif active_tab == "detalles":
        return tab3_content


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
    solution, opt_term_cond = opti.solve_model(instance, distances, model, solvername)#, solverpath_exe)
    if opt_term_cond == 'infeasible':
        return no_update, no_update, True
    else:
        data_nodes = solution.dfNodesAssign.to_json(date_format='iso', orient='split')
        data_clusters = solution.dfClustersInfo.to_json(date_format='iso', orient='split')
        return data_nodes, data_clusters, False


# Update map
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
                                    #hover_name="demand",
                                    hover_data={'id': True,  # remove species from hover data
                                                'zona': True,
                                                'demand': True,
                                                'latitude': False,
                                                'longitude': False
                                                },
                                    labels={'id': 'paciente ',
                                            'demand': 'demanda'},
                                    color="zona",
                                    category_orders={"zona": zonas},
                                    color_continuous_scale=px.colors.cyclical.Edge,
                                    size='demand',
                                    size_max=10,
                                    zoom=10,
                                    height=600)
    map_clients.update_layout(mapbox_style="open-street-map",)
    return map_clients


# main to run the app
if __name__ == "__main__":
    app.run_server(debug=True)