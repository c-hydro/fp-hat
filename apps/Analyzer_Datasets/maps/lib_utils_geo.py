"""
Library Features:

Name:          lib_utils_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200401'
Version:       '1.0.0'
"""

#################################################################################
# Libraries
import logging
import pyproj

from pysheds.grid import Grid

import numpy as np
import xarray as xr

from lib_info_args import logger_name

# Debug
import matplotlib.pylab as plt
#################################################################################


# --------------------------------------------------------------------------------
# Method to define section mask
def compute_section_mask(fdir_da, fdir_map=None, fdir_nodata=0, terrain_da=None, section_dframe=None,
                         str_delimiter=':'):

    fdir_values = fdir_da.values

    if fdir_map is None:
        fdir_map = [8, 9, 6, 3, 2, 1, 4, 7]

    geo_values = terrain_da.values
    geo_longitude = terrain_da['west_east'].values
    geo_latitude = terrain_da['south_north'].values
    geo_transform = terrain_da.attrs['transform']
    geo_crs = terrain_da.attrs['crs']

    grid_longitude, grid_latitude = np.meshgrid(geo_longitude, geo_latitude)

    mask_values = np.zeros([fdir_values.shape[0], fdir_values.shape[1]], dtype=bool)
    mask_values[:, :] = True

    grid = Grid()
    grid.add_gridded_data(data=fdir_values, data_name='fdir',
                          affine=geo_transform,
                          crs=pyproj.Proj(geo_crs),
                          nodata=fdir_nodata)
    grid.add_gridded_data(data=mask_values, data_name='mask',
                          affine=geo_transform,
                          crs=pyproj.Proj(geo_crs),
                          nodata=False)

    section_obj = {}
    for section_id, section_fields in section_dframe.iterrows():

        section_idx_y = section_fields['hmc_idx_x']
        section_idx_x = section_fields['hmc_idx_y']
        section_name = section_fields['section_name']
        section_domain = section_fields['section_domain']
        # section_drained_area_db = section_fields['section_drained_area']
        section_tag = str_delimiter.join([section_domain, section_name])

        section_x = section_idx_x - 1
        section_y = section_idx_y - 1
        section_mask = 'section_mask'

        grid.catchment(data=grid.fdir, x=section_x, y=section_y,
                       dirmap=fdir_map, out_name=section_mask,
                       recursionlimit=15000, nodata_out=0, ytype='index')

        section_mask = np.array(grid.section_mask).astype(np.float32)

        section_mask[section_mask == 0] = 0
        section_mask[geo_values < 0] = 0
        section_mask[section_mask >= 1] = 1

        geo_latitude = np.flipud(geo_latitude)

        section_da = create_darray_2d(section_mask, geo_longitude, geo_latitude,
                                      coord_name_x='Longitude', coord_name_y='Latitude',
                                      dim_name_x='west_east', dim_name_y='south_north',
                                      dims_order=['south_north', 'west_east'])

        section_obj[section_tag] = {}
        section_obj[section_tag] = section_da

    return section_obj

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to define section area
def compute_section_area(fdir_da, fdir_map=None, fdir_nodata=0, terrain_da=None, section_dframe=None,
                         drainage_area_tag='section_drainage_area_cmp',
                         drainage_area_units='Km^2', drainage_area_rounding=1,
                         str_delimiter=':'):

    fdir_values = fdir_da.values

    if fdir_map is None:
        fdir_map = [8, 9, 6, 3, 2, 1, 4, 7]

    geo_values = terrain_da.values
    geo_longitude = terrain_da['west_east'].values
    geo_latitude = terrain_da['south_north'].values
    geo_transform = terrain_da.attrs['transform']
    geo_crs = terrain_da.attrs['crs']

    grid_longitude, grid_latitude = np.meshgrid(geo_longitude, geo_latitude)
    area_cell_values = compute_cell_area(grid_longitude, grid_latitude,
                                         np.abs(geo_transform[0]), np.abs(geo_transform[4]))

    mask_values = np.zeros([fdir_values.shape[0], fdir_values.shape[1]], dtype=bool)
    mask_values[:, :] = True

    grid = Grid()
    grid.add_gridded_data(data=fdir_values, data_name='fdir',
                          affine=geo_transform,
                          crs=pyproj.Proj(geo_crs),
                          nodata=fdir_nodata)
    grid.add_gridded_data(data=mask_values, data_name='mask',
                          affine=geo_transform,
                          crs=pyproj.Proj(geo_crs),
                          nodata=False)

    section_data_default = np.zeros([section_dframe.shape[0]])
    section_data_default[:] = np.nan
    section_dframe[drainage_area_tag] = section_data_default
    for section_id, section_fields in section_dframe.iterrows():

        section_idx_y = section_fields['hmc_idx_x']
        section_idx_x = section_fields['hmc_idx_y']
        section_name = section_fields['section_name']
        section_domain = section_fields['section_domain']
        section_drainage_area_db = section_fields['section_drained_area']
        section_tag = str_delimiter.join([section_domain, section_name])

        section_x = section_idx_x - 1
        section_y = section_idx_y - 1
        section_mask = 'section_mask'

        grid.catchment(data=grid.fdir, x=section_x, y=section_y,
                       dirmap=fdir_map, out_name=section_mask,
                       recursionlimit=15000, nodata_out=0, ytype='index')

        section_mask = np.array(grid.section_mask).astype(np.float32)

        section_mask[section_mask == 0] = 0
        section_mask[geo_values < 0] = 0
        section_mask[section_mask >= 1] = 1

        section_drained_area_cmp = np.sum(area_cell_values * section_mask)

        if drainage_area_units == 'Km^2':
            section_drained_area_cmp = np.float32(section_drained_area_cmp / 1000000)
            section_drained_area_cmp = float(str(round(section_drained_area_cmp, drainage_area_rounding)))
        elif drainage_area_units == 'm^2':
            pass
        else:
            logging.error(' ===> Drainage area units are not allowed')
            raise IOError('Drainage area units are wrongly defined. Check your settings.')

        section_dframe.loc[
            (section_dframe['section_name'] == section_name) & (section_dframe['section_domain'] == section_domain),
            drainage_area_tag] = section_drained_area_cmp

    return section_dframe

# --------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to order section area (according with domain and area values)
def order_section_area(section_df,
                       drainage_order_tag='section_domain_order',
                       drainage_area_tag='section_drainage_area_cmp',
                       order_format='{:03d}', order_reverse=False):

    section_dict = {}
    for section_id, section_fields in section_df.iterrows():
        section_area = section_fields[drainage_area_tag]

        section_name = section_fields['section_name']
        section_domain = section_fields['section_domain']

        if section_domain not in list(section_dict.keys()):
            section_dict[section_domain] = {}
        section_dict[section_domain][section_name] = section_area

    section_df[drainage_order_tag] = ['NA'] * section_df.shape[0]
    for section_domain, section_area_unsorted in section_dict.items():
        section_area_sorted = dict(sorted(section_area_unsorted.items(), key=lambda item: item[1],
                                          reverse=order_reverse))

        for section_id_int, (section_name, section_area) in enumerate(section_area_sorted.items()):
            section_id_str = order_format.format(section_id_int + 1)
            section_df.loc[(section_df['section_name'] == section_name) &
                           (section_df['section_domain'] == section_domain), drainage_order_tag] = section_id_str

    return section_df
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_2d(data, geo_x, geo_y, geo_1d=True, time=None,
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

    return data_da
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute cell area in m^2
def compute_cell_area(geo_x, geo_y, cell_size_x, cell_size_y):

    # Method constant(s)
    r = 6378388  # (Radius)
    e = 0.00672267  # (Ellipsoid)

    # dx = (R * cos(lat)) / (sqrt(1 - e2 * sqr(sin(lat)))) * PI / 180
    dx_2d = (r * np.cos(np.abs(geo_y) * np.pi / 180)) / \
            (np.sqrt(1 - e * np.sqrt(np.sin(np.abs(geo_y) * np.pi / 180)))) * np.pi / 180
    # dy = (R * (1 - e2)) / pow((1 - e2 * sqr(sin(lat))),1.5) * PI / 180
    dy_2d = (r * (1 - e)) / np.power((1 - e * np.sqrt(np.sin(np.abs(geo_y) / 180))), 1.5) * np.pi / 180

    # area cell in m^2
    area_cell = ((dx_2d / (1 / cell_size_x)) * (dy_2d / (1 / cell_size_y)))  # [m^2]

    return area_cell

# -------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to convert decimal degrees to km
def deg_2_km(deg):
    earth_radius = 6378.1370
    km = deg * (np.pi * earth_radius) / 180
    return km
# --------------------------------------------------------------------------------
