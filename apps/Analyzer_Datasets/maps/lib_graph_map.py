"""
Library Features:

Name:          lib_jupyter_plot_map
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""
#######################################################################################

# Libraries
import logging
import os
import cartopy
import numpy as np

from library.jupyter_generic.lib_jupyter_utils_system import make_folder
from library.jupyter_generic.lib_jupyter_utils_colormap import load

import matplotlib.pylab as plt
import matplotlib.ticker as mticker
import cartopy.io.img_tiles as cimgt
from pyproj import Proj

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable

logging.getLogger('rasterio').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to plot map variable in png format
def plot_map_var(file_path, var_darray, var_time, var_limit_min=None, var_limit_max=None,
                 var_name_data='air_temperature', var_units='[C]',
                 var_name_geo_x='longitude', var_name_geo_y='latitude',
                 tag_sep=' ', fig_color_map_type=None, fig_dpi=150, fig_show=True):
    
    file_folder, file_name = os.path.split(file_path)
    if not os.path.exists(file_folder):
        make_folder(file_folder)
        
    # Axis labels
    var_label = tag_sep.join([var_name_data, var_units])

    if fig_color_map_type is None:
        fig_color_map_type = 'RdYlBu'
    fig_color_map_obj = load(fig_color_map_type)

    map_data = var_darray.values

    if var_limit_min is not None:
        map_data[map_data < var_limit_min] = np.nan
    if var_limit_max is not None:
        map_data[map_data > var_limit_max] = np.nan

    map_lons_tmp = np.float32(var_darray[var_name_geo_x].values)
    map_lats_tmp = np.float32(var_darray[var_name_geo_y].values)

    if (map_lons_tmp.shape.__len__() == 2) and (map_lats_tmp.shape.__len__() == 2):
        map_lons_2d = map_lons_tmp
        map_lats_2d = map_lats_tmp
    elif (map_lons_tmp.shape.__len__() == 1) and (map_lats_tmp.shape.__len__() == 1):
        map_lons_2d, map_lats_2d = np.meshgrid(map_lons_tmp, map_lats_tmp)
    else:
        raise NotImplementedError('Geographical dimensions case not implemented yet')

    map_lon_west = np.min(map_lons_2d)
    map_lon_east = np.max(map_lons_2d)
    map_lat_south = np.min(map_lats_2d)
    map_lat_north = np.max(map_lats_2d)

    plot_crs = cartopy.crs.Mercator()
    data_crs = cartopy.crs.PlateCarree()

    # Define graph title
    figure_title = 'Map Data \n Variable: ' + var_name_data + ' == Units: ' + var_units + ' == Time: ' + str(var_time)

    # Create a background map
    map_background = cimgt.Stamen('terrain-background')
    # map_background = cimgt.OSM()
    # map_background = cimgt.GoogleTiles()

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection=plot_crs)
    ax.set_title(figure_title, size=14, color='black', weight='bold')
    # ax.coastlines(resolution='10m', color='black')
    ax.stock_img()
    ax.set_extent([map_lon_west, map_lon_east, map_lat_south, map_lat_north])

    gl = ax.gridlines(crs=data_crs, draw_labels=True,
                      linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_bottom = True
    gl.xlabels_top = False
    gl.ylabels_left = True
    gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 8, 'color': 'gray', 'weight': 'bold'}
    gl.ylabel_style = {'size': 8, 'color': 'gray', 'weight': 'bold'}

    # Add the Stamen data at zoom level 8.
    ax.add_image(map_background, 8)

    sc = ax.pcolormesh(map_lons_2d, map_lats_2d, map_data, zorder=3,
                       cmap=fig_color_map_obj, transform=data_crs)
    divider = make_axes_locatable(ax)
    ax_cb = divider.new_horizontal(size="5%", pad=0.1, axes_class=plt.Axes)
    fig.add_axes(ax_cb)
    cb1 = plt.colorbar(sc, cax=ax_cb, extend='both')
    cb1.set_label(var_label, size=12, color='gray', weight='normal')
    cb1.ax.tick_params(labelsize=10, labelcolor='gray')

    #plt.show()
    fig.savefig(file_path, dpi=fig_dpi)

    if not fig_show:
        plt.close()

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to plot map terrain in png format
def plot_map_terrain(file_path, darray_data_terrain, darray_data_river_network, dict_section,
                     tag_terrain_name='terrain', tag_terrain_units='[m]',
                     tag_terrain_geo_x='west_east', tag_terrain_geo_y='south_north',
                     tag_section_name='section_name', tag_basin_name='basin_name',
                     tag_section_geo_x='longitude', tag_section_geo_y='latitude',
                     tag_section_drainage_area='section_drained_area',
                     mask_terrain=True,
                     tag_sep=' ', fig_color_map_type=None, fig_dpi=150, fig_show=True):

    # Axis labels
    label_terrain = tag_sep.join([tag_terrain_name, tag_terrain_units])
    label_section = tag_sep.join([dict_section[tag_basin_name], dict_section[tag_section_name]])

    if fig_color_map_type is None:
        fig_color_map_type = 'RdYlBu'
    fig_color_map_obj = load(fig_color_map_type)

    map_data = darray_data_terrain.values
    map_lons_1d = np.float32(darray_data_terrain[tag_terrain_geo_x].values)
    map_lats_1d = np.float32(darray_data_terrain[tag_terrain_geo_y].values)

    map_lons_2d, map_lats_2d = np.meshgrid(map_lons_1d, map_lats_1d)

    map_lon_west = np.min(map_lons_2d)
    map_lon_east = np.max(map_lons_2d)
    map_lat_south = np.min(map_lats_2d)
    map_lat_north = np.max(map_lats_2d)

    if mask_terrain:
        river_network_data = darray_data_river_network.values
        map_data[river_network_data == 1] = np.nan

    plot_crs = cartopy.crs.Mercator()
    data_crs = cartopy.crs.PlateCarree()

    # Define graph title
    figure_title = 'Map Terrain \n Section: ' + dict_section[tag_section_name] + \
                   ' == Basin: ' + dict_section[tag_basin_name] + \
                   ' == Area [Km^2]: ' + str(dict_section[tag_section_drainage_area])

    # Create a background map
    map_background = cimgt.Stamen('terrain-background')
    # map_background = cimgt.OSM()
    # map_background = cimgt.GoogleTiles()

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection=plot_crs)
    ax.set_title(figure_title, size=14, color='black', weight='bold')
    # ax.coastlines(resolution='10m', color='black')
    ax.stock_img()
    ax.set_extent([map_lon_west, map_lon_east, map_lat_south, map_lat_north])

    gl = ax.gridlines(crs=data_crs, draw_labels=True,
                      linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_bottom = True
    gl.xlabels_top = False
    gl.ylabels_left = True
    gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 8, 'color': 'gray', 'weight': 'bold'}
    gl.ylabel_style = {'size': 8, 'color': 'gray', 'weight': 'bold'}

    # Add the Stamen data at zoom level 8.
    ax.add_image(map_background, 8)

    sc = ax.pcolormesh(map_lons_2d, map_lats_2d, map_data, zorder=3,
                       cmap=fig_color_map_obj, transform=data_crs)
    divider = make_axes_locatable(ax)
    ax_cb = divider.new_horizontal(size="5%", pad=0.1, axes_class=plt.Axes)
    fig.add_axes(ax_cb)
    cb1 = plt.colorbar(sc, cax=ax_cb, extend='both')
    cb1.set_label(label_terrain, size=12, color='gray', weight='normal')
    cb1.ax.tick_params(labelsize=10, labelcolor='gray')

    ax.plot(dict_section[tag_section_geo_x], dict_section[tag_section_geo_y], 'o',
            markersize=20, markerfacecolor='white', markeredgecolor='gray', markeredgewidth=2,
            transform=data_crs)
    ax.text(dict_section[tag_section_geo_x], dict_section[tag_section_geo_y],
            label_section, transform=data_crs, bbox=dict(boxstyle='square', facecolor='white', alpha=0.5))

    #plt.show()
    
    file_folder, file_name = os.path.split(file_path)
    if not os.path.exists(file_folder):
        make_folder(file_folder)
    fig.savefig(file_path, dpi=fig_dpi)

    if not fig_show:
        plt.close()

# -------------------------------------------------------------------------------------
