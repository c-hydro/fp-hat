"""
Class Features

Name:          lib_jupyter_data_geo_ascii
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""

#######################################################################################
# Libraries
import logging
import rasterio
import os

import numpy as np

from rasterio.crs import CRS

from lib_data_io_generic import create_darray_2d
from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
logging.getLogger("rasterio").setLevel(logging.WARNING)
logging.getLogger("fiona").setLevel(logging.WARNING)

# Debug
import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to read an ascii grid file
def read_data_grid(file_name, output_format='data_array', output_dtype='float32',
                   var_limit_min=None, var_limit_max=None, var_proj='EPSG:4326'):

    try:
        dset = rasterio.open(file_name)
        bounds = dset.bounds
        res = dset.res
        transform = dset.transform
        data = dset.read()

        if dset.crs is None:
            crs = CRS.from_string(var_proj)
        else:
            crs = dset.crs

        if output_dtype == 'float32':
            values = np.float32(data[0, :, :])
        else:
            log_stream.error(' ===> Data type is not allowed.')
            raise NotImplementedError('Case not implemented yet')

        if var_limit_min is not None:
            var_limit_min = np.float32(var_limit_min)
            values[values < var_limit_min] = np.nan
        if var_limit_max is not None:
            var_limit_max = np.float32(var_limit_max)
            values[values > var_limit_max] = np.nan

        decimal_round_geo = 7

        center_right = bounds.right - (res[0] / 2)
        center_left = bounds.left + (res[0] / 2)
        center_top = bounds.top - (res[1] / 2)
        center_bottom = bounds.bottom + (res[1] / 2)

        lon = np.arange(center_left, center_right + np.abs(res[0] / 2), np.abs(res[0]), float)
        lat = np.flip(np.arange(center_bottom, center_top + np.abs(res[1] / 2), np.abs(res[1]), float), axis=0)
        lons, lats = np.meshgrid(lon, lat)

        lat_upper = lats[0, 0]
        lat_lower = lats[-1, 0]
        if lat_lower > lat_upper:
            lats = np.flipud(lats)
            values = np.flipud(values)

        min_lon_round = round(np.min(lons), decimal_round_geo)
        max_lon_round = round(np.max(lons), decimal_round_geo)
        min_lat_round = round(np.min(lats), decimal_round_geo)
        max_lat_round = round(np.max(lats), decimal_round_geo)

        center_right_round = round(center_right, decimal_round_geo)
        center_left_round = round(center_left, decimal_round_geo)
        center_bottom_round = round(center_bottom, decimal_round_geo)
        center_top_round = round(center_top, decimal_round_geo)

        assert min_lon_round == center_left_round
        assert max_lon_round == center_right_round
        assert min_lat_round == center_bottom_round
        assert max_lat_round == center_top_round

        data_attrs = {'transform': transform, 'crs': crs,
                        'bbox': [bounds.left, bounds.bottom, bounds.right, bounds.top],
                        'bb_left': bounds.left, 'bb_right': bounds.right,
                        'bb_top': bounds.top, 'bb_bottom': bounds.bottom,
                        'res_lon': res[0], 'res_lat': res[1]}

        if output_format == 'data_array':

            data_obj = create_darray_2d(values, lons[0, :], lats[:, 0],
                                        coord_name_x='west_east', coord_name_y='south_north',
                                        dim_name_x='west_east', dim_name_y='south_north')

            data_obj.attrs = data_attrs

        elif output_format == 'dictionary':

            data_var = {'values': values, 'longitude': lons[0, :], 'latitude': lats[:, 0]}
            data_obj = {**data_var, **data_attrs}

        else:
            log_stream.error(' ===> File static "' + file_name + '" output format not allowed')
            raise NotImplementedError('Case not implemented yet')

    except IOError as io_error:

        data_obj = None
        log_stream.warning(' ===> File static in ascii grid was not correctly open with error "' + str(io_error) + '"')
        log_stream.warning(' ===> Filename "' + os.path.split(file_name)[1] + '"')

    return data_obj
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to load an ascii vector file
def read_data_vector(file_name):

    file_handle = open(file_name, 'r')
    file_lines = file_handle.readlines()
    file_handle.close()

    vector_frame = [float(elem.strip('\n')) for elem in file_lines]

    return vector_frame

# -------------------------------------------------------------------------------------
