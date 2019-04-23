class Settings:
    def __init__(self):
        self.k_m = 0
        self.substrate_uptake = 'generalized_logistic'
        self.parallel = False
        self.num_points = 25
        self.objective = 'batch_productivity'
        self.initial_biomass = 0.05
        self.initial_substrate = 50
        self.initial_product = 0
        self.time_end = 100
        self.productivity_coefficient = 0
        self.yield_coefficient = 0
        self.titer_coefficient = 0
        self.dupont_metric_coefficient = 0
        self.num_timepoints = 1000


settings = Settings()
