#!/usr/bin/python
# -*- coding: utf-8 -*-

# data.py

from __future__ import print_function

from abc import ABCMeta, abstractmethod
import datetime
import os, os.path

import numpy as np
import pandas as pd

from event import MarketEvent

import pandas.io.sql as psql
import pymysql as mdb

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

class DataHandler(object):
    """
    Abstract base class providing an interface for subsequent data handlers.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        """
        Returns the last (most recent) bar on the internal data store
        of OHLC bars for the specified traded symbol.
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Returns datetime object for latest bar.
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        Can return either Open, High, Low, Close, Volume or Open
        Interest for the last bar.
        """
        raise NotImplementedError("Should implement get_latest_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Can return either Open, High, Low, Close, Volume or Open
        Interest for the last N bars.
        """
        raise NotImplementedError("Should implement get_latest_bar_values()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes latest bar(s) to the internal data store for each traded symbol,
        in a tuple format: (datetime, open, high, low, close, volume, open interest).
        """
        raise NotImplementedError("Should implement update_bars()")


class SecuritiesDBDataHandler(DataHandler):
    """
    SecuritiesDBDataHandler queries the Securities Database for historical data
    for each requested symbol, then stores the historical data in a dictionary of
    pandas DataFrames. The historical data is then fed to an internal data store
    on a 'drip-feed' basis to simulate the retrieval of new market data on each
    new trading day.
    """

    def __init__(self, events, symbol_list):
        """
        Parameters:
        events - Event Queue
        symbol_list - A list of symbol strings.
        """
        self.events = events
        self.symbol_list = symbol_list

        # Dictionary of pandas DataFrames storing historical data
        self.symbol_data = {}
        # Internal data store
        self.internal_store = {}
        self.continue_backtest = True

        self._query_securities_db()

        self.generator_dict = {s: self._get_new_bar(s) for s in symbol_list}


    def _query_securities_db(self):
        db_host = 'localhost'
        db_user = 'daniel'
        db_pass = 'pass'
        db_name = 'securities_master'
        con = mdb.connect(db_host, db_user, db_pass, db_name)

        sql = """SELECT dp.price_date, dp.open_price, dp.high_price, dp.low_price, 
                 dp.close_price, dp.volume, dp.adj_close_price AS adj_close
                 FROM daily_price AS dp INNER JOIN symbol AS sym
                  ON dp.symbol_id = sym.id
                 WHERE sym.ticker = '%s'
                 ORDER BY dp.price_date ASC;"""

        comb_index = None

        for s in self.symbol_list:
            self.symbol_data[s] = psql.read_sql_query(sql % s, con=con, index_col='price_date')
            #print(self.symbol_data[s].tail())
            #if comb_index is None:
             #   comb_index = self.symbol_list[s].index
            #else:
             #   comb_index.union(self.symbol_data[s].index)

            self.internal_store[s] = []

        #for s in self.symbol_list:
         #   self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()


    def _get_new_bar(self, symbol):
        """
        Returns generator object to iterate through historical data
        """
        for b in self.symbol_data[symbol].itertuples():
            yield b

    def get_latest_bar(self, symbol):
        try:
            bars_list = self.internal_store[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        try:
            bars_list = self.internal_store[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        try:
            bars_list = self.internal_store[symbol]
        except KeyError:
            print("That symbol is not available in the securities database.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        try:
            bars_list = self.internal_store[symbol]
        except KeyError:
            print("That symbol is not available in the securities database.")
            raise
        else:
            return getattr(bars_list[-1], val_type)

    def get_latest_bars_values(self, symbol, val_type, N=1):
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print("That symbol is not available in the securities database.")
            raise
        else:
            return np.array([getattr(b, val_type) for b in bars_list])

    def update_bars(self):
        for s in self.symbol_list:
            try:
                bar = self.generator_dict[s].next()
                print(bar)
                print(getattr(bar,'adj_close'))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.internal_store[s].append(bar)
        self.events.put(MarketEvent())
