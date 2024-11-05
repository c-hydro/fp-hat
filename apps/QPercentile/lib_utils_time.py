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
# method to define period based on left and right bounds
def set_time_bounds(time_run, time_period, time_rounding='H', time_frequency='H'):
    log_stream.info(' ----> Set time bounds ... ')

    time_run = pd.Timestamp(time_run)
    time_run = time_run.floor(time_rounding)

    time_start, time_end = None, None
    if isinstance(time_period, (int, float)):
        pass
    elif isinstance(time_period, dict):

        # get time period bounds
        time_period_left = time_period['left']
        time_period_right = time_period['right']

        # set time start
        time_start = pd.date_range(end=time_run, periods=time_period_left, freq=time_frequency)[0]

        # set time end
        time_tmp = pd.date_range(start=time_run, periods=2, freq=time_frequency)[-1]
        time_end = pd.date_range(start=time_tmp, periods=time_period_right, freq=time_frequency)[-1]

    else:
        log_stream.error(' ===> Argument "time_period" format is not expected')
        raise NotImplemented('Case not implemented yet')

    log_stream.info(' ----> Set time bounds ... DONE')

    return time_start, time_end


# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set time run
def set_time_info(time_run_args=None, time_run_file=None, time_format='%Y-%m-%d %H:$M',
                  time_run_file_start=None, time_run_file_end=None,
                  time_period=1, time_frequency='H', time_rounding='H', time_reverse=True):

    # info time run start
    log_stream.info(' ----> Set time run ... ')

    # set time run (user or file settings)
    if time_run_args is not None:
        time_run = time_run_args
        log_stream.info(' -----> Time ' + time_run + ' set by argument')
    elif (time_run_args is None) and (time_run_file is not None):
        time_run = time_run_file
        log_stream.info(' -----> Time ' + time_run + ' set by user')
    elif (time_run_args is None) and (time_run_file is None):
        time_now = date.today()
        time_run = time_now.strftime(time_format)
        logging.info(' -----> Time ' + time_run + ' set by system')
    else:
        log_stream.info(' ----> Set time run ... FAILED')
        log_stream.error(' ===> Argument "time_run" is not correctly set')
        raise IOError('Time type or format is wrong')

    # info time run end
    log_stream.info(' ----> Set time run ... DONE')

    # set time bounds
    time_run_file_start, time_run_file_end = set_time_bounds(time_run, time_period, time_rounding, time_frequency)

    log_stream.info(' ----> Set time period ... ')
    if (time_run_file_start is None) and (time_run_file_end is None):

        log_stream.info(' -----> Time info defined by "time_run" argument ... ')

        time_tmp = pd.Timestamp(time_run)
        time_run = time_tmp.floor(time_rounding)

        if time_period > 0:
            time_range = pd.date_range(end=time_run, periods=time_period, freq=time_frequency)
        else:
            log_stream.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
            time_range = pd.DatetimeIndex([time_run], freq=time_frequency)

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

    log_stream.info(' ----> Set time period ... DONE')

    return time_run, time_range

# -------------------------------------------------------------------------------------
