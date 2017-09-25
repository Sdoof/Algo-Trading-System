#!/usr/bin/python
# -*- coding: utf-8 -*-

# performance.py

from __future__ import print_function

import numpy as np
import pandas as pd

def create_sharpe_ratio(returns, periods=252):
    """

    :param returns: A pandas Series representing period percentage returns.
    :param periods: 252 for Daily, 252*6.5 for Hourly, 252*6.5*60 for Minutely.
    :return:
    """

    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)

def create_drawdowns(pnl):
    """

    :param pnl: A pandas Series representing period percentage returns.
    :return:
    """


    hwm = [0]   # high water mark

    idx = pnl.index
    drawdown = pd.Series(index = idx)
    duration = pd.Series(index = idx)

    for t in range(1, len(idx)):
        hwm.append(max(hwm[t-1], pnl[t]))
        drawdown[t] = (hwm[t] - pnl[t])
        duration[t] = (0 if drawdown[t] == 0 else duration[t-1]+1)

    return drawdown, drawdown.max(), duration.max()


