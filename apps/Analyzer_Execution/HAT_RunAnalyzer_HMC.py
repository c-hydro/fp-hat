#!/usr/bin/python3
"""
Hydrological Analysis Tool - Analyzer_Execution

__date__ = '20210225'
__version__ = '1.5.0'
__author__ =
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
        'Flavio Pignone (flavio.pignone@cimafoundation.org',

__library__ = 'HAT'

General command line:
python3 HAT_RunAnalyzer_HMC_Main.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20210225 (1.5.0) --> Beta release for HMC 3.x.x
20200605 (1.0.0) --> Beta release for HMC 2.x.x
"""

# -------------------------------------------------------------------------------------
# Complete library
import logging
import time
import os

from argparse import ArgumentParser

from lib_data_io_json import read_file_settings
from lib_utils_time import set_time
from lib_utils_system import make_folder

from driver_data_io_static import DriverStatic
from driver_data_io_dynamic import DriverDynamic
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_version = '1.5.0'
alg_release = '2021-02-25'
alg_name = 'RUN ANALYZER'
# Algorithm parameter(s)
time_format = '%Y-%m-%d %H:%M'
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
    set_logging(logger_file=os.path.join(data_settings['log']['folder_name'],
                                         data_settings['log']['file_name']))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize time information
    time_now, time_exec, time_range = set_time(
        time_run_args=alg_time, time_run_file=data_settings['time']['time_now'],
        time_format=time_format,
        time_period=data_settings['time']['time_period'],
        time_frequency=data_settings['time']['time_frequency'],
        time_rounding=data_settings['time']['time_rounding'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Driver and method of static datasets
    driver_data_static = DriverStatic(
        src_dict=data_settings['data']['static'],
        alg_ancillary=data_settings['algorithm']['ancillary'],
        alg_template_tags=data_settings['algorithm']['template']
    )
    static_data_collection = driver_data_static.organize_static()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time range
    for time_step in time_range:

        # -------------------------------------------------------------------------------------
        # Driver and method of dynamic datasets
        driver_data_dynamic = DriverDynamic(
            time_now=time_now,
            time_exec=time_exec,
            time_run=time_step,
            static_data_collection=static_data_collection,
            src_dict=data_settings['data']['dynamic']['source'],
            anc_dict=data_settings['data']['dynamic']['ancillary'],
            dest_dict=data_settings['data']['dynamic']['destination'],
            alg_ancillary=data_settings['algorithm']['ancillary'],
            alg_template_tags=data_settings['algorithm']['template'],
            flag_cleaning_dynamic_source=data_settings['algorithm']['flags']['cleaning_dynamic_source'],
            flag_cleaning_dynamic_analysis=data_settings['algorithm']['flags']['cleaning_dynamic_analysis'],
            flag_cleaning_dynamic_destination=data_settings['algorithm']['flags']['cleaning_dynamic_destination'],
            flag_cleaning_dynamic_tmp=data_settings['algorithm']['flags']['cleaning_dynamic_tmp'])

        dynamic_data_collection = driver_data_dynamic.organize_dynamic_data()
        analyze_data_collection, analyze_warnings_collection = driver_data_dynamic.analyze_dynamic_data(
            dynamic_data_collection)
        driver_data_dynamic.dump_dynamic_data(analyze_data_collection, analyze_warnings_collection)
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
    parser_handle = ArgumentParser()
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


# -------------------------------------------------------------------------------------
# Call script from external library
if __name__ == '__main__':
    main()
# -------------------------------------------------------------------------------------
