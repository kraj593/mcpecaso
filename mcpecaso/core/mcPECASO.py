import cobra
import pandas as pd
from .substrate_dependent_envelopes import envelope_calculator
from .Fermentation import *
from joblib import Parallel, delayed
import multiprocessing
import time
import warnings
from .settings import settings
from copy import deepcopy


class mcPECASO(object):

    def __init__(self, **kwargs):
        self.model = None
        self.biomass_rxn = None
        self.substrate_rxn = None
        self.target_rxn = None
        self.condition = 'None'
        self.production_envelope = None
        self.model_complete_flag = False
        self.two_stage_fermentation_list = []
        self.one_stage_fermentation_list = []
        self.two_stage_suboptimal_batch = None
        self.two_stage_best_batch = None
        self.one_stage_best_batch = None
        self.settings = deepcopy(settings)
        self.one_stage_constraint_flag = True
        self.two_stage_constraint_flag = True
        self.objective_name = ''
        self.two_stage_characteristics = {'stage_one_growth_rate': [],
                                          'stage_two_growth_rate': [],
                                          'productivity': [],
                                          'yield': [],
                                          'titer': [],
                                          'objective value': []}
        self.one_stage_characteristics = {'growth_rate': [],
                                          'productivity': [],
                                          'yield': [],
                                          'titer': [],
                                          'objective value': []}
        self.continuous_flag = False

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
            self.production_envelope = pd.DataFrame(envelope_calculator(self.model, self.biomass_rxn,
                                                                        self.substrate_rxn, self.target_rxn,
                                                                        self.settings))
        else:
            warnings.warn("The production envelope could not be generated.")

    def add_two_stage_fermentation(self, two_stage_fermentation):
        self.two_stage_fermentation_list.append(two_stage_fermentation)
        if self.settings.scope == 'global':
            self.two_stage_characteristics['stage_one_growth_rate'].append(two_stage_fermentation.stage_one_fluxes[0])
            self.two_stage_characteristics['stage_two_growth_rate'].append(two_stage_fermentation.stage_two_fluxes[0])

        elif self.settings.scope == 'extrema':
            self.two_stage_characteristics['stage_one_growth_rate'].append(two_stage_fermentation.stage_one_factor *
                                                                           max(self.production_envelope.growth_rates))
            self.two_stage_characteristics['stage_two_growth_rate'].append(two_stage_fermentation.stage_two_factor *
                                                                           max(self.production_envelope.growth_rates))

        else:
            raise Exception('Unknown Scope')

        self.two_stage_characteristics['productivity'].append(two_stage_fermentation.batch_productivity)
        self.two_stage_characteristics['yield'].append(two_stage_fermentation.batch_yield)
        self.two_stage_characteristics['titer'].append(two_stage_fermentation.batch_titer)
        self.two_stage_characteristics['objective value'].append(two_stage_fermentation.objective_value)

        if not two_stage_fermentation.constraint_flag:
            self.two_stage_constraint_flag = False
            warnings.warn("The constraints set for the fermentation metrics could not be met for one or more one stage "
                          "fermentation batches. These batches were not considered while determining the best batch. "
                          "Consider reducing or removing the constraints to resolve this issue.")
        else:
            if self.settings.scope == 'global':
                if (two_stage_fermentation.stage_one_fluxes[0] == max(self.production_envelope['growth_rates']) and
                   two_stage_fermentation.stage_two_fluxes[0] == min(self.production_envelope['growth_rates'])):
                    self.two_stage_suboptimal_batch = two_stage_fermentation
                if self.two_stage_best_batch is not None:
                    if two_stage_fermentation.objective_value > self.two_stage_best_batch.objective_value:
                        if two_stage_fermentation.stage_one_fluxes != two_stage_fermentation.stage_two_fluxes:
                            self.two_stage_best_batch = two_stage_fermentation
                else:
                    if two_stage_fermentation.stage_one_fluxes != two_stage_fermentation.stage_two_fluxes:
                        self.two_stage_best_batch = two_stage_fermentation
            elif self.settings.scope =='extrema':
                if two_stage_fermentation.extrema_type == 'ts_sub':
                    self.two_stage_suboptimal_batch = two_stage_fermentation
                if two_stage_fermentation.extrema_type == 'ts_best':
                    self.two_stage_best_batch = two_stage_fermentation
            else:
                raise Exception('Unknown Scope')

    def add_one_stage_fermentation(self, one_stage_fermentation):
        self.one_stage_fermentation_list.append(one_stage_fermentation)
        if self.settings.scope == 'global':
            self.one_stage_characteristics['growth_rate'].append(one_stage_fermentation.fluxes[0])
        elif self.settings.scope == 'extrema':
            self.one_stage_characteristics['growth_rate'].append(one_stage_fermentation.stage_one_factor *
                                                                 max(self.production_envelope.growth_rates))
        self.one_stage_characteristics['productivity'].append(one_stage_fermentation.batch_productivity)
        self.one_stage_characteristics['yield'].append(one_stage_fermentation.batch_yield)
        self.one_stage_characteristics['titer'].append(one_stage_fermentation.batch_titer)
        self.one_stage_characteristics['objective value'].append(one_stage_fermentation.objective_value)
        if not one_stage_fermentation.constraint_flag:
            self.one_stage_constraint_flag = False
            warnings.warn("The constraints set for the fermentation metrics could not be met for one or more one stage "
                          "fermentation batches. These batches were not considered while determining the best batch. "
                          "Consider reducing or removing the constraints to resolve this issue.")
        else:
            if self.one_stage_best_batch is not None:
                if one_stage_fermentation.objective_value > self.one_stage_best_batch.objective_value:
                    self.one_stage_best_batch = one_stage_fermentation
            else:
                self.one_stage_best_batch = one_stage_fermentation

    def calculate_fermentation_characteristics(self):
        if self.production_envelope is None:
            self.calculate_production_envelope()

        objective_name = ''
        if self.settings.productivity_coefficient:
            objective_name += str(self.settings.productivity_coefficient) + ' * productivity + '
        if self.settings.yield_coefficient:
            objective_name += str(self.settings.yield_coefficient) + ' * yield + '
        if self.settings.titer_coefficient:
            objective_name += str(self.settings.titer_coefficient) + ' * titer + '
        objective_name = objective_name.rstrip(" + ")
        objective_dict = {'batch_productivity': 'productivity',
                          'batch_yield': 'yield',
                          'batch_titer': 'titer',
                          'linear_combination': objective_name}
        try:
            self.objective_name = objective_dict[self.settings.objective]
        except KeyError:
            warnings.warn("Please check your objective. The objective provided in the settings class isn't valid.")
            self.objective_name = objective_dict['batch_productivity']

        if self.production_envelope is not None:
            self.two_stage_fermentation_list = []
            self.one_stage_fermentation_list = []
            self.two_stage_suboptimal_batch = None
            self.two_stage_best_batch = None
            self.one_stage_best_batch = None
            envelope = self.production_envelope
            flux_list = [list(envelope[['growth_rates', 'substrate_uptake_rates', 'production_rates_ub']].iloc[i])
                         for i in range(len(envelope))]
            for i in range(len(flux_list)):
                flux_list[i][1] = -flux_list[i][1]
            if self.settings.scope == 'global':
                if self.settings.parallel:
                    print('Starting parallel pool')
                    num_cores = multiprocessing.cpu_count()
                    start_time = time.time()
                    os_ferm_list = Parallel(n_jobs=num_cores, verbose=5)(
                        delayed(OneStageFermentation)(flux_list[index], self.settings)
                        for index in range(len(flux_list)))
                    ts_ferm_list = Parallel(n_jobs=num_cores, verbose=5)(
                        delayed(TwoStageFermentation)(flux_list[stage_one_index], flux_list[stage_two_index], self.settings)
                        for stage_one_index in range(len(flux_list))
                        for stage_two_index in range(len(flux_list)))
                    end_time = time.time()
                else:
                    start_time = time.time()
                    os_ferm_list = [OneStageFermentation(flux_list[index], self.settings)
                                    for index in range(len(flux_list))]
                    ts_ferm_list = [TwoStageFermentation(flux_list[stage_one_index], flux_list[stage_two_index], self.settings)
                                    for stage_one_index in range(len(flux_list))
                                    for stage_two_index in range(len(flux_list))]
                    end_time = time.time()
            elif self.settings.scope == 'extrema':
                start_time = time.time()
                max_growth = max(self.production_envelope.growth_rates)
                ts_ferm_list = []
                os_ferm_list = []
                ts_ferm_list.append(FermentationExtrema(self.model, max_growth, self.biomass_rxn, self.substrate_rxn,
                                                        self.target_rxn, self.settings, 'ts_best'))
                ts_ferm_list.append(FermentationExtrema(self.model, max_growth, self.biomass_rxn, self.substrate_rxn,
                                                        self.target_rxn, self.settings, 'ts_sub'))
                os_ferm_list.append(FermentationExtrema(self.model, max_growth, self.biomass_rxn, self.substrate_rxn,
                                                        self.target_rxn, self.settings, 'os_best'))
                end_time = time.time()
            else:
                raise Exception('Unknown Scope')

            time.sleep(0.5)
            print("Completed analysis in ", str(end_time-start_time), "s")
            for ts_ferm in ts_ferm_list:
                self.add_two_stage_fermentation(ts_ferm)
            for os_ferm in os_ferm_list:
                self.add_one_stage_fermentation(os_ferm)

        else:
            warnings.warn("A production envelope could not be generated for the given model. This is likely due to "
                          "missing fields in the model.")

