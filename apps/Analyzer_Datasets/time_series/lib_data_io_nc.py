"""
Library Features:

Name:          lib_data_io_nc
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os

from copy import deepcopy

import numpy as np
import xarray as xr
import pandas as pd
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to set netcdf time-series file
def set_time_collections(var_data_collections,
                         var_header='header', var_attrs='attributes',
                         tag_time_series='times',
                         tag_time_delta_obs='time_observed_delta', tag_time_delta_for='time_forecast_delta'):

    time_stamp_start_collections = []
    time_stamp_end_collections = []
    time_delta_obs_collections = []
    time_delta_for_collections = []
    for var_key, var_obj in var_data_collections.items():
        if var_obj is not None:
            time_array = var_obj[var_header][tag_time_series]
            time_delta_obs = var_obj[var_attrs][tag_time_delta_obs]
            time_delta_for = var_obj[var_attrs][tag_time_delta_for]

            time_idx = pd.DatetimeIndex(time_array)
            time_stamp_start_step = time_idx[0]
            time_stamp_end_step = time_idx[-1]

            time_stamp_start_collections.append(time_stamp_start_step)
            time_stamp_end_collections.append(time_stamp_end_step)

            time_delta_obs_collections.append(time_delta_obs)
            time_delta_for_collections.append(time_delta_for)
        else:
            logging.warning(' ===> Time obj is not defined for time-series ' + var_key)

    time_delta_int = list(set(time_delta_obs_collections + time_delta_for_collections))[0]
    time_delta_obj = pd.Timedelta(time_delta_int, unit='seconds')

    time_stamp_start = pd.DatetimeIndex(time_stamp_start_collections).min()
    time_stamp_end = pd.DatetimeIndex(time_stamp_end_collections).max()

    time_range = pd.date_range(start=time_stamp_start, end=time_stamp_end, freq=time_delta_obj.resolution_string)

    return time_range
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to filter netcdf time-series file
def filter_file_collections(var_data_collections, var_structure, var_points, var_delimiter=':',
                            var_observed='observed_data'):

    var_data_filter = {}
    for var_datasets_key, var_datasets_collections in var_structure.items():

        for var_field_key, var_field_name in var_datasets_collections.items():

            var_field_part = var_field_name.split(var_delimiter)
            var_field_root = var_delimiter.join([var_field_part[0], var_field_part[1]])

            for var_key, var_data in var_data_collections.items():
                var_data_part = var_key.split(var_delimiter)
                var_data_root = var_delimiter.join([var_data_part[0], var_data_part[1]])

                var_data_point = var_delimiter.join(var_data_part[2:])

                if var_data_root == var_field_root:

                    if var_datasets_key == var_observed:
                        if var_data.ndim == 2:
                            var_data_filtered = var_data[0, :].reshape([1, var_data.shape[1]])
                        elif var_data.ndim == 1:
                            var_data_filtered = var_data.reshape([1, var_data.shape[0]])
                        else:
                            logging.error(' ===> Variable datasets format is not allowed')
                            raise IOError('Array format must be 1D or 2D')
                    else:
                        if var_data.ndim == 1:
                            var_data_filtered = deepcopy(var_data.reshape([1, var_data.shape[0]]))
                        else:
                            var_data_filtered = deepcopy(var_data)

                    if var_data_point not in list(var_data_filter.keys()):
                        var_data_filter[var_data_point] = {}
                    if var_delimiter.join([var_datasets_key, var_field_key]) not in list(var_data_filter[var_data_point].keys()):
                        var_data_filter[var_data_point][var_delimiter.join([var_datasets_key, var_field_key])] = {}

                    var_data_filter[var_data_point][var_delimiter.join(
                        [var_datasets_key, var_field_key])] = var_data_filtered

    return var_data_filter

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read netcdf time-series file
def read_file_collections(file_name_list, variable_name_common=None, attr_name_common=None):

    if variable_name_common is None:
        variable_name_common = ['times', 'File_Type', 'Exec_Type']
    if attr_name_common is None:
        attr_name_common = ['run_var', 'run_mode']

    file_header_collections = {}
    file_data_collections = {}
    file_attrs_collections = {}
    for file_name_step in file_name_list:

        if os.path.exists(file_name_step):
            file_dset = xr.open_dataset(file_name_step)
            attrs_dset = file_dset.attrs
        else:
            logging.warning(' ===> File ' + file_name_step + ' not found!')

        # Iterate over file attributes
        for attr_key, attr_value in attrs_dset.items():

            if attr_key not in list(file_attrs_collections.keys()):
                file_attrs_collections[attr_key] = attr_value
            elif (attr_key in list(file_attrs_collections.keys())) and (attr_key in attr_name_common):
                tmp_value = file_attrs_collections[attr_key]
                if not isinstance(tmp_value, list):
                    tmp_value = [tmp_value, attr_value]
                elif isinstance(tmp_value, list):
                    tmp_value.append(attr_value)
                file_attrs_collections[attr_key] = tmp_value

        # Iterate over file variable(s)
        variable_name_list = list(file_dset.data_vars)
        for variable_name_step in variable_name_list:

            variable_data_step = file_dset[variable_name_step].values

            if variable_name_step in variable_name_common:
                if variable_name_step not in list(file_header_collections.keys()):
                    file_header_collections[variable_name_step] = variable_data_step

            if (variable_name_step not in list(file_data_collections.keys())) and \
                    (variable_name_step not in variable_name_common):
                file_data_collections[variable_name_step] = variable_data_step
            elif (variable_name_step in list(file_data_collections.keys())) and \
                    (variable_name_step not in variable_name_common):
                variable_data_tmp = deepcopy(file_data_collections[variable_name_step])
                variable_data_stack = np.vstack((variable_data_tmp, variable_data_step))
                file_data_collections[variable_name_step] = variable_data_stack

    return file_header_collections, file_data_collections, file_attrs_collections
# -------------------------------------------------------------------------------------
