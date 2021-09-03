"""
Library Features:

Name:          lib_utils_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210408'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import pandas as pd

from datetime import date

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set time run
def set_time(time_run_args=None, time_run_file=None, time_format='%Y-%m-%d %H:$M',
             time_run_file_start=None, time_run_file_end=None,
             time_period=1, time_frequency='H', time_rounding='H', time_reverse=True):

    log_stream.info(' ----> Set time period ... ')
    if (time_run_file_start is None) and (time_run_file_end is None):

        log_stream.info(' -----> Time info defined by "time_run" argument ... ')

        if time_run_args is not None:
            time_run = time_run_args
            log_stream.info(' ------> Time ' + time_run + ' set by argument')
        elif (time_run_args is None) and (time_run_file is not None):
            time_run = time_run_file
            log_stream.info(' ------> Time ' + time_run + ' set by user')
        elif (time_run_args is None) and (time_run_file is None):
            time_now = date.today()
            time_run = time_now.strftime(time_format)
            logging.info(' ------> Time ' + time_run + ' set by system')
        else:
            log_stream.info(' ----> Set time period ... FAILED')
            log_stream.error(' ===> Argument "time_run" is not correctly set')
            raise IOError('Time type or format is wrong')

        time_tmp = pd.Timestamp(time_run)
        time_run = time_tmp.floor(time_rounding)

        if time_period > 0:
            time_range = pd.date_range(end=time_run, periods=time_period, freq=time_frequency)
        else:
            log_stream.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
            time_range = pd.DatetimeIndex([time_now], freq=time_frequency)

        log_stream.info(' -----> Time info defined by "time_run" argument ... DONE')

    elif (time_run_file_start is not None) and (time_run_file_end is not None):

        log_stream.info(' -----> Time info defined by "time_start" and "time_end" arguments ... ')

        time_run_file_start = pd.Timestamp(time_run_file_start)
        time_run_file_start = time_run_file_start.floor(time_rounding)
        time_run_file_end = pd.Timestamp(time_run_file_end)
        time_run_file_end = time_run_file_end.floor(time_rounding)

        time_now = date.today()
        time_run = time_now.strftime(time_format)
        time_run = pd.Timestamp(time_run)
        time_run = time_run.floor(time_rounding)
        time_range = pd.date_range(start=time_run_file_start, end=time_run_file_end, freq=time_frequency)

        log_stream.info(' -----> Time info defined by "time_start" and "time_end" arguments ... DONE')

    else:
        log_stream.info(' ----> Set time period ... FAILED')
        log_stream.error(' ===> Arguments "time_start" and/or "time_end" is/are not correctly set')
        raise IOError('Time type or format is wrong')

    if time_reverse:
        time_range = time_range[::-1]

    time_chunks = set_chunks(time_range)

    log_stream.info(' ----> Set time period ... DONE')

    return time_run, time_range, time_chunks

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set chunks
def set_chunks(time_range, time_period='D'):

    time_groups = time_range.to_period(time_period)
    time_chunks = time_range.groupby(time_groups)

    return time_chunks
# -------------------------------------------------------------------------------------
