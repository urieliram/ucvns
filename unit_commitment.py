# --------------------------------------------------------------------------------
# File: unit_commitment.py
# Developers: Uriel Iram Lezama Lope
# Purpose: Solve a basic Unit Commitment Problem
# --------------------------------------------------------------------------------
import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import results
from pyomo.opt.results import solver
from pyomo.util.infeasible import log_infeasible_constraints
from pyomo.opt import SolverStatus, TerminationCondition
import uc


def solve(G1, T1, c, Piecewise, Pmax, Pmin, TU, TD, De, Re, FixShedu, Relax, U, ambiente):
    G = []
    T = []
    for g in range(0, G1):
        G.append(g)
    for t in range(0, T1):
        T.append(t)

    # T = [1, 2, 3, 4]
    # G = [1, 2]
    # c = [10, 5]
    # De = [160,160,160,160]
    # Re = [10,10,10,10]
    # Pmax = [50, 90]
    # Pmin = [30, 20]

    # Aquí se pasa de la solución en arreglo U a una solución en diccionario
    Shedule_dict = {}
    for g in range(len(G)):
        for t in range(len(T)):
            Shedule_dict[g, t] = U[g][t]    

    # print("Shedule_dict")
    # print(Shedule_dict)

    # aqui se pasan de arreglos a diccionarios como los lee Pyomo
    c_dict = dict(zip(G, c))
    Pmax_dict = dict(zip(G, Pmax))
    Pmin_dict = dict(zip(G, Pmin))
    De_dict = dict(zip(T, De))
    Re_dict = dict(zip(T, Re))
    TU_dict = dict(zip(G, TU))
    TD_dict = dict(zip(G, TD))

    # Create the Pyomo model
    model = uc.uc(G, T, c_dict, Piecewise, Pmax_dict, Pmin_dict,
                  TU_dict, TD_dict, De_dict, Re_dict, FixShedu, Relax, Shedule_dict)

    # Create the solver interface and solve the model
    # solver = pyo.SolverFactory('glpk')
    #solver = pyo.SolverFactory('cbc')
    #https://www.ibm.com/docs/en/icos/12.8.0.0?topic=parameters-relative-mip-gap-tolerance
    if ambiente == "thinkpad":
        solver = pyo.SolverFactory('cplex', executable='/opt/ibm/ILOG/CPLEX_Studio1210/cplex/bin/x86-64_linux/cplex')
    if ambiente == "yalma":
        solver = pyo.SolverFactory('cplex', executable='/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex')
    solver.options['mip tolerances mipgap'] = 0.01  
    #solver.options['mip tolerances absmipgap'] = 200
    solver.options['timelimit'] = 300
    res = solver.solve(model, tee=False) #, timelimit=10 tee=True ver log

    try:
        pyo.assert_optimal_termination(res)
    except:
        print("An exception occurred")
        return None
            
    # model.obj.pprint() # Print the objetive function
    # model.demand.pprint()  Print constraint
    # model.reserve.pprint()
    # model.display()      # Print the optimal solution

    file = open("modeluc.txt", "w")
    file.write('z: %s \n' % (pyo.value(model.obj)))
    file.write('TIME, GEN,\t u, \t p \n')
    for t in range(0, T1):
        for g in range(0, G1):
            file.write('%s, %s,\t  %s,\t %s \n' %
                       (int(t), int(g), int(model.u[(g, t)].value), model.p[(g, t)].value))

    file.write('TIME,\t ex \t ex2 \n')
    for t in range(0, T1):
        file.write('%s, \t%s,\t %s,\t \n' %
                   (int(t), model.ex[t].value, model.ex2[t].value))
    file.close()
    
    #https://stackoverflow.com/questions/51044262/finding-out-reason-of-pyomo-model-infeasibility
    log_infeasible_constraints(model)

    #https://pyomo.readthedocs.io/en/stable/working_models.html
    if (res.solver.status == SolverStatus.ok) and (res.solver.termination_condition == TerminationCondition.optimal):
        print ("this is feasible and optimal")
        return model
    elif res.solver.termination_condition == TerminationCondition.infeasible:
        print (">>> do something about it? or exit?")
        return None
    else:
        print ("something else is wrong",str(res.solver))  # something else is wrong
        return None

    
    # z = pyo.value(model.obj)

    
