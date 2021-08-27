import pandas as pd
from pyomo.environ import *
from pyomo.opt import *
from utilities import Cluster, Solution

def create_model(instance, # dataframe with clients data
                 distances, # dictionary of distances
                 ):
    # Create el modelo
    model = ConcreteModel()

    # Define sets
    model.CLIENTES = Set(initialize=instance.df.id)

    # Define decision variables
    model.y = Var(model.CLIENTES, domain=Binary) # cluster centers
    model.x = Var(model.CLIENTES, model.CLIENTES, domain=Binary) # assignment to ceneters


    # Demand
    # Create demand dictionary
    demanda = dict(zip(instance.df.id, instance.df.demand))
    model.demanda = Param(model.CLIENTES, initialize = demanda)
    # Distance
    model.distancia = Param(model.CLIENTES, model.CLIENTES, initialize = distances)
    # Number of clusters
    model.n_clusters = Param(initialize=instance.n_clusters)
    model.epsilon = Param(initialize=instance.epsilon)
    carga_media = sum(demanda.values()) / instance.n_clusters
    model.cargam = Param(initialize = carga_media)


    # Define objective function
    def value_rule(model):
      return sum(sum(model.distancia[i,j] * model.x[i,j] for i in model.CLIENTES) for j in model.CLIENTES)
    model.total_value = Objective(sense=minimize, rule=value_rule)

    # Define constraints
    # Each client is assigned to one cluster
    def asign_rule(model, i):
      return sum(model.x[i,j] for j in model.CLIENTES) == 1
    model.asign = Constraint(model.CLIENTES, rule=asign_rule)

    # number of clusters
    def nacopios_rule(model):
      return sum(model.y[j] for j in model.CLIENTES) == model.n_clusters
    model.nacopios = Constraint( rule=nacopios_rule)

    # assignment only to open centers
    def relvar_rule(model, i, j):
      return model.y[j] >= model.x[i,j]
    model.relvar = Constraint(model.CLIENTES, model.CLIENTES, rule=relvar_rule)

    # balance constraints
    def cargamedia1_rule(model, j):
      return sum(model.demanda[i]*model.x[i,j] for i in model.CLIENTES) <= (1 + instance.epsilon) * model.cargam * model.y[j]
    model.cargamedia1 = Constraint(model.CLIENTES, rule=cargamedia1_rule)

    def cargamedia2_rule(model, j):
      return sum(model.demanda[i]*model.x[i,j] for i in model.CLIENTES) >= (1 - instance.epsilon) * model.cargam * model.y[j]
    model.cargamedia2 = Constraint(model.CLIENTES, rule=cargamedia2_rule)

    return model


def solve_model(instance, distances, model, solver_name, solver_path=None):
    if solver_path == None:
        solver = SolverFactory(solver_name)
    else:
        solver = SolverFactory(solver_name, executable=solver_path)

    # set time limit
    solver.options['tmlim'] = 5
    # Resuelve el modelo
    solver.solve(model, options_string="mipgap=0.02")
    # solve the model
    results = solver.solve(model)
    term_cond = results.solver.termination_condition
    if term_cond==TerminationCondition.feasible or term_cond==TerminationCondition.optimal:
        # Obtener función objetivo
        obj_val = model.total_value.expr()
        # Creates solution
        solution = Solution(instance.n_clusters, instance.df)
        # Crea un cluster centrado en cada acopio abierto
        res = model.y.get_values()
        for key, value in res.items():
            if value > 0:
                cluster = Cluster(instance.nodes[key - 1])
                solution.clusters_list.append(cluster)
                # Listado de id de los acopios
                id_acopios = [cluster.center.id for cluster in solution.clusters_list]
        # Asigna cada nodo al cluster asociado a su acopio
        res = model.x.get_values()
        for key, value in res.items():
            if value > 0:
                # posicion del cluster con centre en j en el arreglo de clusters
                posicion = id_acopios.index(key[1])
                if key[0] not in id_acopios:
                    solution.clusters_list[posicion].node_list.append(instance.nodes[key[0] - 1])

        # Computes cluster measurements
        for cluster in solution.clusters_list:
            cluster.get_measures(distances)

        # get dataframe to print
        solution.get_dataframes()

        # return solution
        return solution, term_cond

    else:
        return None, term_cond





