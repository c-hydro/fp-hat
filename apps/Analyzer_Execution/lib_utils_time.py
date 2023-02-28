"""
Library Features:

Name:          lib_utils_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import pandas as pd

from copy import deepcopy
from datetime import date

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set time run
def set_time(time_run_args=None, time_run_file=None, time_format='%Y-%m-%d %H:$M',
             time_period=1, time_frequency='H', time_rounding='H', time_reverse=True):

    log_stream.info(' ---> Set time run ... ')
    if time_run_args is not None:
        time_run = time_run_args
        log_stream.info(' ----> Time ' + time_run + ' set by argument')
    elif (time_run_args is None) and (time_run_file is not None):
        time_run = time_run_file
        log_stream.info(' ----> Time ' + time_run + ' set by user')
    elif (time_run_args is None) and (time_run_file is None):
        time_now = date.today()
        time_run = time_now.strftime(time_format)
        log_stream.info(' ----> Time ' + time_run + ' set by system')
    else:
        log_stream.info(' ---> Set time run ... FAILED')
        log_stream.error(' ===> Time is not correctly set')
        raise IOError('Time type or format is wrong')

    log_stream.info(' ---> Set time run ... DONE')

    time_exec = deepcopy(time_run)

    time_tmp = pd.Timestamp(time_run)
    time_run = time_tmp.floor(time_rounding)
    time_exec = pd.Timestamp(time_exec)

    if time_period > 0:
        time_range = pd.date_range(end=time_run, periods=time_period, freq=time_frequency)
    else:
        log_stream.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
        time_range = pd.DatetimeIndex([time_run], freq=time_frequency)

    if time_reverse:
        time_range = time_range[::-1]

    return time_run, time_exec, time_range

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to define time boundaries
def define_time_boundaries(time_reference, time_period=1, time_frequency='H',
                           time_index='first', time_direction='left'):

    if time_reference is None:
        log_stream.error(' ===> The "time_reference" defined by "NoneType" is not allowed')
        raise RuntimeError('The variable must be defined by TimeStamp object')
    if time_index is None:
        log_stream.warning(' ===> The "time_index" is defined by NoneType. Set the "first" default flag')
        time_index = 'first'
    if time_direction is None:
        log_stream.warning(' ===> The "time_direction" is defined by NoneType. Set the "left" default flag')
        time_direction = 'left'

    if (time_period is not None) and (time_frequency is not None):
        if time_period == 0:
            log_stream.warning(' ===> The "time_period" must be at least defined by 1 time step')
            time_period = 1

        if not time_frequency[0].isdigit():
            time_delta_str = str(1) + time_frequency
        else:
            time_delta_str = time_frequency

        if time_direction == 'left':
            time_range = pd.date_range(end=time_reference, periods=time_period, freq=time_frequency)
        elif time_direction == 'right':
            time_reference = time_reference + pd.Timedelta(time_delta_str)
            time_range = pd.date_range(start=time_reference, periods=time_period, freq=time_frequency)
        else:
            log_stream.error(' ===> The "time_direction" defined by "' + time_direction + '" is not supported')
            raise NotImplemented('Case not implemented yet')

        if time_index == 'first':
            time_select = time_range[0]
        elif time_index == 'last':
            time_select = time_range[-1]
        elif time_index == 'first_last':
            time_select = [time_range[0], time_range[::-1]]
        else:
            log_stream.error(' ===> The "time_index" defined by "' + time_index + '" is not supported')
            raise NotImplemented('Case not implemented yet')
    else:
        log_stream.warning(' ===> The "time_period" or the "time_frequency" is/are defined by NoneType. '
                           'The "time_select" variable will be defined by NoneType too')
        time_select = None

    return time_select

# -------------------------------------------------------------------------------------
