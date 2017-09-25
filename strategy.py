#!/usr/bin/python
# -*- coding: utf-8 -*-

# strategy.py

from __future__ import print_function

from abc import ABCMeta, abstractmethod
import datetime

try:
    import Queue as queue
except ImportError:
    import queue

import numpy as np
import pandas as pd

from event import SignalEvent

class Strategy(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self):
        raise NotImplementedError("calculate_signals() not implemented")
    