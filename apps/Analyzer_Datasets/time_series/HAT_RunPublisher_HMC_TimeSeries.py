"""
HAT - Analyzer HMC time-series

__date__ = '20210728'
__version__ = '1.5.1'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hat'

General command line:
python HAT_RunPublisher_HMC_TimeSeries.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20210728 (1.5.1) --> Operational release
20210429 (1.5.0) --> Beta release
20210113 (1.0.0) --> Last stable version of library in the old development
"""
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Library
import logging
import os
import argparse
import time

from lib_utils_logging import set_logging_file
from lib_utils_time import set_time
from lib_data_io_json import read_file_settings
from lib_info_args import logger_name, time_format_algorithm

from driver_data_io_static import DriverStatic
from driver_data_io_registry import DriverRegistry
from driver_data_io_dynamic import DriverDynamic

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
project_name = 'HAT'
alg_name = 'Analyzer Datasets'
alg_type = 'HMC TimeSeries'
alg_version = '1.5.1'
alg_release = '2021-07-28'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_settings(alg_settings)

    # Set algorithm logging
    set_logging_file(
        logger_name=logger_name,
        logger_file=os.path.join(data_settings['log']['folder_name'], data_settings['log']['file_name']))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    log_stream.info(' ============================================================================ ')
    log_stream.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version +
                    ' - Release ' + alg_release + ')]')
    log_stream.info(' ==> START ... ')
    log_stream.info(' ')

    # Time algorithm information
    alg_time_start = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize time run
    time_run, time_range, time_chunks = set_time(
        time_run_args=alg_time,
        time_run_file=data_settings['time']['time_run'],
        time_run_file_start=data_settings['time']['time_start'],
        time_run_file_end=data_settings['time']['time_end'],
        time_format=time_format_algorithm,
        time_period=data_settings['time']['time_period'],
        time_frequency=data_settings['time']['time_frequency'],
        time_rounding=data_settings['time']['time_rounding']
    )
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Driver and methods of static datasets
    driver_data_static = DriverStatic(
        src_dict=data_settings['data']['static']['source'],
        dst_dict=data_settings['data']['static']['destination'],
        alg_template_tags=data_settings['algorithm']['template'],
        flag_cleaning_static=data_settings['algorithm']['flags']['cleaning_static']
    )
    static_data_collection = driver_data_static.organize_static()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time chunk(s)
    for time_step in time_range:

        # -------------------------------------------------------------------------------------
        # Driver and methods of dynamic datasets
        driver_data_registry = DriverRegistry(
            time_step,
            static_data_collection=static_data_collection,
            src_dict=data_settings['data']['dynamic']['source'],
            dst_dict=data_settings['data']['dynamic']['destination'],
            alg_template=data_settings['algorithm']['template'],
            flag_cleaning_registry=data_settings['algorithm']['flags']['cleaning_dynamic_registry']
        )
        registry_data_collection = driver_data_registry.organize_registry()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Driver and methods of dynamic datasets
        driver_data_dynamic = DriverDynamic(
            time_step,
            static_data_collection=static_data_collection,
            registry_data_collection=registry_data_collection,
            src_dict=data_settings['data']['dynamic']['source'],
            anc_dict=data_settings['data']['dynamic']['ancillary'],
            anl_dict=data_settings['data']['dynamic']['analysis'],
            dst_dict=data_settings['data']['dynamic']['destination'],
            alg_info=data_settings['algorithm']['info'],
            alg_template=data_settings['algorithm']['template'],
            flag_cleaning_dynamic_src=data_settings['algorithm']['flags']['cleaning_dynamic_source'],
            flag_cleaning_dynamic_anl=data_settings['algorithm']['flags']['cleaning_dynamic_analysis'],
            flag_cleaning_dynamic_dst=data_settings['algorithm']['flags']['cleaning_dynamic_destination'],
            flag_cleaning_dynamic_tmp=data_settings['algorithm']['flags']['cleaning_dynamic_tmp'])

        dynamic_data_collections = driver_data_dynamic.organize_dynamic_data()
        dynamic_analysis_collections = driver_data_dynamic.analyze_dynamic_data(dynamic_data_collections)
        driver_data_dynamic.dump_dynamic_data(dynamic_analysis_collections)
        driver_data_dynamic.clean_dynamic_tmp()
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    alg_time_elapsed = round(time.time() - alg_time_start, 1)

    logging.info(' ')
    logging.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version +
                 ' - Release ' + alg_release + ')]')
    logging.info(' ==> TIME ELAPSED: ' + str(alg_time_elapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = argparse.ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_settings, alg_time

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set logging information
def set_logging(logger_file='log.txt', logger_format=None):
    if logger_format is None:
        logger_format = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

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


# -------------------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# -------------------------------------------------------------------------------------
