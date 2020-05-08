import numpy as np
from scipy.integrate import odeint
import warnings
from .substrate_dependent_envelopes import *


def crop_dfba_timecourse_data(dfba_data, t):
    
    """This function takes in dFBA data and timepoints and crops them to the point where substrate
    is over. dFBA data should be in the format: [[biomass,substrate,product]...] and timepoints are
    a list of timepoints."""
    np.warnings.filterwarnings('ignore')
    if any(dfba_data[:, 1] < 0):
        substrate_consumed_index = np.where(dfba_data[:, 1] < 0)[0][0]
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


def two_stage_timecourse(initial_concentrations, time_end, time_switch, two_stage_fluxes, num_of_points=1000):

    """This function generates two_stage timecourse data using dfba given flux vectors for the two stages
       initial_concs is a vector containing initial concentrations
       time_end is the batch end time
       time_switch is the time at which the second stage becomes active
       Ensure t_switch < t_end
       two_stage_fluxes is a list of two lists that has flux data for biomass, substrate and product respectively"""
    stage_one_fluxes, stage_two_fluxes = two_stage_fluxes
    stage_one_start_data = initial_concentrations

    if time_end <= 0:
        two_stage_data, time = one_stage_timecourse(stage_one_start_data, [0], stage_one_fluxes)
        return two_stage_data, time

    # These two conditions are to ensure that the optimizer functions properly
    if time_switch > time_end:
        time_switch = time_end
    if (time_switch < 0) or np.isnan(time_switch):
        time_switch = 0

    if np.floor(num_of_points*(time_switch/time_end)) != 0:
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


def two_stage_timecourse_continuous(initial_concentrations, time_end, time_switch, stage_one_factor, stage_two_factor,
                                    model, max_growth, biomass_rxn, substrate_rxn, target_rxn, settings):
    """This function generates two_stage timecourse data using dfba given phenotype for the two stages
       initial_concs is a vector containing initial concentrations
       time_end is the batch end time
       time_switch is the time at which the second stage becomes active
       Ensure t_switch < t_end
       two_stage_fluxes is a list of two lists that has flux data for biomass, substrate and product respectively"""
    stage_one_start_data = initial_concentrations
    uptake_dict = {'linear': linear_uptake, 'logistic': logistic_uptake}

    if settings.uptake_fun in uptake_dict.keys():
        uptake_fun = uptake_dict[settings.uptake_fun]
    else:
        raise KeyError('Unknown substrate uptake function specified. Only ', [fun for fun in uptake_dict.keys()],
                       'are acceptable uptake functions.')

    with model:
        stage_one_biomass_flux = stage_one_factor/100*max_growth
        stage_one_substrate_flux = -np.around(uptake_fun(stage_one_biomass_flux, **settings.uptake_params)+0.0000005,
                                              decimals=6)
        biomass_rxn.bounds = (stage_one_biomass_flux, stage_one_biomass_flux)
        substrate_rxn.bounds = (stage_one_substrate_flux, 1000)
        model.objective = target_rxn
        stage_one_product_flux = model.optimize().objective_value
        stage_one_fluxes = [stage_one_biomass_flux, stage_one_substrate_flux, stage_one_product_flux]

        stage_two_biomass_flux = stage_two_factor/100*max_growth
        stage_two_substrate_flux = -np.around(uptake_fun(stage_two_biomass_flux, **settings.uptake_params)+0.0000005,
                                              decimals=6)
        biomass_rxn.bounds = (stage_two_biomass_flux, stage_two_biomass_flux)
        substrate_rxn.bounds = (stage_two_substrate_flux, 1000)
        model.objective = target_rxn
        stage_two_product_flux = model.optimize().objective_value
        stage_two_fluxes = [stage_two_biomass_flux, stage_two_substrate_flux, stage_two_product_flux]
    if time_end <= 0:
        two_stage_data, time = one_stage_timecourse(stage_one_start_data, [0], stage_one_fluxes)
        return two_stage_data, time

    # These two conditions are to ensure that the optimizer functions properly
    if time_switch > time_end:
        time_switch = time_end
    if (time_switch < 0) or np.isnan(time_switch):
        time_switch = 0

    if np.floor(settings.num_timepoints * (time_switch / time_end)) != 0:
        time_stage_one = np.linspace(0, time_switch, int(settings.num_timepoints * (time_switch / time_end)))
        data_stage_one, time_stage_one = one_stage_timecourse(stage_one_start_data, time_stage_one, stage_one_fluxes)
    else:
        data_stage_one, time_stage_one = one_stage_timecourse(stage_one_start_data, [0], stage_one_fluxes)

    stage_two_start_data = data_stage_one.transpose()[-1]
    if (stage_two_start_data[1] > 0) and (int(settings.num_timepoints * (time_end - time_switch) / time_end) != 0):
        time_stage_two = np.linspace(time_switch, time_end, int(settings.num_timepoints * (time_end - time_switch) / time_end))
        data_stage_two, t_stage_two = one_stage_timecourse(stage_two_start_data, time_stage_two, stage_two_fluxes)
    else:
        data_stage_two, t_stage_two = one_stage_timecourse(stage_two_start_data, [time_stage_one[-1]], stage_two_fluxes)

    two_stage_data = np.concatenate((data_stage_one, data_stage_two), axis=1)
    time = np.concatenate((time_stage_one, t_stage_two), axis=0)

    if two_stage_data[1][-1] > 0:
        warnings.warn("Substrate has not been depleted. Please increase your batch time.")

    return two_stage_data, time
