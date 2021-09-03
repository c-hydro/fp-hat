"""
Library Features:

Name:          lib_graph_map_base
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210903'
Version:       '1.0.0'
"""
#######################################################################################

# Libraries
import logging
import os
import cartopy
import numpy as np

from copy import deepcopy

from lib_utils_system import make_folder
from lib_info_args import logger_name

from lib_graph_map_colormap import load

import matplotlib.pylab as plt
import matplotlib.colors as colors
import cartopy.io.img_tiles as cimgt

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable

# Logging
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger('rasterio').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to plot map variable in png format
def plot_map_var(file_path, var_darray, var_time, var_limit_min=None, var_limit_max=None,
                 var_name_data='air_temperature', var_units='C', var_description=None,
                 var_temporal_window='NA',
                 var_name_geo_x='longitude', var_name_geo_y='latitude',
                 tag_sep=' ', fig_background='stamen', fig_color_map_type=None, fig_dpi=150, fig_show=True):
    
    file_folder, file_name = os.path.split(file_path)
    if not os.path.exists(file_folder):
        make_folder(file_folder)
        
    # Axis labels
    if not var_units.startswith('['):
        var_units = '[' + var_units
    if not var_units.endswith(']'):
        var_units = var_units + ']'
    var_label = tag_sep.join([var_name_data, var_units])

    if fig_color_map_type is None:
        fig_color_map_type = 'RdYlBu'

    if isinstance(fig_color_map_type, colors.LinearSegmentedColormap):
        fig_color_map_obj = deepcopy(fig_color_map_type)
    elif isinstance(fig_color_map_type, str):
        fig_color_map_obj = load(fig_color_map_type)
    else:
        raise NotImplementedError('Variable colormap case not implemented yet')

    if hasattr(fig_color_map_obj, 'vmin'):
        fig_color_vmin = float(getattr(fig_color_map_obj, 'vmin'))
    else:
        fig_color_vmin = var_limit_min
    if hasattr(fig_color_map_obj, 'vmax'):
        fig_color_vmax = float(getattr(fig_color_map_obj, 'vmax'))
    else:
        fig_color_vmax = var_limit_max
    if hasattr(fig_color_map_obj, 'ticklabel'):
        fig_color_tick_label = getattr(fig_color_map_obj, 'ticklabel')
    else:
        fig_color_tick_label = None
    if hasattr(fig_color_map_obj, 'tickloc'):
        fig_color_tick_loc = getattr(fig_color_map_obj, 'tickloc')
    else:
        fig_color_tick_loc = None

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
        raise NotImplementedError('Variable geographical dimensions case not implemented yet')

    map_lon_west = np.min(map_lons_2d)
    map_lon_east = np.max(map_lons_2d)
    map_lat_south = np.min(map_lats_2d)
    map_lat_north = np.max(map_lats_2d)

    plot_crs = cartopy.crs.Mercator()
    data_crs = cartopy.crs.PlateCarree()

    # Define graph title
    figure_title = 'Map Data \n Description: ' + var_description + \
                   ' \n Variable: ' + var_name_data + ' == Period: ' + var_temporal_window + \
                   ' == Units: ' + var_units + ' \n Time: ' + str(var_time)

    # Create a background map
    if fig_background == 'stamen':
        map_background = cimgt.Stamen('terrain-background')
    elif fig_background == 'osm':
        map_background = cimgt.OSM()
    elif fig_background == 'google':
        map_background = cimgt.GoogleTiles()
    else:
        raise NotImplementedError('Variable background case not implemented yet')

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

    if (fig_color_vmin is not None) and (fig_color_vmax is not None):
        sc = ax.pcolormesh(map_lons_2d, map_lats_2d, map_data, zorder=3,
                           cmap=fig_color_map_obj, transform=data_crs, vmin=fig_color_vmin, vmax=fig_color_vmax)
    elif (fig_color_vmin is not None) and (fig_color_vmax is None):
        sc = ax.pcolormesh(map_lons_2d, map_lats_2d, map_data, zorder=3,
                           cmap=fig_color_map_obj, transform=data_crs, vmin=fig_color_vmin)
    elif (fig_color_vmin is None) and (fig_color_vmax is None):
        sc = ax.pcolormesh(map_lons_2d, map_lats_2d, map_data, zorder=3,
                           cmap=fig_color_map_obj, transform=data_crs)
    else:
        raise NotImplementedError('Variable limits case not implemented yet')

    divider = make_axes_locatable(ax)
    ax_cb = divider.new_horizontal(size="5%", pad=0.1, axes_class=plt.Axes)
    fig.add_axes(ax_cb)
    cb1 = plt.colorbar(sc, cax=ax_cb, extend='both')
    cb1.set_label(var_label, size=12, color='gray', weight='normal')
    cb1.ax.tick_params(labelsize=10, labelcolor='gray')

    if fig_color_tick_loc and fig_color_tick_label:
        cb1.set_ticks(fig_color_tick_loc)
        cb1.ax.set_xticklabels(fig_color_tick_label)

    #plt.show()
    fig.savefig(file_path, dpi=fig_dpi)

    if not fig_show:
        plt.close()

# -------------------------------------------------------------------------------------
