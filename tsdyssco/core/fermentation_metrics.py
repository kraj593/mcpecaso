def batch_productivity(dfba_data, time):
    """ This function returns the productivity of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""

    return dfba_data[2, -1] / time[-1]


def batch_yield(dfba_data, time):
    """ This function returns the yield of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""

    return (dfba_data[2, -1] - dfba_data[2, 0]) / (dfba_data[1, 0] - dfba_data[1, -1])


def batch_end_titer(dfba_data, time):
    """ This function returns the end titer of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""

    return dfba_data[2, -1]


def dupont_metric(dfba_data, time):
    """ This function returns the approximate dupont metric of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""

    return batch_productivity(dfba_data, time)*(1-1/batch_yield(dfba_data, time))

