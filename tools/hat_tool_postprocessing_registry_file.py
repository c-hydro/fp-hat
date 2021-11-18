#!/usr/bin/python3

"""
HAT POSTPROCESSING TOOL - Registry file manager

__date__ = '20211118'
__version__ = '1.0.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'HAT'

General command line:
python3 hmc_tool_postprocessing_registry_file.py -settings_file configuration.json -time "YYYY-mm-dd HH:MM"
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import argparse
import os
import csv
import json

logger = logging.getLogger(__name__)
logger_format = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logger.setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.INFO,
    format=logger_format,
    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()]
)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to join file registry
def main(file_format='csv'):

    logging.info(' ---> Method to join registry file ...')

    file_configuration, file_time = get_args()

    if os.path.exists(file_configuration):
        data_configuration = read_file_settings(file_configuration)
        file_registry_in, file_registry_out, file_flag_out = parse_file_settings(data_configuration)
    else:
        logging.error(' ===> FileName: ' + file_configuration + ' does not exist')
        raise IOError('File not found')

    if isinstance(file_registry_in, str):
        file_registry_in = [file_registry_in]
    elif isinstance(file_registry_in, list):
        pass
    else:
        logging.error(' ===> Datatype of file_registry_in is defined by unsupported format')
        raise NotImplementedError('Case not implemented yet')

    data_registry_ws = []
    for file_registry_id, file_registry_tmp in enumerate(file_registry_in):
        if file_registry_tmp.endswith(file_format):
            if os.path.exists(file_registry_tmp):
                data_registry_tmp = read_file_registry(file_registry_tmp)
                data_registry_ws.extend(data_registry_tmp)
            else:
                logging.warning(' ===> FileName ' + file_registry_tmp + ' does not exist.')

        else:
            logging.error(' ===> FileType must be in ' + file_format + ' format')
            raise NotImplementedError('Case not implemented yet')

    if data_registry_ws:

        data_registry_unique = list(set(data_registry_ws))
        data_registry_sorted = sorted(data_registry_unique)

        if file_flag_out:
            if os.path.exists(file_registry_out):
                os.remove(file_registry_out)

        if not os.path.exists(file_registry_out):

            folder_name_out, file_name_out = os.path.split(file_registry_out)
            make_folder(folder_name_out)
            write_file_registry(file_registry_out, data_registry_sorted)

            logging.info(' ---> Method to join registry file ... DONE')
        else:
            logging.info(' ---> Method to join registry file ... SKIPPED. File was previously saved.')

    else:
        logging.warning(' ===> All registry datasets are null. Impossible to join datasets.')
        logging.info(' ---> Method to join registry file ... FAILED.')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write file registry
def write_file_registry(file_name, file_data, file_newline='\n', file_sep=' ', file_quoting=csv.QUOTE_NONE):
    with open(file_name, "w", newline=file_newline) as file_handle:
        file_writer = csv.writer(file_handle, quoting=file_quoting, delimiter=file_sep)
        for row_data in file_data:
            file_writer.writerow([row_data])
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write file registry
def read_file_registry(file_name, file_sep=' '):
    with open(file_name, 'r') as file_handle:
        file_reader = csv.reader(file_handle, delimiter=file_sep)
        file_data = []
        for row_data in file_reader:
            file_data.append(row_data[0])
    return file_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to parse file settings
def parse_file_settings(data_settings, tag_flags='flags', tag_datasets='datasets',
                         subtag_flag_destination='update_file_destination',
                         subtag_folder_name='folder_name', subtag_file_name='file_name'):
    ws_flags = data_settings[tag_flags]
    ws_datasets = data_settings[tag_datasets]

    datasets_source = ws_datasets['source']
    datasets_destination = ws_datasets['destination']

    file_path_source = []
    for data_key, data_fields in datasets_source.items():
        folder_name_tmp = data_fields[subtag_folder_name]
        file_name_tmp = data_fields[subtag_file_name]
        file_path_tmp = os.path.join(folder_name_tmp, file_name_tmp)
        file_path_source.append(file_path_tmp
                                     )
    folder_name_destination = datasets_destination[subtag_folder_name]
    file_name_destination = datasets_destination[subtag_file_name]
    file_path_destination = os.path.join(folder_name_destination, file_name_destination)

    file_flag_destination = ws_flags[subtag_flag_destination]

    return file_path_source, file_path_destination, file_flag_destination
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read file settings
def read_file_settings(file_name):
    with open(file_name) as file_handle:
        file_data = json.load(file_handle)
    return file_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def make_folder(path_folder):
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
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
# Call script from external library
if __name__ == "__main__":
    main()
# -------------------------------------------------------------------------------------
