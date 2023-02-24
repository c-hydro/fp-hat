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
