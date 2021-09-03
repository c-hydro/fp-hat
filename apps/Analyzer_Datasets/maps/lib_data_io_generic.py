"""
Library Features:

Name:          lib_data_io_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os
import re
import tempfile

import xarray as xr
import pandas as pd
import numpy as np

from lib_utils_system import get_dict_values, fill_tags2string, make_folder
from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to create a temporary filename
def create_filename_tmp(prefix='tmp_', suffix='.tiff', folder=None):

    if folder is None:
        folder = '/tmp'

    with tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, suffix=suffix, delete=False) as tmp:
        temp_file_name = tmp.name
    return temp_file_name
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to organize file template
def organize_file_template(file_collections, file_dataset_tag='maps_forcing_obs_ws'):
    file_name_list = []
    file_time_list = []
    for file_time_step, file_dataset_step in file_collections.items():
        if file_dataset_tag in list(file_dataset_step.keys()):
            file_name_step = file_dataset_step[file_dataset_tag]
            file_name_list.append(file_name_step)
            file_time_list.append(file_time_step)
    return file_name_list, file_time_list
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to fill file path
def fill_file_template(file_obj, template_default=None, template_filled=None):

    if (template_filled is not None) and (template_default is not None):
        if isinstance(file_obj, dict):
            file_filled_obj = {}
            for file_path_key, file_path_raw in file_obj.items():
                file_path_def = fill_tags2string(file_path_raw, template_default, template_filled)
                file_filled_obj[file_path_key] = file_path_def
        elif isinstance(file_obj, str):
            file_filled_obj = fill_tags2string(file_obj, template_default, template_filled)
        else:
            raise NotImplementedError('Object in filling string is not allowed')
    else:
        file_filled_obj = file_path_collections

    return file_filled_obj
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define file template
def define_file_template(time_run, time_analysis=None,
                         section_name=None, basin_name=None, domain_name=None, run_name=None,
                         template_default=None):

    if isinstance(time_run, str):
        time_run = pd.Timestamp(time_run)

    if time_analysis is None:
        time_analysis = time_run

    if isinstance(time_analysis, str):
        time_analysis = pd.Timestamp(time_analysis)

    template_filled = {}
    if template_default is not None:
        for template_key in list(template_default.keys()):
            if template_key == 'section_name':
                template_filled[template_key] = section_name
            elif template_key == 'basin_name':
                template_filled[template_key] = basin_name
            elif template_key == 'domain_name':
                template_filled[template_key] = domain_name
            elif template_key == 'run_datetime':
                template_filled[template_key] = time_run
            elif template_key == 'run_sub_path':
                template_filled[template_key] = time_run
            elif template_key == 'time_series_datetime':
                template_filled[template_key] = time_run
            elif template_key == 'time_series_sub_path':
                template_filled[template_key] = time_run
            elif template_key == 'maps_forcing_obs_ws_datetime':
                template_filled[template_key] = time_analysis
            elif template_key == 'maps_forcing_obs_ws_sub_path':
                template_filled[template_key] = time_run
            elif template_key == 'maps_outcome_datetime':
                template_filled[template_key] = time_analysis
            elif template_key == 'maps_outcome_sub_path':
                template_filled[template_key] = time_run
            elif template_key == 'plot_datetime':
                template_filled[template_key] = time_analysis
            elif template_key == 'plot_sub_path':
                template_filled[template_key] = time_analysis
            elif template_key == 'var_name':
                template_filled[template_key] = '{var_name}'
            elif template_key == 'group_name':
                template_filled[template_key] = '{group_name}'
            elif template_key == 'time_name':
                template_filled[template_key] = '{time_name}'
            elif template_key == 'run_name':
                template_filled[template_key] = run_name
            else:
                raise NameError('Template key ' + template_key + ' is not assigned by the procedure')
    else:
        template_filled = None

    return template_filled
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to parser time from path list
def get_folders_time(folder_list, time_format_in='%Y%m%d_%H', time_format_out='%Y-%m-%d %H:00'):

    if isinstance(folder_list, str):
        folder_list = [folder_list]

    time_list = []
    for folder_step in folder_list:
        time_stamp_step = pd.to_datetime(folder_step, format=time_format_in)
        time_str_step = time_stamp_step.strftime(format=time_format_out)
        time_list.append(time_str_step)
    return time_list
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to list all subfolders in a root path
def get_path_folders(root_path):
    folder_list = os.listdir(root_path)
    return folder_list
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to search root of a generic path
def get_path_root(generic_path):

    string_patterns = re.findall(r"\{([A-Za-z0-9_]+)\}", generic_path)

    dict_patterns = {}
    for string_pattern in string_patterns:
        dict_patterns[string_pattern] = ':::'

    tmp_path = generic_path.format(**dict_patterns)
    root_path = tmp_path.split(sep=':::')[0]

    return root_path
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get user path
def get_user_root():
    user_path = os.path.expanduser("~")
    return user_path
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define file path
def define_file_path(settings_data, tag_folder_name='folder_name', tag_file_name='file_name'):

    user_path = get_user_root()

    file_path_collections = {}
    for data_key, data_fields in settings_data.items():

        folder_name = get_dict_values(data_fields, tag_folder_name, [])

        if "$HOME" in folder_name:
            folder_name = folder_name.replace('$HOME', user_path)
        if "$ENV_HOME" in folder_name:
            folder_name = folder_name.replace('$ENV_HOME', user_path)

        file_name = get_dict_values(data_fields, tag_file_name, [])
        file_path = os.path.join(folder_name, file_name)

        file_path_collections[data_key] = file_path

    return file_path_collections
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define file name filling with variable name
def define_file_var(file_name_collections, file_time, var_name, dataset_name, var_tag='var_name'):

    if file_time in list(file_name_collections.keys()):

        file_name = file_name_collections[file_time][dataset_name]

        file_name_tmp = file_name.replace(var_tag, ':')
        file_path_var = file_name_tmp.format(var_name)
        folder_name_var, file_name_var = os.path.split(file_path_var)
        make_folder(folder_name_var)
    else:
        raise IOError('Plot filename is not defined for time ' + file_time)

    return file_path_var

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to validate time step
def validate_time_step(time_step, time_range):
    time_step = pd.Timestamp(time_step)
    if time_step in time_range:
        time_valid = True
    else:
        time_valid = False
    return time_valid
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data time range
def create_time_range(time_run, time_obs_period=1, time_obs_freq='H', time_for_period=0, time_for_freq='H',
                      time_format='%Y-%m-%d %H:00', time_reverse=True):

    time_run = pd.Timestamp(time_run)
    time_obs_end = time_run
    time_for_start = time_run + pd.Timedelta(1, unit=time_for_freq)

    time_obs_range = pd.date_range(end=time_obs_end, periods=time_obs_period, freq=time_obs_freq)
    time_for_range = pd.date_range(start=time_for_start, periods=time_for_period, freq=time_for_freq)

    time_range_stamp = time_obs_range.union(time_for_range)

    if time_reverse:
        time_range_stamp = time_range_stamp[::-1]

    time_range_str = []
    for time_step in time_range_stamp:
        time_str = time_step.strftime(format=time_format)
        time_range_str.append(time_str)

    return time_range_stamp, time_range_str

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data array variable
def create_darray_maps(dset_collections, var_time=None,
                       var_name_in='Air_Temperature', var_name_out='Air_T'):

    if var_time is not None:
        if var_time in list(dset_collections.keys()):

            dset_generic = dset_collections[var_time]
            dset_vars = list(dset_generic.data_vars)

            if var_name_in in dset_vars:

                dset_tmp = dset_generic.rename({var_name_in: var_name_out})
                var_darray_def = dset_tmp[var_name_out]
                var_attrs_def = var_darray_def.attrs

                return var_darray_def, var_attrs_def
            else:
                raise IOError('Dataset variable does not exist')
        else:
            raise IOError('Dataset time does not exist')
    else:
        raise IOError('Dataset time is undefined')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create time-series dataframe variable
def create_dframe_ts(df_generic,
                     var_name_in='discharge_obs', var_name_out='discharge_obs',
                     var_value_min=0, var_value_max=None,
                     index_name='time'):

    df_columns = list(df_generic.columns)

    var_dict = {}
    if var_name_in in df_columns:

        var_data = df_generic[var_name_in].values

        if var_value_min is not None:
            var_data[var_data < var_value_min] = np.nan
        if var_value_max is not None:
            var_data[var_data > var_value_max] = np.nan

        var_idx = df_generic.index
        var_dict[var_name_out] = var_data
        var_dict[index_name] = var_idx

        df_var = pd.DataFrame(data=var_dict)
        if index_name in list(df_var.columns):
            df_var.set_index(index_name, inplace=True)
        return df_var

    else:
        raise IOError('Dataframe variable does not exist')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray(data, geo_x, geo_y, geo_1d=True, time=None, var_name=None,
                  coord_name_x='west_east', coord_name_y='south_north', coord_name_time='time',
                  dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                  dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x]
        if time is not None:
            dims_order = [dim_name_y, dim_name_x, dim_name_time]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        if time is None:
            data_da = xr.DataArray(data,
                                   dims=dims_order,
                                   coords={coord_name_x: (dim_name_x, geo_x),
                                           coord_name_y: (dim_name_y, geo_y)})
        elif isinstance(time, pd.DatetimeIndex):

            if data.shape.__len__() == 2:
                data = np.expand_dims(data, axis=-1)

            data_da = xr.DataArray(data,
                                   dims=dims_order,
                                   coords={coord_name_x: (dim_name_x, geo_x),
                                           coord_name_y: (dim_name_y, geo_y),
                                           coord_name_time: (dim_name_time, time)})
        else:
            log_stream.error(' ===> Time obj is in wrong format')
            raise IOError('Variable time format not valid')

    else:
        log_stream.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    if var_name is not None:
        data_da.name = var_name

    return data_da
# -------------------------------------------------------------------------------------
