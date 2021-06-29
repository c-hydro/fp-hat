"""
Library Features:

Name:          lib_utils_io
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210408'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging

import os
import pickle
import json
import tempfile

import pandas as pd
import xarray as xr
import numpy as np

from copy import deepcopy

from tools.preprocessing_tool_source2nc_converter.lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Attr(s) decoded
attrs_reserved = ['coordinates']
attrs_decoded = ['_FillValue', 'scale_factor']
attr_valid_range = 'Valid_range'
attr_missing_value = 'Missing_value'

# Defined attributes look-up table
attributes_defined_lut = {
    'blocking_attrs': ['coordinates'],
    'encoding_attrs': {
        '_FillValue': ['_FillValue', 'fill_value'],
        'scale_factor': ['scale_factor', 'ScaleFactor']
    },
    'filtering_attrs': {
        'Valid_range': ['Valid_range', 'valid_range'],
        'Missing_value': ['Missing_value', 'missing_value']
    }
}
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_2d(data, geo_x, geo_y, geo_1d=True, time=None, name=None,
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

    if name is not None:
        data_da.name = name

    return data_da
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_3d(data, time, geo_x, geo_y, geo_1d=True, var_name=None,
                     coord_name_x='west_east', coord_name_y='south_north', coord_name_time='time',
                     dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x, dim_name_time]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        data_da = xr.DataArray(data,
                               name=var_name,
                               dims=dims_order,
                               coords={coord_name_time: (dim_name_time, time),
                                       coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)})
    else:
        log_stream.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to select attributes
def select_attrs(var_attrs_raw):

    var_attrs_select = {}
    if var_attrs_raw:
        for var_key, var_value in var_attrs_raw.items():
            if var_value is not None:
                if var_key not in attrs_decoded:
                    if isinstance(var_value, list):
                        var_string = [str(value) for value in var_value]
                        var_value = ','.join(var_string)
                    if isinstance(var_value, dict):
                        var_string = json.dumps(var_value)
                        var_value = var_string
                    if var_key in attrs_reserved:
                        var_value = None
                    if var_value is not None:
                        var_attrs_select[var_key] = var_value

    return var_attrs_select
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create dataset
def create_dset(var_data_values,
                var_geo_values, var_geo_x, var_geo_y,
                var_data_time=None,
                var_data_name='variable', var_geo_name='terrain', var_data_attrs=None, var_geo_attrs=None,
                var_geo_1d=False,
                file_attributes=None,
                coord_name_x='longitude', coord_name_y='latitude', coord_name_time='time',
                dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                dims_order_2d=None, dims_order_3d=None):

    var_geo_x_tmp = var_geo_x
    var_geo_y_tmp = var_geo_y
    if var_geo_1d:
        if (var_geo_x.shape.__len__() == 2) and (var_geo_y.shape.__len__() == 2):
            var_geo_x_tmp = var_geo_x[0, :]
            var_geo_y_tmp = var_geo_y[:, 0]
    else:
        if (var_geo_x.shape.__len__() == 1) and (var_geo_y.shape.__len__() == 1):
            var_geo_x_tmp, var_geo_y_tmp = np.meshgrid(var_geo_x, var_geo_y)

    if dims_order_2d is None:
        dims_order_2d = [dim_name_y, dim_name_x]
    if dims_order_3d is None:
        dims_order_3d = [dim_name_y, dim_name_x, dim_name_time]

    if isinstance(var_data_time, pd.Timestamp):
        var_data_time = pd.DatetimeIndex([var_data_time])
    elif isinstance(var_data_time, pd.DatetimeIndex):
        pass
    else:
        log_stream.error(' ===> Time format is not allowed')
        raise NotImplemented('Case not implemented yet')

    var_dset = xr.Dataset(coords={coord_name_time: ([dim_name_time], var_data_time)})
    var_dset.coords[coord_name_time] = var_dset.coords[coord_name_time].astype('datetime64[ns]')

    if file_attributes:
        if isinstance(file_attributes, dict):
            var_dset.attrs = file_attributes

    var_da_terrain = xr.DataArray(np.flipud(var_geo_values),  name=var_geo_name,
                                  dims=dims_order_2d,
                                  coords={coord_name_x: ([dim_name_y, dim_name_x], var_geo_x_tmp),
                                          coord_name_y: ([dim_name_y, dim_name_x], np.flipud(var_geo_y_tmp))})
    var_dset[var_geo_name] = var_da_terrain
    var_geo_attrs_select = select_attrs(var_geo_attrs)

    if var_geo_attrs_select is not None:
        var_dset[var_geo_name].attrs = var_geo_attrs_select

    if var_data_values.shape.__len__() == 2:
        var_da_data = xr.DataArray(np.flipud(var_data_values), name=var_data_name,
                                   dims=dims_order_2d,
                                   coords={coord_name_x: ([dim_name_y, dim_name_x], var_geo_x_tmp),
                                           coord_name_y: ([dim_name_y, dim_name_x], np.flipud(var_geo_y_tmp))})
    elif var_data_values.shape.__len__() == 3:
        var_da_data = xr.DataArray(np.flipud(var_data_values), name=var_data_name,
                                   dims=dims_order_3d,
                                   coords={coord_name_time: ([dim_name_time], var_data_time),
                                           coord_name_x: ([dim_name_y, dim_name_x], var_geo_x_tmp),
                                           coord_name_y: ([dim_name_y, dim_name_x], np.flipud(var_geo_y_tmp))})
    else:
        raise NotImplemented

    if var_data_attrs is not None:
        if attr_valid_range in list(var_data_attrs.keys()):
            valid_range = var_data_attrs[attr_valid_range]
            var_da_data = clip_map(var_da_data, valid_range)

        if attr_missing_value in list(var_data_attrs.keys()):
            missing_value = var_data_attrs[attr_missing_value]
            var_da_data = var_da_data.where(var_da_terrain > 0, other=missing_value)

    var_dset[var_data_name] = var_da_data
    if var_data_attrs is not None:
        var_data_attrs_select = select_attrs(var_data_attrs)
    else:
        var_data_attrs_select = None

    if var_data_attrs_select is not None:
        var_dset[var_data_name].attrs = var_data_attrs_select

    return var_dset

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write dataset
def write_dset(file_name,
               dset_data, dset_attrs=None,
               dset_mode='w', dset_engine='h5netcdf', dset_compression=0, dset_format='NETCDF4',
               dim_key_time='time', fill_data=-9999.0, dset_type='float32'):

    dset_encoded = dict(zlib=True, complevel=dset_compression, _FillValue=fill_data, dtype=dset_type)

    dset_encoding = {}
    for var_name in dset_data.data_vars:

        if isinstance(var_name, bytes):
            var_name_upd = var_name.decode("utf-8")
            dset_data = var_name.rename({var_name: var_name_upd})
            var_name = var_name_upd

        var_data = dset_data[var_name]
        var_attrs = dset_data[var_name].attrs
        if len(var_data.dims) > 0:
            dset_encoding[var_name] = deepcopy(dset_encoded)

        if var_attrs:
            for attr_key, attr_value in var_attrs.items():
                if attr_key in attrs_decoded:

                    dset_encoding[var_name][attr_key] = {}

                    if isinstance(attr_value, list):
                        attr_string = [str(value) for value in attr_value]
                        attr_value = ','.join(attr_string)

                    dset_encoding[var_name][attr_key] = attr_value

            if '_FillValue' not in list(dset_encoding[var_name].keys()):
                dset_encoding[var_name]['_FillValue'] = fill_data

    if dim_key_time in list(dset_data.coords):
        dset_encoding[dim_key_time] = {'calendar': 'gregorian'}

    dset_data.to_netcdf(path=file_name, format=dset_format, mode=dset_mode, engine=dset_engine,
                        encoding=dset_encoding)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write dataset
def write_dset_NOTUSE(file_name,
               dset_data, dset_attrs=None,
               dset_mode='w', dset_engine='h5netcdf', dset_compression=0, dset_format='NETCDF4',
               dim_key_time='time', fill_data=-9999.0, dset_type='float32'):

    dset_encoded = dict(zlib=True, complevel=dset_compression, _FillValue=fill_data, dtype=dset_type)

    dset_encoding = {}
    for var_name in dset_data.data_vars:

        if isinstance(var_name, bytes):
            var_name_upd = var_name.decode("utf-8")
            dset_data = var_name.rename({var_name: var_name_upd})
            var_name = var_name_upd

        var_data = dset_data[var_name]
        var_attrs = dset_data[var_name].attrs
        if len(var_data.dims) > 0:
            dset_encoding[var_name] = deepcopy(dset_encoded)

        if var_attrs:
            for attr_key, attr_value in var_attrs.items():
                if attr_key in attrs_decoded:

                    dset_encoding[var_name][attr_key] = {}

                    if isinstance(attr_value, list):
                        attr_string = [str(value) for value in attr_value]
                        attr_value = ','.join(attr_string)

                    dset_encoding[var_name][attr_key] = attr_value

            if '_FillValue' not in list(dset_encoding[var_name].keys()):
                dset_encoding[var_name]['_FillValue'] = fill_data

    if dim_key_time in list(dset_data.coords):
        dset_encoding[dim_key_time] = {'calendar': 'gregorian'}

    dset_data.to_netcdf(path=file_name, format=dset_format, mode=dset_mode, engine=dset_engine,
                        encoding=dset_encoding)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a tmp name
def create_filename_tmp(prefix='tmp_', suffix='.tiff', folder=None):

    if folder is None:
        folder = '/tmp'

    with tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, suffix=suffix, delete=False) as tmp:
        temp_file_name = tmp.name
    return temp_file_name
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data obj
def read_obj(file_name):
    if os.path.exists(file_name):
        data = pickle.load(open(file_name, "rb"))
    else:
        data = None
    return data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write data obj
def write_obj(file_name, data):
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# -------------------------------------------------------------------------------------
