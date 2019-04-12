def batch_productivity(dfba_data, time_end):
    """ This function returns the productivity of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""

    return dfba_data[2, -1] / time_end


def batch_yield(dfba_data, time_end):
    """ This function returns the yield of a batch.
        Input dfba_data should be in the order [biomass, substrate, product]"""

    return (dfba_data[2, -1] - dfba_data[2, 0]) / (dfba_data[1, 0] - dfba_data[1, -1])