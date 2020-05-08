from scipy.optimize import minimize
from .fermentation_metrics import *
from.two_stage_dfba import *


def productivity_constraint(time_switch, min_productivity, initial_concentrations,
                            time_end, two_stage_fluxes, settings):
    data, time = two_stage_timecourse(initial_concentrations, time_end, *list(time_switch), two_stage_fluxes,
                                      settings.num_timepoints)

    return (batch_productivity(data, time, settings) - min_productivity)/batch_productivity(data, time, settings)


def yield_constraint(time_switch, min_yield, initial_concentrations, time_end, two_stage_fluxes, settings):
    data, time = two_stage_timecourse(initial_concentrations, time_end, *list(time_switch), two_stage_fluxes,
                                      settings.num_timepoints)

    return (batch_yield(data, time, settings) - min_yield)/batch_yield(data, time, settings)


def titer_constraint(time_switch, min_titer, initial_concentrations, time_end, two_stage_fluxes, settings):
    data, time = two_stage_timecourse(initial_concentrations, time_end, *list(time_switch), two_stage_fluxes,
                                      settings.num_timepoints)

    return (batch_end_titer(data, time, settings) - min_titer)/batch_end_titer(data, time, settings)


def optimization_target(time_switch, initial_concentrations, time_end, two_stage_fluxes, objective_fun, settings):
    data, time = two_stage_timecourse(initial_concentrations, time_end, *list(time_switch), two_stage_fluxes,
                                      settings.num_timepoints)

    return -objective_fun(data, time, settings)


def optimal_switch_time(initial_concentrations, time_end, two_stage_fluxes, settings,
                        objective_fun=batch_productivity, min_productivity=0, min_yield=0, min_titer=0):

    constraints = []

    if min_productivity:
        constraints.append({'type': 'ineq', 'fun': productivity_constraint,
                            'args': ([min_productivity, initial_concentrations, time_end, two_stage_fluxes, settings])})

    if min_yield:
        constraints.append({'type': 'ineq', 'fun': yield_constraint,
                            'args': ([min_yield, initial_concentrations, time_end, two_stage_fluxes, settings])})

    if min_titer:
        constraints.append({'type': 'ineq', 'fun': titer_constraint,
                            'args': ([min_titer, initial_concentrations, time_end, two_stage_fluxes, settings])})

    opt_result = minimize(optimization_target, x0=np.array([4]),
                          args=(initial_concentrations, time_end, two_stage_fluxes, objective_fun, settings),
                          options={'maxiter': 200, 'catol': 1e-2}, method='COBYLA', tol=1e-2,
                          constraints=constraints
                          )

    temp_data, temp_time = two_stage_timecourse(initial_concentrations, time_end, opt_result.x[0], two_stage_fluxes,
                                                settings.num_timepoints)

    if opt_result.x[0] <= 0:
        opt_result.x[0] = 0
    elif opt_result.x[0] > temp_time[-1]:
        opt_result.x[0] = temp_time[-1]
    return opt_result


def productivity_constraint_continuous(independent_variables, min_productivity, initial_concentrations, time_end, model,
                                       max_growth, biomass_rxn, substrate_rxn, target_rxn, settings):

    time_switch, stage_one_factor, stage_two_factor = independent_variables
    data, time = two_stage_timecourse_continuous(initial_concentrations, time_end, time_switch, stage_one_factor,
                                                 stage_two_factor, model, max_growth, biomass_rxn, substrate_rxn,
                                                 target_rxn, settings)

    return (batch_productivity(data, time, settings) - min_productivity)/min_productivity


def yield_constraint_continuous(independent_variables, min_yield, initial_concentrations, time_end, model,
                                max_growth, biomass_rxn, substrate_rxn, target_rxn, settings):

    time_switch, stage_one_factor, stage_two_factor = independent_variables
    data, time = two_stage_timecourse_continuous(initial_concentrations, time_end, time_switch, stage_one_factor,
                                                 stage_two_factor, model, max_growth, biomass_rxn, substrate_rxn,
                                                 target_rxn, settings)

    return (batch_yield(data, time, settings) - min_yield)/min_yield


def titer_constraint_continuous(independent_variables, min_titer, initial_concentrations, time_end, model,
                                max_growth, biomass_rxn, substrate_rxn, target_rxn, settings):

    time_switch, stage_one_factor, stage_two_factor = independent_variables
    data, time = two_stage_timecourse_continuous(initial_concentrations, time_end, time_switch, stage_one_factor,
                                                 stage_two_factor, model, max_growth, biomass_rxn, substrate_rxn,
                                                 target_rxn, settings)

    return (batch_end_titer(data, time, settings) - min_titer)/min_titer


def optimization_target_continuous(independent_variables, initial_concentrations, time_end, model, max_growth,
                                   biomass_rxn, substrate_rxn, target_rxn, objective_fun, settings):

    time_switch, stage_one_factor, stage_two_factor = independent_variables
    data, time = two_stage_timecourse_continuous(initial_concentrations, time_end, time_switch, stage_one_factor,
                                                 stage_two_factor, model, max_growth, biomass_rxn, substrate_rxn,
                                                 target_rxn, settings)

    return -objective_fun(data, time, settings)


def optimal_switch_time_continuous(initial_concentrations, time_end, model, max_growth, biomass_rxn, substrate_rxn,
                                   target_rxn, settings, objective_fun=batch_productivity, min_productivity=0,
                                   min_yield=0, min_titer=0, extrema_type='ts_best'):

    constraints = [{'type': 'ineq', 'fun': lambda x: x[1] * 100},
                   {'type': 'ineq', 'fun': lambda x: x[2] * 100},
                   {'type': 'ineq', 'fun': lambda x: (100 - x[1])*100},
                   {'type': 'ineq', 'fun': lambda x: (100 - x[2])*100}]

    initial_guesses = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    if extrema_type == 'os_best':
        initial_guesses = [[0, 3, 3], [0, 50, 50]]
        constraints.append({'type': 'ineq', 'fun': lambda x: (x[1] - x[2])*1000})
        constraints.append({'type': 'ineq', 'fun': lambda x: (x[2] - x[1])*1000})

    if extrema_type == 'ts_sub':
        initial_guesses = [[1, 100, 0], [5, 100, 0]]
        constraints.append({'type': 'ineq', 'fun': lambda x: (x[1] - 100)*100})
        constraints.append({'type': 'ineq', 'fun': lambda x: (0 - x[2])*100})

    if extrema_type == 'ts_best':
        initial_guesses = [[2, 100, 33], [2, 100, 75], [2, 40, 20], [2, 50, 0], [2, 75, 0]]

    if min_productivity:
        constraints.append({'type': 'ineq', 'fun': productivity_constraint_continuous,
                            'args': ([min_productivity, initial_concentrations, time_end, model, max_growth,
                                      biomass_rxn, substrate_rxn, target_rxn, settings])})
    if min_yield:
        constraints.append({'type': 'ineq', 'fun': yield_constraint_continuous,
                            'args': ([min_yield, initial_concentrations, time_end, model, max_growth,
                                      biomass_rxn, substrate_rxn, target_rxn, settings])})

    if min_titer:
        constraints.append({'type': 'ineq', 'fun': titer_constraint_continuous,
                            'args': ([min_titer, initial_concentrations, time_end, model, max_growth,
                                      biomass_rxn, substrate_rxn, target_rxn, settings])})
    opt_results = []
    for i in range(len(initial_guesses)):
        opt_results.append(minimize(optimization_target_continuous, x0=np.array(initial_guesses[i]),
                                    args=(initial_concentrations, time_end, model, max_growth, biomass_rxn,
                                          substrate_rxn, target_rxn, objective_fun, settings),
                                    options={'maxiter': 1000, 'catol': 4e-2}, method='COBYLA', tol=1e-1,
                                    constraints=constraints + [{'type': 'ineq', 'fun': lambda x: (x[1] - 100)*100},
                                                               {'type': 'ineq', 'fun': lambda x: (x[0])*100}]
                                    if (i == 0 and extrema_type == 'ts_best')
                                    else constraints))
    successful_opt_values = [opt.fun for opt in opt_results if opt.success]
    if successful_opt_values:
        opt_result = [opt for opt in opt_results if opt.fun == min(successful_opt_values)][0]
    else:
        opt_result = opt_results[0]
    for opt in opt_results:
        if extrema_type == 'ts_best' and opt and opt.x[1] == 100:
            if abs(abs(opt_result.fun) - abs(opt.fun))/abs(opt_result.fun) < 0.05:
                opt_result = opt

    temp_data, temp_time = two_stage_timecourse_continuous(initial_concentrations, time_end, opt_result.x[0],
                                                           opt_result.x[1], opt_result.x[2], model, max_growth,
                                                           biomass_rxn, substrate_rxn, target_rxn, settings)

    if opt_result.x[0] <= 0:
        opt_result.x[0] = 0
    elif opt_result.x[0] > temp_time[-1]:
        opt_result.x[0] = temp_time[-1]

    return opt_result
