from .optimizer import optimal_switch_time
from .two_stage_dfba import two_stage_timecourse, one_stage_timecourse
from .fermentation_metrics import *
from .settings import settings

objective_dict = {'batch_productivity': batch_productivity,
                  'batch_yield': batch_yield,
                  'batch_titer': batch_end_titer,
                  'dupont_metric': dupont_metric,
                  'linear_combination': linear_combination}


class TwoStageFermentation(object):
    def __init__(self, stage_one_fluxes, stage_two_fluxes):
        self.stage_one_fluxes = stage_one_fluxes
        self.stage_two_fluxes = stage_two_fluxes
        self.initial_concentrations = [settings.initial_biomass, settings.initial_substrate, settings.initial_product]
        self.time_end = settings.time_end
        self.data = []
        self.time = []
        self.optimal_switch_time = None
        self.batch_yield = None
        self.batch_productivity = None
        self.batch_titer = None
        self.dupont_metric = None
        self.linear_combination = None
        self.objective_value = None
        try:
            self.objective = objective_dict[settings.objective]
        except KeyError:
            print("Invalid objective. Please check your tsdyssco objective in the settings file.")
            self.objective = objective_dict['batch_productivity']

        self.calculate_fermentation_data()

    def calculate_fermentation_data(self):
        opt_result = optimal_switch_time(self.initial_concentrations, self.time_end,
                                         [self.stage_one_fluxes, self.stage_two_fluxes],
                                         self.objective)
        self.optimal_switch_time = opt_result.x
        self.data, self.time = two_stage_timecourse(self.initial_concentrations, self.time_end,
                                                    self.optimal_switch_time,
                                                    [self.stage_one_fluxes, self.stage_two_fluxes])
        self.time_end = self.time[-1]
        self.batch_productivity = batch_productivity(self.data, self.time)
        self.batch_yield = batch_yield(self.data, self.time)
        self.batch_titer = batch_end_titer(self.data, self.time)
        self.dupont_metric = dupont_metric(self.data, self.time)
        self.linear_combination = linear_combination(self.data, self.time)
        self.objective_value = getattr(self, settings.objective)


class OneStageFermentation(object):

    def __init__(self, fluxes):
        self.fluxes = fluxes
        self.initial_concentrations = [settings.initial_biomass, settings.initial_substrate, settings.initial_product]
        self.time_end = settings.time_end
        self.data = []
        self.time = []
        self.batch_yield = None
        self.batch_productivity = None
        self.batch_titer = None
        self.dupont_metric = None
        self.linear_combination = None
        self.objective_value = None
        try:
            self.objective = objective_dict[settings.objective]
        except KeyError:
            print("Invalid objective. Please check your tsdyssco objective in the settings file.")
            self.objective = objective_dict['batch_productivity']

        self.calculate_fermentation_data()

    def calculate_fermentation_data(self):
        self.data, self.time = one_stage_timecourse(self.initial_concentrations, self.time_end, self.fluxes)
        self.time_end = self.time[-1]
        self.batch_productivity = batch_productivity(self.data, self.time)
        self.batch_yield = batch_yield(self.data, self.time)
        self.batch_titer = batch_end_titer(self.data, self.time)
        self.dupont_metric = dupont_metric(self.data, self.time)
        self.linear_combination = linear_combination(self.data, self.time)
        self.objective_value = getattr(self, settings.objective)
