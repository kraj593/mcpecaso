import numpy as np
import warnings


def logistic_uptake(growth_rate, **kwargs):

    params = {'A': -1, 'K': 1, 'C': 1, 'Q': 1, 'v': 1, 'B': 0, 'min_sub': 0.5, 'max_sub': 10}

    for arg in kwargs:
        if arg in ['A', 'K', 'C', 'Q', 'v', 'B']:
            params[arg] = kwargs[arg]
        else:
            warnings.warn('One or more of the parameters specified in the settings is(are) not recognized and was(were'
                          ' ignored. Please check documentation for a list of acceptable parameters for the specified '
                          'uptake function.')

    if params['B'] == 0:

        return params['max_sub']

    else:
        logistic = params['A'] + (params['K'] - params['A']) / \
           (params['C'] + params['Q'] * np.exp(-params['B'] * growth_rate))**(1 / params['v'])

        return params['min_sub'] + (params['max_sub'] - params['min_sub'])*logistic


def linear_uptake(growth_rate, **kwargs):

    params = {'m': 10, 'c': 0.5, 'max_sub':10}

    for arg in kwargs:
        if arg in ['m', 'c']:
            params[arg] = kwargs[arg]
        else:
            warnings.warn('One or more of the parameters specified in the settings is(are) not recognized and was(were'
                          ' ignored. Please check documentation for a list of acceptable parameters for the specified '
                          'uptake function.')

    if params['m'] * growth_rate + params['c'] > 10:
        return 10
    else:
        return params['m'] * growth_rate + params['c']


def envelope_calculator(model, biomass_rxn, substrate_rxn, target_rxn, settings):

    n_search_points = settings.num_points
    production_rates_lb = []
    production_rates_ub = []
    growth_rates = []
    substrate_uptake_rates = []
    max_growth = model.optimize().objective_value

    uptake_dict = {'linear': linear_uptake, 'logistic': logistic_uptake}

    if settings.uptake_fun in uptake_dict.keys():
        uptake_fun = uptake_dict[settings.uptake_fun]
    else:
        raise KeyError('Unknown substrate uptake function specified. Only ', [fun for fun in uptake_dict.keys()],
                       'are acceptable uptake functions.')

    with model:
        for growth_rate in np.linspace(max_growth, 0, n_search_points):
            biomass_rxn.bounds = (growth_rate, growth_rate)
            model.objective = substrate_rxn.id
            min_feasible_uptake = model.optimize(objective_sense='maximize').objective_value
            sub_model_prediction = -np.around(uptake_fun(growth_rate, **settings.uptake_params)+0.0000005, decimals=6)
            if sub_model_prediction <= min_feasible_uptake:
                substrate_uptake_rate = sub_model_prediction
            else:
                warnings.warn('The parameters used with the model for substrate uptake resulted in rates that are lower'
                              ' than thee minimum feasible uptake for one or more cases. The minimum feasible uptake'
                              ' rate was used in these cases')
                substrate_uptake_rate = min_feasible_uptake

            substrate_rxn.lower_bound = substrate_uptake_rate
            model.objective = target_rxn.id
            growth_rates.append(growth_rate)
            substrate_uptake_rates.append(-substrate_uptake_rate)
            sol_min = model.optimize(objective_sense='minimize')
            if model.solver.status != 'optimal':
                print("Min Solver wasn't feasible for Growth Rate: ", growth_rate,
                      " with uptake rate: ", substrate_uptake_rate)
                production_rates_lb.append(0)
            else:
                production_rates_lb.append(sol_min.objective_value)
            sol_max = model.optimize(objective_sense='maximize')
            if model.solver.status != 'optimal':
                print("Max Solver wasn't feasible for Growth Rate: ", growth_rate,
                      " with uptake rate: ", substrate_uptake_rate)
                production_rates_ub.append(0)
            else:
                production_rates_ub.append(sol_max.objective_value)
    yield_lb = list(np.divide(production_rates_lb, substrate_uptake_rates))
    yield_ub = list(np.divide(production_rates_ub, substrate_uptake_rates))

    data = dict(zip(['growth_rates', 'substrate_uptake_rates',
                     'production_rates_lb', 'production_rates_ub', 'yield_lb', 'yield_ub'],
                    [growth_rates, substrate_uptake_rates,
                     production_rates_lb, production_rates_ub, yield_lb, yield_ub]))
    
    return data
