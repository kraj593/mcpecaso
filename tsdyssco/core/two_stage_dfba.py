import numpy as np
from scipy.integrate import odeint
import warnings


def crop_dfba_timecourse_data(dfba_data, t):
    
    """This function takes in dFBA data and timepoints and crops them to the point where substrate
    is over. dFBA data should be in the format: [[biomass,substrate,product]...] and timepoints are
    a list of timepoints."""
    
    if any(dfba_data[:, 1] <= 0):
        substrate_consumed_index = np.where(dfba_data[:, 1] <= 0)[0][0]
    else:
        substrate_consumed_index = len(t) - 1
    return dfba_data[:substrate_consumed_index + 1], t[:substrate_consumed_index + 1]


def dfba_fun(concentrations, time, fluxes):

    """This function returns the time derivatives for biomass, substrate and products respectively.
       The concentrations are in the order: [Biomass, Substrate, Products]"""

    dcdt = []
    
    for i in range(len(concentrations)):
        if concentrations[1] > 0: 
            dcdt.append(concentrations[0]*fluxes[i])
            
        else:
            dcdt.append(0)

    return dcdt


def one_stage_timecourse(initial_concentrations, time, fluxes):
    
    """This function employs odeint and returns timecourse data for one stage using dFBA
        initial_concs is a vector containing initial concentrations
        data[0] = Biomass Concentration
        data[1] = Substrate Concentration
        data[2-n] = Products Concentration
        time is a timepoint vector
        fluxes is a vector containing flux data for biomass, substrate and products respectively"""

    (data, full_output) = odeint(dfba_fun, initial_concentrations, time, args=tuple([fluxes]), full_output=True)
    data, time = crop_dfba_timecourse_data(data, time)
    return data.transpose(), time


def two_stage_timecourse(initial_concentrations, time_end, time_switch, two_stage_fluxes):

    """This function generates two_stage timecourse data using dfba given flux vectors for the two stages
       initial_concs is a vector containing initial concentrations
       time_end is the batch end time
       time_switch is the time at which the second stage becomes active
       Ensure t_switch < t_end
       two_stage_fluxes is a list of two lists that has flux data for biomass, substrate and product respectively"""
    
    num_of_points = 1000
    stage_one_fluxes, stage_two_fluxes = two_stage_fluxes
    stage_one_start_data = initial_concentrations
    
    # These two conditions are to ensure that the optimizer functions properly
    if time_switch > time_end:
        time_switch = time_end
    if time_switch < 0:
        time_switch = 0

    if int(num_of_points*(time_switch/time_end)) != 0:
        time_stage_one = np.linspace(0, time_switch, int(num_of_points*(time_switch/time_end)))
        data_stage_one, time_stage_one = one_stage_timecourse(stage_one_start_data, time_stage_one, stage_one_fluxes)
    else:
        data_stage_one, time_stage_one = one_stage_timecourse(stage_one_start_data, [0], stage_one_fluxes)

    stage_two_start_data = data_stage_one.transpose()[-1]
    if (stage_two_start_data[1] > 0) and (int(num_of_points*(time_end - time_switch)/time_end) != 0):
        time_stage_two = np.linspace(time_switch, time_end, int(num_of_points*(time_end - time_switch)/time_end))
        data_stage_two, t_stage_two = one_stage_timecourse(stage_two_start_data, time_stage_two, stage_two_fluxes)
    else:
        data_stage_two, t_stage_two = one_stage_timecourse(stage_two_start_data, [time_stage_one[-1]], stage_two_fluxes)
    
    two_stage_data = np.concatenate((data_stage_one, data_stage_two), axis=1)
    time = np.concatenate((time_stage_one, t_stage_two), axis=0)

    if two_stage_data[1][-1] > 0:
        warnings.warn("Substrate has not been depleted. Please increase your batch time.")
    return two_stage_data, time

