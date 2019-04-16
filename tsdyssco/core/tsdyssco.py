import cameo
import cobra
from ..settings import *
import pandas as pd
from .substrate_dependent_envelopes import envelope_calculator
from .optimizer import




class tsdyssco(object):

    def __init__(self, **kwargs):
        self.model = None
        self.biomass_rxn = None
        self.substrate_rxn = None
        self.target_rxn = None
        self.condition = 'None'
        self.production_envelope = pd.DataFrame()
        self.model_complete_flag = False
        for key in kwargs:

            if key in ['model', 'biomass_rxn', 'substrate_rxn', 'target_rxn', 'condition']:
                setattr(self, key, kwargs[key])

        self.check_model_complete()


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

        if flag == True:
            print("Your model is complete.")
            self.model_complete_flag = True


    def calculate_production_envelope(self):
        self.check_model_complete()
        if self.model_complete_flag:
            self.production_envelope = pd.DataFrame(envelope_calculator(self.model, self.biomass_rxn,
                                                                    self.substrate_rxn, self.target_rxn,
                                                                    k_m, num_points))



