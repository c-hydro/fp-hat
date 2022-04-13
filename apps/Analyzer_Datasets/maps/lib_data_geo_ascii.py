"""
Class Features

Name:          lib_data_geo_ascii
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

from lib_data_io_generic import create_darray
from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
logging.getLogger("rasterio").setLevel(logging.WARNING)
logging.getLogger("fiona").setLevel(logging.WARNING)

# Debug
import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Default method variable(s)
info_default_fields = ['rows', 'cols', 'xll_corner', 'yll_corner', 'cell_size']
map_default_fields = ['nrows', 'ncols', 'xllcorner', 'yllcorner', 'cellsize']
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data grid information
def create_data_grid(info_grid, info_expected_fields=None, map_expected_fields=None,
                     tag_geo_values='data', grid_format='data_array',
                     tag_geo_x='geo_x', tag_geo_y='geo_y',
                     tag_nodata='nodata_value', value_no_data=-9999.0, value_default_data=1):

    if info_expected_fields is None:
        info_expected_fields = info_default_fields
    if map_expected_fields is None:
        map_expected_fields = map_default_fields

    data_grid = {}
    if info_grid is not None:
        if isinstance(info_grid, dict):
            if set(info_expected_fields).issubset(info_grid):
                if any(field is not None for field in info_grid.values()):
                    for info_field, map_field in zip(info_expected_fields, map_expected_fields):
                        data_grid[map_field] = info_grid[info_field]

                    xll = data_grid['xllcorner']
                    yll = data_grid['yllcorner']
                    nrows = data_grid['nrows']
                    ncols = data_grid['ncols']
                    res = data_grid['cellsize']

                    geo_x_start = xll + res / 2
                    geo_x_end = xll + res / 2 + res * (ncols - 1)
                    geo_x_values = np.linspace(geo_x_start, geo_x_end, ncols)

                    geo_y_start = yll + res / 2
                    geo_y_end = yll + res / 2 + res * (nrows - 1)
                    geo_y_values = np.linspace(geo_y_start, geo_y_end, nrows)

                    # geo_x_values = np.arange(xll + res / 2, xll + res / 2 + res * ncols, res)
                    # geo_y_values = np.arange(yll + res / 2, yll + res / 2 + res * nrows, res)

                    geo_x_values_2d, geo_y_values_2d = np.meshgrid(geo_x_values, geo_y_values)

                    geo_y_right = geo_x_values_2d[0, 0]
                    geo_y_left = geo_x_values_2d[0, -1]
                    geo_y_upper = geo_y_values_2d[0, 0]
                    geo_y_lower = geo_y_values_2d[-1, 0]
                    if geo_y_lower > geo_y_upper:
                        geo_y_values_2d = np.flipud(geo_y_values_2d)

                    geo_data_values = np.zeros([geo_y_values.shape[0], geo_x_values.shape[0]])
                    geo_data_values[:, :] = value_default_data

                    if grid_format == 'dictionary':

                        data_grid[tag_geo_values] = geo_data_values
                        data_grid[tag_geo_x] = geo_x_values_2d[0, :]
                        data_grid[tag_geo_y] = geo_y_values_2d[:, 0]

                        if tag_nodata not in list(data_grid.keys()):
                            data_grid[tag_nodata] = value_no_data

                    elif grid_format == 'data_array':

                        data_attrs = {
                            'xllcorner': data_grid['xllcorner'], 'yllcorner': data_grid['yllcorner'],
                            'nrows': data_grid['nrows'], 'ncols': data_grid['ncols'],
                            'cellsize': data_grid['cellsize'], tag_nodata: value_no_data}

                        data_grid = create_darray(
                            geo_data_values, geo_x_values_2d[0, :], geo_y_values_2d[:, 0],
                            coord_name_x='west_east', coord_name_y='south_north',
                            dim_name_x='west_east', dim_name_y='south_north')

                        data_grid.attrs = data_attrs
                    else:
                        log_stream.error(' ===> Grid format "' + grid_format + '" is not expected')
                        raise NotImplementedError('Only "dictionary" and "data_array" formats are available.')
                else:
                    log_stream.error(' ===> Some grid values are set to NoneType.')
                    raise RuntimeError('Create grid object is not possible.')
            else:
                log_stream.error(' ===> Some grid fields are not available.')
                raise RuntimeError('Create grid object is not possible.')
        else:
            log_stream.error(' ===> Grid information must be in dictionary format.')
            raise RuntimeError('Create grid object is not possible.')
    else:
        log_stream.error(' ===> Grid information are not defined.')
        raise RuntimeError('Create grid object is not possible.')

    return data_grid
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to init data grid with default structure
def init_data_grid(data_obj_ref, value_obj_default=-9999.0):

    values_obj_default = np.zeros(shape=(data_obj_ref.shape[0], data_obj_ref.shape[1]))
    values_obj_default[:, :] = value_obj_default

    lons_obj_array = data_obj_ref['west_east'].values
    lats_obj_array = data_obj_ref['south_north'].values
    lons_obj_grid, lats_obj_grid = np.meshgrid(lons_obj_array, lats_obj_array)

    data_obj_default = create_darray(
        values_obj_default, lons_obj_grid[0, :], lats_obj_grid[:, 0],
        coord_name_x='west_east', coord_name_y='south_north',
        dim_name_x='west_east', dim_name_y='south_north')

    return data_obj_default
# -------------------------------------------------------------------------------------


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

        if center_bottom > center_top:
            log_stream.warning(' ===> Coords "center_bottom": ' + str(center_bottom) + ' is greater than "center_top": '
                               + str(center_top) + '. Try to inverse the bottom and top coords. ')
            center_tmp = center_top
            center_top = center_bottom
            center_bottom = center_tmp

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

            data_obj = create_darray(values, lons[0, :], lats[:, 0],
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
