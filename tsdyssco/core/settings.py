class Settings:
    def __init__(self):
        self.uptake_fun = 'logistic'
        self.uptake_params = {'B':5}
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
        self.num_timepoints = 1000
        self.productivity_constraint = 0
        self.yield_constraint = 0
        self.titer_constraint = 0
        self.scope = 'global'


settings = Settings()
