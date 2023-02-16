import pyomo.environ as pyo
from pyomo.environ import *

def uc(G,T,c,Piecewise,Pmax,Pmin,TU,TD,De,Re, FixShedu,Relax,Shedule_dict):
    model     = pyo.ConcreteModel(name="(UC)")

    if(Relax == False): #Si se desea relajar las variables enteras
        model.u   = pyo.Var( G , T , within=Binary)
        model.v   = pyo.Var( G , T , within=Binary )
        model.w   = pyo.Var( G , T , within=Binary )
    else:        
        model.u   = pyo.Var( G , T , bounds=(0.0,1.0))
        model.v   = pyo.Var( G , T , bounds=(0.0,1.0))
        model.w   = pyo.Var( G , T , bounds=(0.0,1.0))
    model.p   = pyo.Var( G , T , bounds=(0.0,999999.0))
    model.pb  = pyo.Var( G , T , bounds=(0.0,999999.0))
    model.pc  = pyo.Var( G , T , bounds=(0.0,999999.0))
    model.cp  = pyo.Var( G , T , bounds=(0.0,9999999.0))
    model.ex  = pyo.Var( T , bounds=(0.0,9999999.0))
    model.ex2 = pyo.Var( T , bounds=(0.0,9999999.0))
    Penalty = 999999999999.0    

    if(FixShedu == True): #Si se desea usar la solución fixed
        model.u.fix(0)
        model.u.set_values(Shedule_dict)

    #Costo en punto medio
    def obj_rule(model):
        return sum(c[g] * model.p[g,t] for g in G for t in T) \
             + sum(Penalty * model.ex[t] for t in T) \
             + sum(Penalty * model.ex2[t] for t in T)
    model.obj = pyo.Objective(rule = obj_rule)

    #Costo en piecewise
    # def obj_rule(model):
    #     return sum(model.cp[g,t] for g in G for t in T) \
    #         + sum(Penalty * model.ex[t] for t in T) \
    #         + sum(Penalty * model.ex2[t] for t in T)
    # model.obj = pyo.Objective(rule = obj_rule)

    def pow_min_rule(model,g,t): # min
        return model.p[g,t] >= Pmin[g] * model.u[g,t]
    model.pow_min = pyo.Constraint(G,T, rule = pow_min_rule)

    def pow_pow_rule(model,g,t): # pow_pow
        return model.pb[g,t] >= model.p[g,t]
    model.pow_pow = pyo.Constraint(G,T, rule = pow_pow_rule)

    def pow_max_rule(model,g,t): # max
        return model.pb[g,t] <= Pmax[g] * model.u[g,t]
    model.pow_max = pyo.Constraint(G,T, rule = pow_max_rule)    

    def demand_rule(model,t):   # demand 
        return sum( model.p[g,t] for g in G) + model.ex[t] >= De[t] 
    model.demand = pyo.Constraint(T, rule = demand_rule)

    def reserve_rule(model,t):  # demand + reserve
        return sum( model.pb[g,t] for g in G) + model.ex2[t] >= De[t] + Re[t] 
    model.reserve = pyo.Constraint(T, rule = reserve_rule)

    def logical_rule(model,g,t):  # logical
        if t == 0:
            return pyo.Constraint.Skip
        else:
            return model.u[g,t] - model.u[g,t-1] == model.v[g,t] - model.w[g,t]
    model.logical = pyo.Constraint(G,T,rule = logical_rule)

    def mut_rule(model,g,t):  # minimum-up time
        if t < value(TU[g]):
            return pyo.Constraint.Skip            
        else:      
            return sum( model.v[g,i] for i in range(t-value(TU[g])+1,t)) <= model.u[g,t] 
    model.mut = pyo.Constraint(G,T, rule = mut_rule)
    
    # def uptime_rule(m,g,t):
    #     if t < value(m.ScaledMinimumUpTime[g]):
    #         return Constraint.Skip
    #     if m.status_vars in ['ALS_state_transition_vars']:
    #         return sum(m.UnitStart[g,i] for i in range(t-value(m.ScaledMinimumUpTime[g])+1, t)) <= m.UnitStayOn[g,t] 
    #     else:
    #         return sum(m.UnitStart[g,i] for i in range(t-value(m.ScaledMinimumUpTime[g])+1, t+1)) <= m.UnitOn[g,t] 
    
    # model.UpTime = Constraint(model.ThermalGenerators, model.TimePeriods, rule=uptime_rule)
    
    def mdt_rule(model,g,t):  # minimum-down time
        if t < value(TD[g]):
            return pyo.Constraint.Skip            
        else:      
            return sum( model.w[g,i] for i in range(t-value(TD[g])+1,t)) <= 1-model.u[g,t] 
    model.mdt = pyo.Constraint(G,T, rule = mdt_rule)

    #     def downtime_rule(m, g, t):
    #     if t < value(m.ScaledMinimumDownTime[g]):
    #         return Constraint.Skip
    #     if t == value(m.ScaledMinimumDownTime[g]):
    #         return sum(m.UnitStart[g, i] for i in range(t-value(m.ScaledMinimumDownTime[g])+1, t+1)) <= 1 - m.UnitOnT0[g]
    #     else:
    #         return sum(m.UnitStart[g, i] for i in range(t-value(m.ScaledMinimumDownTime[g])+1, t+1)) <= 1 - m.UnitOn[g, t-value(m.ScaledMinimumDownTime[g])]
    # model.DownTime = Constraint(
    #     model.ThermalGenerators, model.TimePeriods, rule=downtime_rule)

    # # compute the per-generator, per-time period production costs. We'll do this by hand
    # def piecewise_production_costs_index_set_generator(model):
    #     return ((g,t,i) for g in G for t in T for i in range(len(Piecewise[g,t])-1))
    # model.PiecewiseProductionCostsIndexSet = Set(initialize=piecewise_production_costs_index_set_generator, dimen=3)
    
    # def _production_cost_function(model, g, t, i):
    #     return model.PowerGenerationPiecewiseCostValues[g,t][i]

    def piecewise_rule(model,g,t,l):  # piecewise production costs
        # x0 = m.PowerGenerationPiecewisePoints[g,t][i]
        # x1 = m.PowerGenerationPiecewisePoints[g,t][i+1]
        # y0 = _production_cost_function(m,g,t,i)
        # y1 = _production_cost_function(m,g,t,i+1)
        # slope = (y1 - y0)/ (x1 - x0) 
        # intercept = -slope*x0 + y0
        slope = c[g]
        intercept = 0
        return model.cp[g,t] >= slope * model.p[g,t] + intercept * model.u[g,t] 
    model.piecewise = Constraint(G,T,Piecewise, rule=piecewise_rule)
    # model.piecewise = pyo.Constraint(G,T, rule = piecewise_rule)

    # def piecewise_production_cost_rule(m, g, t, i):

    #     x0 = m.PowerGenerationPiecewisePoints[g,t][i]
    #     x1 = m.PowerGenerationPiecewisePoints[g,t][i+1]
    #     y0 = _production_cost_function(m,g,t,i)
    #     y1 = _production_cost_function(m,g,t,i+1)
    #     slope = (y1 - y0)/ (x1 - x0) 
    #     intercept = -slope*x0 + y0

    #     # this will be good regardless
    #     return m.ProductionCost[g,t] >= slope*m.PowerGeneratedAboveMinimum[g,t] + intercept*m.UnitOn[g,t]

    # model.ProductionCostConstr = Constraint(model.PiecewiseProductionCostsIndexSet, rule=piecewise_production_cost_rule)

    # _compute_total_production_cost(model)

    return model