import pandas as pd


def cut_negative(h: pd.Series, head2: pd.Series, tail2: pd.Series):
    """Cut negative pulses.

    If baseline average is above height definition,
    set to None.
    """
    h.loc[head2.add(tail2).div(2).gt(h)] = None
    return h


def cut_high_intensity(laser: pd.Series, sumV: pd.Series, qcut=0.1):
    """Cut high intensity laser pulses.

    High intensity laser events have worse resolution.
    """
    laser.loc[sumV.gt(sumV.quantile(qcut))] = None
    return laser
