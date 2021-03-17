"""
Library Features:

Name:          lib_data_io_ascii
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os
import time
import json
import difflib

import numpy as np
import pandas as pd

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to select data warnings
def select_data_warnings(file_dframe, file_section_col, file_section_value, file_section_name, file_fields=None):

    section_dframe_raw = file_dframe.loc[file_dframe[file_section_col] == file_section_name, file_fields]

    section_dframe_unique = section_dframe_raw.drop_duplicates(keep='first')
    section_dframe_cols = section_dframe_unique.columns

    section_dict = {}
    if section_dframe_unique.shape[0] == 1:

        for section_dframe_col in section_dframe_cols:
            section_dframe_val = section_dframe_unique[section_dframe_col].values
            section_dict[section_dframe_col] = section_dframe_val
    else:

        section_dframe_unique = section_dframe_unique.reset_index()
        section_dframe_idx = section_dframe_unique[file_section_value].idxmax()

        if not np.isnan(section_dframe_idx):
            section_dframe_select = section_dframe_unique.iloc[section_dframe_idx]

            for section_dframe_col in section_dframe_cols:
                section_dframe_val = section_dframe_select[section_dframe_col]
                section_dict[section_dframe_col] = section_dframe_val
        else:
            section_dict = None

    return section_dict
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write warnings ascii file
def write_file_warnings(file_name, warnings_collections, warnings_structure,
                        tag_section_name='section_name',
                        no_time='NA', no_data=-9999.0, no_string='NA',
                        column_delimiter=','):

    field_type_list = ['float', 'time_stamp', 'float', 'string']

    warnings_header = None
    warnings_datasets = None
    for section_name, section_data in warnings_collections.items():

        field_list = []
        field_values = []

        field_list.append(tag_section_name)
        field_values.append(section_name)
        for key, data in section_data.items():

            for (field_key, field_value), field_type in zip(data.items(), field_type_list):
                field_list.append(field_key)

                if field_type == 'float':
                    if isinstance(field_value, (int, float)):
                        if not np.isnan(field_value):
                            field_value = str(float(field_value))
                        else:
                            field_value = str(no_data)
                    else:
                        field_value = str(no_data)
                elif field_type == 'time_stamp':
                    if isinstance(field_value, pd.Timestamp):
                        field_value = field_value.strftime('%Y-%m-%d %H:%M')
                    else:
                        field_value = no_time
                elif field_type == 'string':
                    if isinstance(field_value, str):
                        field_value = str(field_value)
                    else:
                        field_value = no_string
                else:
                    raise NotImplementedError('Parse warnings case not implemented yet')

                field_values.append(field_value)

        if warnings_header is None:
            warnings_header = column_delimiter.join(field_list)
        if warnings_datasets is None:
            warnings_datasets = []

        warnings_datasets.append(column_delimiter.join(field_values))

    with open(file_name, 'w') as file_handle:
        warnings_header = warnings_header + '\n'
        file_handle.write(warnings_header)
        for warnings_row in warnings_datasets:
            warnings_row = warnings_row + '\n'
            file_handle.write(warnings_row)

# -------------------------------------------------------------------------------------
