from scipy.optimize import minimize
from .fermentation_metrics import *
from.two_stage_dfba import *


def constraint_function(time_switch, min_productivity, min_yield, min_titer, initial_concentrations,
                        time_end, two_stage_fluxes, settings):
    data, time = two_stage_timecourse(initial_concentrations, time_end, *list(time_switch), two_stage_fluxes,
                                      settings.num_timepoints)

    return ((batch_productivity(data, time, settings) - min_productivity) *
            (batch_yield(data, time, settings) - min_yield) *
            (batch_end_titer(data, time, settings) - min_titer))


def optimization_target(time_switch, initial_concentrations, time_end, two_stage_fluxes, objective_fun, settings):
    data, time = two_stage_timecourse(initial_concentrations, time_end, *list(time_switch), two_stage_fluxes,
                                      settings.num_timepoints)

    return -objective_fun(data, time, settings)


def optimal_switch_time(initial_concentrations, time_end, two_stage_fluxes, settings,
                        min_productivity=0, min_yield=0, min_titer=0, objective_fun=batch_productivity):

    opt_result = minimize(optimization_target, x0=np.array([4]),
                          args=(initial_concentrations, time_end, two_stage_fluxes, objective_fun, settings),
                          options={'maxiter': 1000000}, method='COBYLA',
                          constraints={'type': 'ineq', 'fun': constraint_function,
                                       'args': ([min_productivity, min_yield, min_titer, initial_concentrations,
                                                time_end, two_stage_fluxes, settings])})

    temp_data, temp_time = two_stage_timecourse(initial_concentrations, time_end, opt_result.x[0], two_stage_fluxes,
                                                settings.num_timepoints)

    if opt_result.x[0] <= 0:
        opt_result.x[0] = 0
    elif opt_result.x[0] > temp_time[-1]:
        opt_result.x[0] = temp_time[-1]
    return opt_result


