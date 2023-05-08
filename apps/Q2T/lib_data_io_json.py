"""
Library Features:

Name:          lib_data_io_json
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os
import json

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to read file settings
def read_file_settings(file_name):
    if os.path.exists(file_name):
        with open(file_name) as file_handle:
            file_data = json.load(file_handle)
    else:
        log_stream.error(' ===> Error in reading settings file "' + file_name + '"')
        raise IOError('File not found')
    return file_data
# -------------------------------------------------------------------------------------
