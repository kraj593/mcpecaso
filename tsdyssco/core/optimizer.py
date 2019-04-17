from scipy.optimize import minimize_scalar
from .fermentation_metrics import *
from.two_stage_dfba import *


def optimization_target(time_switch, initial_concentrations, time_end, two_stage_fluxes, objective_fun):
    data, time = two_stage_timecourse(initial_concentrations, time_end, time_switch, two_stage_fluxes)
    return -objective_fun(data, time)


def optimal_switch_time(initial_concentrations, time_end, two_stage_fluxes, objective_fun=batch_productivity):

    opt_result = minimize_scalar(optimization_target,
                                 args=(initial_concentrations, time_end, two_stage_fluxes, objective_fun),
                                 bounds=[0, time_end], options={'maxiter': 1000000}, method='brent')

    temp_data, temp_time = two_stage_timecourse(initial_concentrations, time_end, opt_result.x, two_stage_fluxes)

    if opt_result.x <= 0:
        opt_result.x = 0
    elif opt_result.x > temp_time[-1]:
        opt_result.x = temp_time[-1]
    return opt_result


