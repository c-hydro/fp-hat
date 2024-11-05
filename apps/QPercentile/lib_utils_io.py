"""
Library Features:

Name:          lib_utils_io
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20241104'
Version:       '1.1.0'
"""
# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import tempfile

import numpy as np
import pandas as pd
import xarray as xr

from lib_info_args import logger_name

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to define ensemble list
def define_ensemble_list(ensemble_min=0, ensemble_max=1, ensemble_format='{:03d}'):
    ensemble_list = [ensemble_format.format(ensemble_id) for ensemble_id in range(ensemble_min, ensemble_max + 1)]
    return ensemble_list
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to create a tmp name
def create_filename_tmp(prefix='tmp_', suffix='.tiff', folder=None):

    if folder is None:
        folder = '/tmp'

    with tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, suffix=suffix, delete=False) as tmp:
        temp_file_name = tmp.name
    return temp_file_name
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to create a data frame
def create_dframe(data_values, data_index, column_name='data_{:}', index_name='index'):

    if data_index is not None:
        data_frame = pd.DataFrame(data_values, index=data_index, columns=[column_name])
        data_frame.index.name = index_name
    else:
        data_frame = pd.DataFrame(data_values, columns=[column_name])
        data_frame.index.name = index_name

    return data_frame
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to create a data array
def create_darray(data, geo_x, geo_y, geo_1d=False, time=None, name=None,
                  coord_name_x='longitude', coord_name_y='latitude', coord_name_time='time',
                  dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                  dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x]
    if time is not None:
        dims_order = [dim_name_time, dim_name_y, dim_name_x]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]
    else:

        if geo_x.shape.__len__() == 1:
            if coord_name_x == dim_name_x:
                coord_name_x = 'west_east'
            if coord_name_y == dim_name_y:
                coord_name_y = 'south_north'

            geo_x, geo_y = np.meshgrid(geo_x, geo_y)

            dim_name_x = dim_name_y = [dim_name_y, dim_name_x]

        elif geo_x.shape.__len__() == 2:
            if coord_name_x == dim_name_x:
                coord_name_x = 'west_east'
            if coord_name_y == dim_name_y:
                coord_name_y = 'south_north'

            dim_name_x = dim_name_y = [dim_name_y, dim_name_x]
        else:
            log_stream.error(' ===> Longitude and Latitude must be 2d')
            raise IOError('Variable shape is not valid')

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
                               coords={
                                   coord_name_time: (dim_name_time, time),
                                   coord_name_y: (dim_name_y, geo_y),
                                   coord_name_x: (dim_name_x, geo_x)
                               })
    elif isinstance(time, list):

        if data.shape.__len__() == 2:
            data = np.expand_dims(data, axis=-1)

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={
                                   coord_name_time: (dim_name_time, time),
                                   coord_name_y: (dim_name_y, geo_y),
                                   coord_name_x: (dim_name_x, geo_x)
                               })

    else:
        log_stream.error(' ===> Time obj is in wrong format')
        raise IOError('Variable time format not valid')

    if name is not None:
        data_da.name = name

    return data_da
# ----------------------------------------------------------------------------------------------------------------------
