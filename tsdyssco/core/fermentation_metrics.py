from .settings import settings


def batch_productivity(dfba_data, time):
    """ This function returns the productivity of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""
    if time[-1] > 0:
        return dfba_data[2, -1] / time[-1]
    else:
        return 0


def batch_yield(dfba_data, time):
    """ This function returns the yield of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""
    sub_used = dfba_data[1, 0] - dfba_data[1, -1]
    if sub_used > 0:
        return (dfba_data[2, -1] - dfba_data[2, 0]) / sub_used
    else:
        return 0


def batch_end_titer(dfba_data, time):
    """ This function returns the end titer of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""

    return dfba_data[2, -1]


def dupont_metric(dfba_data, time):
    """ This function returns the approximate dupont metric of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""
    yd = batch_yield(dfba_data, time)
    if yd > 0:
        return batch_productivity(dfba_data, time)*(1-1/yd)
    else:
        return 0


def linear_combination(dfba_data, time):
    """ This function returns a linear combination of the above defined metrics in case it is needed as an
        objective function. Input dfba_data should be in the order [biomass, substrate, product]"""

    return settings.productivity_coefficient*batch_productivity(dfba_data, time) + \
        settings.yield_coefficient*batch_yield(dfba_data, time) + \
        settings.titer_coefficient*batch_end_titer(dfba_data, time) + \
        settings.dupont_metric_coefficient*dupont_metric(dfba_data, time)
