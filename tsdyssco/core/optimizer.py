from scipy.optimize import minimize
from .fermentation_metrics import *
from.two_stage_dfba import *


def optimization_target(time_switch, initial_concentrations, time_end, two_stage_fluxes, objective_fun, settings):
    data, time = two_stage_timecourse(initial_concentrations, time_end, *list(time_switch), two_stage_fluxes,
                                      settings.num_timepoints)
    return -objective_fun(data, time, settings)


def optimal_switch_time(initial_concentrations, time_end, two_stage_fluxes, settings, objective_fun=batch_productivity):

    opt_result = minimize(optimization_target, x0=np.array([4]),
                          args=(initial_concentrations, time_end, two_stage_fluxes, objective_fun, settings),
                          options={'maxiter': 1000000}, method='COBYLA')

    temp_data, temp_time = two_stage_timecourse(initial_concentrations, time_end, opt_result.x[0], two_stage_fluxes,
                                                settings.num_timepoints)

    if opt_result.x[0] <= 0:
        opt_result.x[0] = 0
    elif opt_result.x[0] > temp_time[-1]:
        opt_result.x[0] = temp_time[-1]
    return opt_result


