#!/usr/bin/python3
"""
Hydrological Analysis Tool - Q2T

__date__ = '20230508'
__version__ = '1.1.0'
__author__ =
        'Francesco Silvestro (francesco.silvestro@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',

__library__ = 'HAT'

General command line:
python3 HAT_Q2T.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20230508 (1.1.0) --> Refactor for HAT packagee
20221101 (1.0.0) --> Operational Release
"""

# -------------------------------------------------------------------------------------
# Complete library
import logging
import os
import time

from argparse import ArgumentParser

from lib_data_io_json import read_file_settings
from lib_utils_time import set_time
from lib_utils_system import make_folder

from driver_data_io_static import DriverStatic
from driver_data_io_dynamic import DriverDynamic

from lib_info_args import time_format_algorithm as time_format
from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_version = '1.1.0'
alg_release = '2023-05-08'
alg_name = 'Q2T'
# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_settings(alg_settings)

    # Set algorithm logging
    set_logging(logger_file=os.path.join(data_settings['log']['folder_name'],
                                         data_settings['log']['file_name']))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    log_stream.info(' ============================================================================ ')
    log_stream.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    log_stream.info(' ==> START ... ')
    log_stream.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize time information
    time_now, time_range, time_chunks = set_time(
        time_run_args=alg_time, time_run_file=data_settings['time']['time_now'],
        time_run_file_start=data_settings['time']['time_start'], time_run_file_end=data_settings['time']['time_end'],
        time_format=time_format,
        time_period=data_settings['time']['time_period'],
        time_frequency=data_settings['time']['time_frequency'],
        time_rounding=data_settings['time']['time_rounding'], time_reverse=False)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Driver and method of static datasets
    driver_data_static = DriverStatic(
        src_dict=data_settings['data']['static']['source'],
        dst_dict=data_settings['data']['static']['destination'],
        alg_info=data_settings['algorithm']['info'],
        alg_template=data_settings['algorithm']['template'],
        flag_cleaning_static=data_settings['algorithm']['flags']['cleaning_static']
    )
    static_data_collection = driver_data_static.organize_static()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time chunk(s)
    for time_step in time_range:

        # Driver and method of dynamic datasets
        driver_data_dynamic = DriverDynamic(
            time_reference=time_step,
            src_dict=data_settings['data']['dynamic']['source'],
            anc_dict=data_settings['data']['dynamic']['ancillary'],
            dst_dict=data_settings['data']['dynamic']['destination'],
            tmp_dict=data_settings['tmp'],
            alg_static=static_data_collection,
            alg_info=data_settings['algorithm']['info'],
            alg_template=data_settings['algorithm']['template'],
            flag_cleaning_dynamic_src=data_settings['algorithm']['flags']['cleaning_dynamic_source'],
            flag_cleaning_dynamic_anl=data_settings['algorithm']['flags']['cleaning_dynamic_analysis'],
            flag_cleaning_dynamic_dst=data_settings['algorithm']['flags']['cleaning_dynamic_destination'],

        )
        src_data_collection = driver_data_dynamic.organize_dynamic()
        anl_data_collection = driver_data_dynamic.analyze_dynamic(src_data_collection)
        driver_data_dynamic.save_dynamic(anl_data_collection)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    alg_time_elapsed = round(time.time() - start_time, 1)

    log_stream.info(' ')
    log_stream.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    log_stream.info(' ==> TIME ELAPSED: ' + str(alg_time_elapsed) + ' seconds')
    log_stream.info(' ==> ... END')
    log_stream.info(' ==> Bye, Bye')
    log_stream.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    alg_settings, alg_time = 'configuration.json', None
    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    if parser_values.alg_time:
        alg_time = parser_values.alg_time

    return alg_settings, alg_time

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set logging information
def set_logging(logger_file='log.txt', logger_format=None):
    if logger_format is None:
        logger_format = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

    logger_folder = os.path.split(logger_file)[0]
    make_folder(logger_folder)

    # Remove old logging file
    if os.path.exists(logger_file):
        os.remove(logger_file)

    # Set level of root debugger
    logging.root.setLevel(logging.DEBUG)

    # Open logging basic configuration
    logging.basicConfig(level=logging.DEBUG, format=logger_format, filename=logger_file, filemode='w')

    # Set logger handle
    logger_handle_1 = logging.FileHandler(logger_file, 'w')
    logger_handle_2 = logging.StreamHandler()
    # Set logger level
    logger_handle_1.setLevel(logging.DEBUG)
    logger_handle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    logger_formatter = logging.Formatter(logger_format)
    logger_handle_1.setFormatter(logger_formatter)
    logger_handle_2.setFormatter(logger_formatter)

    # Add handle to logging
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
