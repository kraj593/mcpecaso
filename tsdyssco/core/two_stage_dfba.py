import cameo
import numpy as np
import pandas as pd
from scipy.integrate import odeint


def crop_dfba_timecourse_data(dFBA_data, t):
    
    """This function takes in dFBA data and timepoints and crops them to the point where substrate
    is over. dFBA data should be in the format: [[biomass,substrate,product]...] and timepoints are
    a list of timepoints."""
    
    if any(dFBA_data[:, 1] <= 0):
        substrate_consumed_index= np.where(dFBA_data[:, 1] <= 0)[0][0]
    else:
        substrate_consumed_index = len(t) - 1
    return dFBA_data[:substrate_consumed_index + 1], t[:substrate_consumed_index + 1]


def dfba_fun(concentrations, time, fluxes):

    """This function returns the time derivatives for biomass, substrate and products respectively.
       The concentrations are in the order: [Biomass, Substrate, Products]"""

    dcdt=[]
    
    for i in range(len(concentrations)):
        if concentrations[1] > 0: 
            dcdt.append(concentrations[0]*fluxes[i])
            
        else:
            dcdt.append(0)

    return dcdt


def one_stage_timecourse(initial_concs, time, fluxes):
    
    """This function employs odeint and returns timecourse data for one stage using dFBA
        initial_concs is a vector containing initial concentrations
        data[0] = Biomass Concentration
        data[1] = Substrate Concentration
        data[2-n] = Products Concentration
        time is a timepoint vector
        fluxes is a vector containing flux data for biomass, substrate and products respectively"""

    (data, full_output) = odeint(dfba_fun, initial_concs, time, args=tuple([fluxes]), full_output=1)
    data, time = crop_dfba_timecourse_data(data, time)
    return data.transpose(), time


def two_stage_timecourse(initial_concs, time_end, time_switch, two_stage_fluxes):

    """This function generates two_stage dFBA data
       y0 is a vector containing initial concentrations
       t_end is the batch end time
       t_switch is the time at which the second stage becomes active
       Ensure t_switch < t_end
       two_stage_fluxes is a list of two lists that has flux data for biomass, substrate and product respectively"""
    
    num_of_points = 1000
    stage_one_fluxes, stage_two_fluxes = two_stage_fluxes
    data_stage_one = []
    data_stage_two = []
    stage_one_start_data = initial_concs
    
    #These two conditions are to ensure that the optimizer functions properly
    if time_switch > time_end:
        time_end = time_switch
    if time_switch < 0:
        time_switch = 0
        
    
    if int(num_of_points*(t_switch/t_end)) != 0:
        t_stage_one = np.linspace(0,t_switch,int(num_of_points*(t_switch/t_end)))
        data_stage_one, t_stage_one = generate_timecourse_data(stage_one_start_data, t_stage_one, stage_one_fluxes)
    else:
        data_stage_one, t_stage_one = generate_timecourse_data(stage_one_start_data, [0], stage_one_fluxes)
    
    
    stage_two_start_data = data_stage_one.transpose()[-1]
    if (stage_two_start_data[1] > 0) and (int(num_of_points*(t_end - t_switch)/t_end) != 0):
        t_stage_two = np.linspace(t_switch, t_end, int(num_of_points*(t_end - t_switch)/t_end))
        data_stage_two, t_stage_two = generate_timecourse_data(stage_two_start_data, t_stage_two, stage_two_fluxes)
    else:
        data_stage_two, t_stage_two = generate_timecourse_data(stage_two_start_data, [t_stage_one[-1]], stage_two_fluxes)
    
    data = np.concatenate((data_stage_one, data_stage_two), axis = 1)
    t = np.concatenate((t_stage_one, t_stage_two), axis = 0)

    return data, t

