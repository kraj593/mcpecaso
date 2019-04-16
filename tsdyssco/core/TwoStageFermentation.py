from .optimizer import optimal_switch_time
from .fermentation_metrics import *
from ..settings import *

objective_dict = {'productivity':batch_productivity,
                  'yield':batch_yield,
                  'titer':batch_end_titer,
                  'dupont':dupont_metric}

class TwoStageFermentation(object):
    def __init__(self,**kwargs):
        self.stage_one_fluxes = []
        self.stage_two_fluxes = []
        self.data = []
        self.time = []
        self.optimal_switch_time = None
        self.batch_yield = None
        self.batch_productivity = None
        self.batch_titer = None
        self.objective = objective