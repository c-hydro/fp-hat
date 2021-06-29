"""
Library Features:

Name:          lib_graph_ts_ancillary
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210508'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import json
import pickle
import os

import numpy as np
import pandas as pd

from lib_info_args import time_format_datasets
from lib_utils_system import make_folder

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to write file time-series datasets
def write_file_datasets_ts(file_name, file_datasets):

    folder_string, file_string = os.path.split(file_name)
    make_folder(folder_string)

    with open(file_name, 'wb') as file_handle:
        pickle.dump(file_datasets, file_handle, protocol=pickle.HIGHEST_PROTOCOL)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write file time-series info
def write_file_info_ts(file_name, file_info, file_indent=4, field_sep=','):

    file_dict2json = {}
    for file_key, file_fields in file_info.items():
        file_dict2json[file_key] = {}
        for field_key, field_values in file_fields.items():

            file_dict2json[file_key][field_key] = {}
            if isinstance(field_values, str):
                file_dict2json[file_key][field_key] = field_values
            elif isinstance(field_values, (int, float, np.int64)):
                file_dict2json[file_key][field_key] = str(field_values)
            elif isinstance(field_values, pd.DatetimeIndex):
                field_values_list = [field_value.strftime(time_format_datasets) for field_value in field_values]
                field_values_string = field_sep.join(field_values_list)
                file_dict2json[file_key][field_key] = field_values_string
            else:
                log_stream.warning(' ===> Dump "' + file_key + '" is skipped due to the unsupported format of the key.')
                file_dict2json[file_key][field_key] = None

    folder_string, file_string = os.path.split(file_name)
    make_folder(folder_string)

    file_data = json.dumps(file_dict2json, indent=file_indent, ensure_ascii=False, sort_keys=True)
    with open(file_name, "w", encoding='utf-8') as file_handle:
        file_handle.write(file_data)

# -------------------------------------------------------------------------------------
