import cobra
import pandas as pd
from .substrate_dependent_envelopes import envelope_calculator
from .Fermentation import *
from joblib import Parallel, delayed
import multiprocessing
import time
import warnings
from .settings import settings

objective_dict = {'batch_productivity': 'productivity',
                  'batch_yield': 'yield',
                  'batch_titer': 'titer',
                  'dupont_metric': 'dupont metric',
                  'linear_combination': str(settings.productivity_coefficient) + ' * productivity + ' +
                                        str(settings.productivity_coefficient) + ' * yield + ' +
                                        str(settings.productivity_coefficient) + ' * titer + ' +
                                        str(settings.productivity_coefficient) + ' * dupont metric'}


class TSDyssco(object):

    def __init__(self, **kwargs):
        self.model = None
        self.biomass_rxn = None
        self.substrate_rxn = None
        self.target_rxn = None
        self.condition = 'None'
        self.production_envelope = None
        self.model_complete_flag = False
        self.k_m = None
        self.two_stage_fermentation_list = []
        self.one_stage_fermentation_list = []
        self.two_stage_best_batch = None
        self.one_stage_best_batch = None
        self.two_stage_characteristics = {'stage_one_growth_rate': [],
                                          'stage_two_growth_rate': [],
                                          'productivity': [],
                                          'yield': [],
                                          'titer': [],
                                          'dupont metric': [],
                                          'objective value': []}
        self.one_stage_characteristics = {'growth_rate': [],
                                          'productivity': [],
                                          'yield': [],
                                          'titer': [],
                                          'dupont metric': [],
                                          'objective value': []}
        try:
            self.objective_name = objective_dict[settings.objective]
        except KeyError:
            warnings.warn("Please check your objective. The objective provided in the settings class isn't valid.")
            self.objective_name = objective_dict['batch_productivity']
        for key in kwargs:

            if key in ['model', 'biomass_rxn', 'substrate_rxn', 'target_rxn', 'condition']:
                setattr(self, key, kwargs[key])

        self.calculate_production_envelope()

    def check_model_complete(self):
        self.model_complete_flag = False
        flag = True
        if type(self.model) != cobra.core.model.Model:
            print("Please check your model. It is not a standard COBRApy model.")
            flag = False

        if type(self.biomass_rxn) != cobra.core.reaction.Reaction or self.biomass_rxn.model != self.model:
            print("Please check your biomass reaction object. Ensure that it is a standard cobra Reaction object "
                  "and its parent is the model.")
            flag = False

        if type(self.substrate_rxn) != cobra.core.reaction.Reaction or self.substrate_rxn.model != self.model:
            print("Please check your substrate reaction object. Ensure that it is a standard cobra Reaction object "
                  "and its parent is the model.")
            flag = False

        if type(self.target_rxn) != cobra.core.reaction.Reaction or self.target_rxn.model != self.model:
            print("Please check your target reaction object. Ensure that it is a standard cobra Reaction object "
                  "and its parent is the model.")
            flag = False

        if flag:
            print("The model is complete.")
            self.model_complete_flag = True
        else:
            warnings.warn("The model is incomplete. Please check to ensure all the required fields are present.")

    def calculate_production_envelope(self):
        self.check_model_complete()
        if self.model_complete_flag:
            self.k_m = settings.k_m
            self.production_envelope = pd.DataFrame(envelope_calculator(self.model, self.biomass_rxn,
                                                                        self.substrate_rxn, self.target_rxn,
                                                                        settings.k_m, settings.num_points))
        else:
            warnings.warn("The production envelope could not be generated.")

    def add_two_stage_fermentation(self, two_stage_fermentation):
        self.two_stage_fermentation_list.append(two_stage_fermentation)
        self.two_stage_characteristics['stage_one_growth_rate'].append(two_stage_fermentation.stage_one_fluxes[0])
        self.two_stage_characteristics['stage_two_growth_rate'].append(two_stage_fermentation.stage_two_fluxes[0])
        self.two_stage_characteristics['productivity'].append(two_stage_fermentation.batch_productivity)
        self.two_stage_characteristics['yield'].append(two_stage_fermentation.batch_yield)
        self.two_stage_characteristics['titer'].append(two_stage_fermentation.batch_titer)
        self.two_stage_characteristics['dupont metric'].append(two_stage_fermentation.dupont_metric)
        self.two_stage_characteristics['objective value'].append(two_stage_fermentation.objective_value)
        if self.two_stage_best_batch is not None:
            if two_stage_fermentation.objective_value > self.two_stage_best_batch.objective_value:
                self.two_stage_best_batch = two_stage_fermentation
        else:
            self.two_stage_best_batch = two_stage_fermentation

    def add_one_stage_fermentation(self, one_stage_fermentation):
        self.one_stage_fermentation_list.append(one_stage_fermentation)
        self.one_stage_characteristics['growth_rate'].append(one_stage_fermentation.fluxes[0])
        self.one_stage_characteristics['productivity'].append(one_stage_fermentation.batch_productivity)
        self.one_stage_characteristics['yield'].append(one_stage_fermentation.batch_yield)
        self.one_stage_characteristics['titer'].append(one_stage_fermentation.batch_titer)
        self.one_stage_characteristics['dupont metric'].append(one_stage_fermentation.dupont_metric)
        self.one_stage_characteristics['objective value'].append(one_stage_fermentation.objective_value)
        if self.one_stage_best_batch is not None:
            if one_stage_fermentation.objective_value > self.one_stage_best_batch.objective_value:
                self.one_stage_best_batch = one_stage_fermentation
        else:
            self.one_stage_best_batch = one_stage_fermentation

    def calculate_fermentation_characteristics(self):
        if self.production_envelope is None:
            self.calculate_production_envelope()
        if self.production_envelope is not None:
            envelope = self.production_envelope
            flux_list = [list(envelope[['growth_rates', 'substrate_uptake_rates', 'production_rates_ub']].iloc[i])
                         for i in range(len(envelope))]
            for i in range(len(flux_list)):
                flux_list[i][1] = -flux_list[i][1]
            if settings.parallel:
                print('Starting parallel pool')
                num_cores = multiprocessing.cpu_count()
                start_time = time.time()
                os_ferm_list = Parallel(n_jobs=num_cores, verbose=5)(
                    delayed(OneStageFermentation)(flux_list[index], settings)
                    for index in range(len(flux_list)))
                ts_ferm_list = Parallel(n_jobs=num_cores, verbose=5)(
                    delayed(TwoStageFermentation)(flux_list[stage_one_index], flux_list[stage_two_index], settings)
                    for stage_one_index in range(len(flux_list))
                    for stage_two_index in range(len(flux_list)))
                end_time = time.time()
            else:
                start_time = time.time()
                os_ferm_list = [OneStageFermentation(flux_list[index], settings)
                                for index in range(len(flux_list))]
                ts_ferm_list = [TwoStageFermentation(flux_list[stage_one_index], flux_list[stage_two_index], settings)
                                for stage_one_index in range(len(flux_list))
                                for stage_two_index in range(len(flux_list))]
                end_time = time.time()
            time.sleep(0.5)
            print("Completed analysis in ", str(end_time-start_time), "s")
            for ts_ferm in ts_ferm_list:
                self.add_two_stage_fermentation(ts_ferm)
            for os_ferm in os_ferm_list:
                self.add_one_stage_fermentation(os_ferm)

        else:
            warnings.warn("A production envelope could not be generated for the given model. This is likely due to "
                          "missing fields in the model.")

