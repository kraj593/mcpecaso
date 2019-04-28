import numpy as np


def growth_dependent_uptake(growth_rate, B=0):
    A = -1
    K = 1
    C = 1
    Q = 1
    v = 1

    return A + (K-A)/(C + Q * np.exp(-B*growth_rate))**(1/v)


def envelope_calculator(model, biomass_rxn, substrate_rxn, target_rxn, k_m=0, n_search_points=20):
    
    production_rates_lb = []
    production_rates_ub = []
    growth_rates = []
    substrate_uptake_rates = []
    substrate_uptake_max = -substrate_rxn.lower_bound
    substrate_uptake_min = 0.5
    max_growth = model.optimize().objective_value

    with model:
        for growth_rate in np.linspace(max_growth, 0, n_search_points):
            biomass_rxn.bounds = (growth_rate, growth_rate)
            if k_m == 0 or growth_rate == max_growth:
                substrate_uptake_rate = substrate_uptake_max
            else:
                substrate_uptake_rate = substrate_uptake_min +\
                                        (substrate_uptake_max-substrate_uptake_min)*\
                                        growth_dependent_uptake(growth_rate, k_m)
            substrate_rxn.lower_bound = -np.around(substrate_uptake_rate+0.0000005, decimals=6)
            model.objective = target_rxn.id
            growth_rates.append(growth_rate)
            substrate_uptake_rates.append(substrate_uptake_rate)
            sol_min = model.optimize(objective_sense='minimize')
            if model.solver.status != 'optimal':
                print("Min Solver wasn't feasible for Growth Rate: ", growth_rate,
                      " with uptake rate: ", substrate_uptake_rate)
                production_rates_lb.append(0)
            else:
                production_rates_lb.append(sol_min.objective_value)
            sol_max = model.optimize(objective_sense='maximize')
            production_rates_ub.append(model.optimize(objective_sense='maximize').objective_value)
            if model.solver.status != 'optimal':
                print("Max Solver wasn't feasible for Growth Rate: ", growth_rate,
                      " with uptake rate: ", substrate_uptake_rate)
                production_rates_lb.append(0)
            else:
                production_rates_lb.append(sol_max.objective_value)
    yield_lb = list(np.divide(production_rates_lb, substrate_uptake_rates))
    yield_ub = list(np.divide(production_rates_ub, substrate_uptake_rates))

    data = dict(zip(['growth_rates', 'substrate_uptake_rates',
                     'production_rates_lb', 'production_rates_ub', 'yield_lb', 'yield_ub'],
                    [growth_rates, substrate_uptake_rates,
                     production_rates_lb, production_rates_ub, yield_lb, yield_ub]))
    
    return data
