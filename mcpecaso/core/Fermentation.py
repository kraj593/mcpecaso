from .optimizer import optimal_switch_time, optimal_switch_time_continuous
from .two_stage_dfba import two_stage_timecourse, one_stage_timecourse, two_stage_timecourse_continuous
from .fermentation_metrics import *
import numpy as np

objective_dict = {'batch_productivity': batch_productivity,
                  'batch_yield': batch_yield,
                  'batch_titer': batch_end_titer,
                  'linear_combination': linear_combination}


class TwoStageFermentation(object):
    def __init__(self, stage_one_fluxes, stage_two_fluxes, settings):
        self.settings = settings
        self.stage_one_fluxes = stage_one_fluxes
        self.stage_two_fluxes = stage_two_fluxes
        self.initial_concentrations = [self.settings.initial_biomass, self.settings.initial_substrate,
                                       self.settings.initial_product]
        self.time_end = self.settings.time_end
        self.data = []
        self.time = []
        self.productivity_constraint = settings.productivity_constraint
        self.yield_constraint = settings.yield_constraint
        self.titer_constraint = settings.titer_constraint
        self.optimal_switch_time = None
        self.batch_yield = None
        self.batch_productivity = None
        self.batch_titer = None
        self.linear_combination = None
        self.objective_value = None
        self.constraint_flag = True
        try:
            self.objective = objective_dict[self.settings.objective]
        except KeyError:
            self.objective = objective_dict['batch_productivity']

        self.calculate_fermentation_data()

    def calculate_fermentation_data(self):
        opt_result = optimal_switch_time(self.initial_concentrations, self.time_end,
                                         [self.stage_one_fluxes, self.stage_two_fluxes], self.settings,
                                         self.objective, self.productivity_constraint, self.yield_constraint,
                                         self.titer_constraint)
        if not opt_result.success:
            #print(opt_result.message)
            self.constraint_flag = False

        self.optimal_switch_time = opt_result.x[0]
        self.data, self.time = two_stage_timecourse(self.initial_concentrations, self.time_end,
                                                    self.optimal_switch_time,
                                                    [self.stage_one_fluxes, self.stage_two_fluxes],
                                                    num_of_points=self.settings.num_timepoints)
        self.time_end = self.time[-1]
        self.batch_productivity = batch_productivity(self.data, self.time, self.settings)
        self.batch_productivity = self.batch_productivity*(self.batch_productivity > 0)
        self.batch_yield = batch_yield(self.data, self.time, self.settings)
        self.batch_yield = self.batch_yield*(self.batch_yield > 0)
        self.batch_titer = batch_end_titer(self.data, self.time, self.settings)
        self.batch_titer = self.batch_titer*(self.batch_titer > 0)
        self.linear_combination = linear_combination(self.data, self.time, self.settings)
        try:
            self.objective_value = getattr(self, self.settings.objective)
        except AttributeError:
            self.objective_value = getattr(self, 'batch_productivity')


class FermentationExtrema(object):
    def __init__(self, model, max_growth, biomass_rxn, substrate_rxn, target_rxn, settings, extrema_type='ts_best'):
        self.settings = settings
        self.initial_concentrations = [self.settings.initial_biomass, self.settings.initial_substrate,
                                       self.settings.initial_product]
        self.time_end = self.settings.time_end
        self.data = []
        self.time = []
        self.productivity_constraint = settings.productivity_constraint
        self.yield_constraint = settings.yield_constraint
        self.titer_constraint = settings.titer_constraint
        self.model = model
        self.max_growth = max_growth
        self.biomass_rxn = biomass_rxn
        self.substrate_rxn = substrate_rxn
        self.target_rxn = target_rxn
        self.optimal_switch_time = None
        self.stage_one_factor = None
        self.stage_two_factor = None
        self.batch_yield = None
        self.batch_productivity = None
        self.batch_titer = None
        self.linear_combination = None
        self.objective_value = None
        self.constraint_flag = True
        self.extrema_type = extrema_type

        try:
            self.objective = objective_dict[self.settings.objective]
        except KeyError:
            self.objective = objective_dict['batch_productivity']

        self.calculate_fermentation_data()

    def calculate_fermentation_data(self):

        opt_result = optimal_switch_time_continuous(self.initial_concentrations, self.time_end, self.model,
                                                    self.max_growth, self.biomass_rxn, self.substrate_rxn,
                                                    self.target_rxn, self.settings, self.objective,
                                                    self.productivity_constraint, self.yield_constraint,
                                                    self.titer_constraint, self.extrema_type)
        if not opt_result.success:
            print(opt_result.message)
            self.constraint_flag = False

        self.optimal_switch_time = opt_result.x[0]
        self.stage_one_factor = opt_result.x[1]
        self.stage_two_factor = opt_result.x[2]
        self.data, self.time = two_stage_timecourse_continuous(self.initial_concentrations, self.time_end,
                                                               self.optimal_switch_time, self.stage_one_factor,
                                                               self.stage_two_factor, self.model, self.max_growth,
                                                               self.biomass_rxn, self.substrate_rxn, self.target_rxn,
                                                               self.settings)
        self.time_end = self.time[-1]
        self.batch_productivity = batch_productivity(self.data, self.time, self.settings)
        self.batch_productivity = self.batch_productivity*(self.batch_productivity > 0)
        self.batch_yield = batch_yield(self.data, self.time, self.settings)
        self.batch_yield = self.batch_yield*(self.batch_yield > 0)
        self.batch_titer = batch_end_titer(self.data, self.time, self.settings)
        self.batch_titer = self.batch_titer*(self.batch_titer > 0)
        self.linear_combination = linear_combination(self.data, self.time, self.settings)
        try:
            self.objective_value = getattr(self, self.settings.objective)
        except AttributeError:
            self.objective_value = getattr(self, 'batch_productivity')


class OneStageFermentation(object):

    def __init__(self, fluxes, settings):
        self.settings = settings
        self.fluxes = fluxes
        self.initial_concentrations = [self.settings.initial_biomass, self.settings.initial_substrate,
                                       self.settings.initial_product]
        self.time_end = self.settings.time_end
        self.data = []
        self.time = []
        self.batch_yield = None
        self.batch_productivity = None
        self.batch_titer = None
        self.linear_combination = None
        self.objective_value = None
        self.productivity_constraint = settings.productivity_constraint
        self.yield_constraint = settings.yield_constraint
        self.titer_constraint = settings.titer_constraint
        self.constraint_flag = True
        try:
            self.objective = objective_dict[self.settings.objective]
        except KeyError:
            self.objective = objective_dict['batch_productivity']

        self.calculate_fermentation_data()

    def calculate_fermentation_data(self):
        self.time = np.linspace(0, self.time_end, self.settings.num_timepoints)
        self.data, self.time = one_stage_timecourse(self.initial_concentrations, self.time, self.fluxes)
        self.time_end = self.time[-1]
        self.batch_productivity = batch_productivity(self.data, self.time, self.settings)
        self.batch_productivity = self.batch_productivity*(self.batch_productivity > 0)
        self.batch_yield = batch_yield(self.data, self.time, self.settings)
        self.batch_yield = self.batch_yield*(self.batch_yield > 0)
        self.batch_titer = batch_end_titer(self.data, self.time, self.settings)
        self.batch_titer = self.batch_titer*(self.batch_titer > 0)

        if not((self.batch_productivity >= self.productivity_constraint) and
               (self.batch_yield >= self.yield_constraint) and
               (self.batch_titer >= self.titer_constraint)):
            self.constraint_flag = False

        self.linear_combination = linear_combination(self.data, self.time, self.settings)
        try:
            self.objective_value = getattr(self, self.settings.objective)
        except AttributeError:
            self.objective_value = getattr(self, 'batch_productivity')
