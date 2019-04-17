import cobra
from .settings import settings
import pandas as pd
from .substrate_dependent_envelopes import envelope_calculator
from .TwoStageFermentation import *


class TSDyssco(object):

    def __init__(self, **kwargs):
        self.model = None
        self.biomass_rxn = None
        self.substrate_rxn = None
        self.target_rxn = None
        self.condition = 'None'
        self.production_envelope = None
        self.model_complete_flag = False
        self.two_stage_fermentation_list = []
        for key in kwargs:

            if key in ['model', 'biomass_rxn', 'substrate_rxn', 'target_rxn', 'condition']:
                setattr(self, key, kwargs[key])

        self.calculate_production_envelope()

    def check_model_complete(self):
        self.model_complete_flag = False
        flag = True
        if type(self.model)!= cobra.core.model.Model:
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
            print("Your model is complete.")
            self.model_complete_flag = True

    def calculate_production_envelope(self):
        self.check_model_complete()
        if self.model_complete_flag:
            self.production_envelope = pd.DataFrame(envelope_calculator(self.model, self.biomass_rxn,
                                                                        self.substrate_rxn, self.target_rxn,
                                                                        settings.k_m, settings.num_points))

    def add_fermentation(self, two_stage_fermentation):
        self.two_stage_fermentation_list.append(two_stage_fermentation)

    def calculate_two_stage_characteristics(self):
        if self.production_envelope is None:
            self.calculate_production_envelope()
        envelope = self.production_envelope
        flux_list = [list(envelope[['growth_rates', 'substrate_uptake_rates', 'production_rates_ub']].iloc[i]) for i in
                    range(len(envelope))]
        for i in range(len(flux_list)):
            flux_list[i][1] = -flux_list[i][1]
        ts_ferm_list = [TwoStageFermentation(flux_list[stage_one_index], flux_list[stage_two_index])
                        for stage_one_index in range(len(flux_list))
                        for stage_two_index in range(len(flux_list))]
        for ts_ferm in ts_ferm_list:
            self.add_fermentation(ts_ferm)






