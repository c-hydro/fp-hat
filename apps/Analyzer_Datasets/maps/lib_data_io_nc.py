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

from lib_utils_io import read_obj
from lib_data_io_generic import create_darray
from lib_data_io_gzip import unzip_filename
from lib_utils_zip import remove_zip_extension
from lib_info_args import zip_extension, time_format_algorithm, logger_name

# Logging
log_stream = logging.getLogger(logger_name)

import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to merge raw datasets list
def merge_file_gridded(file_list_in,
                       var_name_terrain='terrain',
                       var_dim_x='west_east', var_dim_y='south_north', var_dim_time='time',
                       var_coord_x='west_east', var_coord_y='south_north', var_coord_time='time',
                       var_dim_order_2d=None, var_dim_order_3d=None,
                       tag_field_datasets='datasets', tag_field_attrs='attributes'
                       ):

    if not isinstance(file_list_in, list):
        file_list_in = [file_list_in]

    if var_dim_order_2d is None:
        var_dim_order_2d = [var_dim_y, var_dim_x]
    if var_dim_order_3d is None:
        var_dim_order_3d = [var_dim_y, var_dim_x, var_dim_time]

    time_collections = []
    var_collections_obj = {}
    var_collections_attrs = {}
    var_terrain_darray = None
    for file_step_in in file_list_in:

        obj_in = read_obj(file_step_in)

        dset_in = obj_in[tag_field_datasets]
        attrs_in = obj_in[tag_field_attrs]

        time_obj_in = dset_in[var_dim_time]

        var_name_list = list(dset_in.data_vars)

        if var_terrain_darray is None:
            if var_name_terrain in var_name_list:
                var_terrain_values = dset_in[var_name_terrain].values
                var_terrain_geo_y = dset_in[var_dim_y].values
                var_terrain_geo_x = dset_in[var_dim_x].values
                var_terrain_attrs = dset_in.attrs

                var_terrain_darray = create_darray(var_terrain_values, var_terrain_geo_x, var_terrain_geo_y,
                                                   var_name=var_name_terrain,
                                                   coord_name_x=var_coord_x, coord_name_y=var_coord_y,
                                                   dim_name_x=var_dim_x, dim_name_y=var_dim_y,
                                                   dims_order=var_dim_order_2d)

            else:
                log_stream.error(' ===> Terrain variable is not defined in the DataSet')
                raise IOError('Terrain variable must be defined in the DataSet')

        if time_obj_in.shape[0] == 1:

            time_values_in = time_obj_in.values[0]

            time_stamp_in = pd.Timestamp(time_values_in).strftime(time_format_algorithm)
            datetime_idx_in = pd.DatetimeIndex([time_values_in])

            log_stream.info(' --------> Collect time "' + time_stamp_in + '" ... ')

            for var_name_step in var_name_list:
                if var_name_step != var_name_terrain:

                    var_darray = dset_in[var_name_step]
                    var_darray = var_darray.expand_dims(time=datetime_idx_in, axis=-1)

                    attr_darray = attrs_in[var_name_step]

                    if var_name_step not in list(var_collections_obj):
                        var_collections_obj[var_name_step] = var_darray
                        var_collections_attrs[var_name_step] = attr_darray
                    else:
                        tmp_darray = var_collections_obj[var_name_step]
                        merge_darray = xr.merge([tmp_darray, var_darray])
                        var_collections_obj[var_name_step] = merge_darray

            time_collections.append(time_values_in)

            log_stream.info(' --------> Collect time "' + time_stamp_in + '" ... DONE')

        elif time_obj_in.shape[0] > 1:

            time_collections = []
            for time_value in time_obj_in.values:
                time_collections.append(time_value)

            for var_name_step in var_name_list:
                if var_name_step != var_name_terrain:

                    var_darray = dset_in[var_name_step]
                    attr_darray = attrs_in[var_name_step]

                    var_collections_obj[var_name_step] = var_darray
                    var_collections_attrs[var_name_step] = attr_darray

        else:
            log_stream.error(' ===> Variable time steps are equal to zero')
            raise IOError('Variable time must be greater than 0')

    # Compose DataSet
    log_stream.info(' --------> Compose unique datasets  ... ')
    datetime_idx_collections = pd.DatetimeIndex(time_collections)

    var_dset_collections = xr.Dataset(coords={var_coord_time: ([var_dim_time], datetime_idx_collections)})
    var_dset_collections.coords[var_coord_time] = var_dset_collections.coords[var_coord_time].astype('datetime64[ns]')

    var_dset_collections[var_name_terrain] = var_terrain_darray
    var_dset_collections[var_name_terrain].attrs = var_terrain_attrs

    var_attrs_collections = {}
    for var_key, var_obj in var_collections_obj.items():
        var_attrs = var_collections_attrs[var_key]

        if isinstance(var_obj, xr.Dataset):
            var_darray = var_obj[var_key]
        elif isinstance(var_obj, xr.DataArray):
            var_darray = deepcopy(var_obj)
        else:
            log_stream.error(' ===> Variable obj format is not allowed')
            raise IOError('Variable obj format must be DataArray or DataSet')

        var_dset_collections[var_key] = var_darray
        var_dset_collections[var_key].attrs = var_attrs

        var_attrs_collections[var_key] = var_attrs

    log_stream.info(' --------> Compose unique datasets  ... DONE')

    return var_dset_collections, var_attrs_collections

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to organize netcdf gridded attributes
def organize_attrs_gridded(data_file_dset, data_attr_settings, data_map_variable, data_attr_ref='var_name_data'):

    data_attr_tmp = {}
    for data_key, data_fields in data_attr_settings.items():
        for field_key, field_value in data_fields.items():
            if field_key == data_attr_ref:
                data_attr_tmp[field_value] = data_fields
                break

    data_attr_collection = {}
    for data_key, data_attr_fields in data_attr_tmp.items():

        data_attr_file = data_file_dset[data_key].attrs
        data_attr_merge = {**data_attr_file, **data_attr_fields}

        data_attr_collection[data_key] = data_attr_merge

    return data_attr_collection

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to organize netcdf gridded file
def organize_file_gridded(data_time_step, data_file_dset, data_file_variables,
                          data_terrain_darray,
                          data_limits_variables=None, data_units_variables=None,
                          var_name_terrain='terrain',
                          var_dim_x='west_east', var_dim_y='south_north', var_dim_time='time',
                          var_coord_x='west_east', var_coord_y='south_north', var_coord_time='time',
                          var_dim_order_2d=None, var_dim_order_3d=None, var_nodata=None):

    var_list_geo_x = ['Longitude', 'longitude']
    var_list_geo_y = ['Latitude', 'latitude']

    if var_dim_order_2d is None:
        var_dim_order_2d = [var_dim_y, var_dim_x]
    if var_dim_order_3d is None:
        var_dim_order_3d = [var_dim_y, var_dim_x, var_dim_time]
    if var_nodata is None:
        var_nodata = np.nan

    var_terrain_values = data_terrain_darray.values
    var_terrain_geo_y = data_terrain_darray['south_north'].values
    var_terrain_geo_x = data_terrain_darray['west_east'].values
    var_terrain_attrs = data_terrain_darray.attrs

    if isinstance(data_file_dset, xr.Dataset):
        pass
    else:
        log_stream.error(' ===> DataObj format is not allowed')
        raise IOError('DataObj format must be DataSet')

    if 'time' in list(data_file_dset.coords):
        if data_file_dset['time'].shape[0] == 1:
            var_datetime_index = pd.DatetimeIndex(data_file_dset['time'].values)
        else:
            var_datetime_index = pd.DatetimeIndex(data_file_dset['time'].values)
    else:
        var_datetime_index = pd.DatetimeIndex([data_time_step])

    var_geo_x = None
    for var_step_geo_x in var_list_geo_x:
        if var_step_geo_x in list(data_file_dset.variables):
            var_geo_x = var_step_geo_x
            break
    var_geo_y = None
    for var_step_geo_y in var_list_geo_y:
        if var_step_geo_y in list(data_file_dset.variables):
            var_geo_y = var_step_geo_y
            break

    if (var_geo_x is not None) and (var_geo_y is not None):

        tmp_file_geo_y = data_file_dset[var_geo_y].values
        tmp_file_geo_x = data_file_dset[var_geo_x].values

        if tmp_file_geo_y.ndim == 1:
            data_file_geo_x, data_file_geo_y = np.meshgrid(tmp_file_geo_x, tmp_file_geo_y)
        elif tmp_file_geo_y.ndim == 2:
            data_file_geo_y = deepcopy(tmp_file_geo_y)
        else:
            log_stream.error(' ===> Format of y coordinates is not supported')
            raise NotImplemented('Case not implemented yet')

        data_file_geo_y_upper = data_file_geo_y[0, 0]
        data_file_geo_y_lower = data_file_geo_y[-1, 0]
        if data_file_geo_y_lower > data_file_geo_y_upper:
            data_file_flipud_flag = True
        else:
            data_file_flipud_flag = False
    else:
        log_stream.error(' ===> Variables "' + str(var_list_geo_y) +
                         '" and/or "' + str(var_list_geo_x) + '" is/are not available in the DataSet')
        raise IOError('Check your DataSet to find the name of x and y coordinates')

    var_dset = xr.Dataset(coords={var_coord_time: ([var_dim_time], var_datetime_index)})
    var_dset.coords[var_coord_time] = var_dset.coords[var_coord_time].astype('datetime64[ns]')

    var_terrain_darray = create_darray(var_terrain_values, var_terrain_geo_x, var_terrain_geo_y,
                                       var_name=var_name_terrain,
                                       coord_name_x=var_coord_x, coord_name_y=var_coord_y,
                                       dim_name_x=var_dim_x, dim_name_y=var_dim_y)
    var_dset[var_name_terrain] = var_terrain_darray
    var_dset[var_name_terrain].attrs = var_terrain_attrs

    for var_key, var_name in data_file_variables.items():
        if var_name in list(data_file_dset.variables):
            var_data_values = data_file_dset[var_name].values
            var_data_attrs = data_file_dset[var_name].attrs
            var_data_dims = data_file_dset[var_name].dims

            if var_dim_time in list(var_data_dims):
                loc_time_dim = list(var_data_dims).index(var_dim_time)
                if loc_time_dim != 2 and loc_time_dim == 0:
                    log_stream.warning(' ===> The "' + var_dim_time +
                                       '" dimension for 3D datasets not in last dims position')
                    log_stream.warning(' ===> Actual "' + var_dim_time + '" position is ' + str(loc_time_dim))

                    var_data_shape = var_data_values.shape
                    var_data_reshape = np.zeros([var_data_shape[1], var_data_shape[2], var_data_shape[0]])
                    for id in range(0, var_data_shape[0]):
                        var_data_tmp = var_data_values[id, :, :]
                        var_data_reshape[:, :, id] = var_data_tmp

                    var_data_values = deepcopy(var_data_reshape)

            if data_file_flipud_flag:
                var_data_values = np.flipud(var_data_values)

            var_limits = None
            if data_limits_variables is not None:
                if var_key in list(data_limits_variables.keys()):
                    var_limits = data_limits_variables[var_key]
                    if var_limits[0] is not None:
                        var_data_values[var_data_values < var_limits[0]] = var_nodata
                    if var_limits[1] is not None:
                        var_data_values[var_data_values > var_limits[1]] = var_nodata
            if 'Valid_range' in list(var_data_attrs.keys()):
                if var_limits is not None:
                    var_limits_str = [str(item) for item in var_limits]
                    var_limits_str = ','.join(var_limits_str)
                    var_data_attrs['Valid_range'] = var_limits_str
            else:
                if var_limits is None:
                    var_data_attrs['Valid_range'] = None
                else:
                    var_limits_str = [str(item) for item in var_limits]
                    var_limits_str = ','.join(var_limits_str)
                    var_data_attrs['Valid_range'] = var_limits_str
            var_units = None
            if data_units_variables is not None:
                if var_key in list(data_units_variables.keys()):
                    var_units = data_units_variables[var_key]
            if 'units' in list(var_data_attrs.keys()):
                if var_units is not None:
                    if isinstance(var_units, str):
                        var_data_attrs['units'] = var_units
                    else:
                        log_stream.error(' ===> Variable units is defined by wrong type.')
                        raise IOError('Obj is expected in string format')
            else:
                if var_units is None:
                    var_data_attrs['units'] = None
                else:
                    var_data_attrs['units'] = var_units

            if var_data_values.ndim == 2:

                var_data_darray_unmasked = create_darray(var_data_values, var_terrain_geo_x, var_terrain_geo_y,
                                                         var_name=var_key,
                                                         coord_name_x=var_coord_x, coord_name_y=var_coord_y,
                                                         dim_name_x=var_dim_x, dim_name_y=var_dim_y,
                                                         dims_order=var_dim_order_2d)

                var_data_darray_masked = var_data_darray_unmasked.where(np.isfinite(var_terrain_darray), np.nan)

            elif var_data_values.ndim == 3:

                var_data_darray_unmasked = create_darray(var_data_values, var_terrain_geo_x, var_terrain_geo_y,
                                                         var_name=var_key,
                                                         coord_name_x=var_coord_x, coord_name_y=var_coord_y,
                                                         coord_name_time=var_coord_time,
                                                         dim_name_x=var_dim_x, dim_name_y=var_dim_y,
                                                         dim_name_time=var_dim_time,
                                                         dims_order=var_dim_order_3d)

                var_data_darray_masked = var_data_darray_unmasked.where(np.isfinite(var_terrain_darray), np.nan)

            else:
                log_stream.error(' ===> Variable DataArray format is not allowed')
                raise IOError('DataArray format must be 2D or 3D')

            '''
            # Debug variable(s)
            map_terrain_geo_x, map_terrain_geo_y = np.meshgrid(var_terrain_geo_x, var_terrain_geo_y)
            
            plt.figure()
            plt.imshow(var_data_darray_masked[:,:,0])
            plt.colorbar()

            plt.figure()
            plt.imshow(var_terrain_darray)
            plt.colorbar()
            plt.show()
            '''

            var_dset[var_key] = var_data_darray_masked
            var_dset[var_key].attrs = var_data_attrs

    return var_dset

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read netcdf gridded file
def read_file_gridded(file_path, folder_name_tmp=None, clean_tmp=True):

    if folder_name_tmp is None:
        folder_name_tmp = '/tmp'

    if os.path.exists(file_path):
        if file_path.endswith(zip_extension):
            file_path_noext = remove_zip_extension(file_path)
            folder_name_noext, file_name_noext = os.path.split(file_path_noext)
            file_path_tmp = os.path.join(folder_name_tmp, file_name_noext)

            unzip_filename(file_path, file_path_tmp)

        else:
            file_path_tmp = file_path
    else:
        file_path_tmp = None

    if file_path_tmp is not None:
        file_dset_tmp = xr.open_mfdataset(file_path_tmp)
        if file_path_tmp != file_path:
            if clean_tmp:
                if os.path.exists(file_path_tmp):
                    os.remove(file_path_tmp)
    else:
        file_dset_tmp = None

    return file_dset_tmp

# -------------------------------------------------------------------------------------
