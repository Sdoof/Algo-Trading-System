#!/usr/bin/python
# -*- coding: utf-8 -*-

# mac.py

from __future__ import print_function

import datetime

import numpy as np
import pandas as pd
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import SecuritiesDBDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio

class MovingAverageCrossStrategy(Strategy):

    def __init__(self, bars, events, short_window=100, long_window=400):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought

    def calculate_signals(self, event):

        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(s, "adj_close", N=self.long_window)
                bar_date = self.bars.get_latest_bar_datetime(s)
                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])

                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ""

                    if short_sma > long_sma and self.bought[s] == "OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = 'LONG'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == "LONG":
                        print("SHORT: %s" % bar_date)
                        sig_dir = 'EXIT'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'


if __name__ == "__main__":
    symbol_list = ['AAPL']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(1990,1,1,0,0,0)
    backtest = Backtest(symbol_list, initial_capital, heartbeat,
                        start_date, SecuritiesDBDataHandler, SimulatedExecutionHandler,
                        Portfolio, MovingAverageCrossStrategy
    )
    backtest.simulate_trading()

