"""
Library Features:

Name:          lib_data_io_csv
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import csv

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


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
