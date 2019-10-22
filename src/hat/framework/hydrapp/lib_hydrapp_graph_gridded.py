"""
Library Features:

Name:          lib_hydrapp_graph_ts
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190226'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import cartopy
import warnings
import os
import numpy as np

import matplotlib.pylab as plt
import matplotlib.ticker as mticker
import cartopy.io.img_tiles as cimgt

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable

from src.hat.dataset.colormap.lib_cmap import load
from src.hat.framework.hydrapp.lib_hydrapp_graph_configuration import configGraphData_Gridded
from src.hat.framework.hydrapp.lib_hydrapp_io_method import writeFileGraph_JSON

from src.common.utils.lib_utils_op_system import createFolderByFile

from src.common.default.lib_default_args import sLoggerName, sTimeFormat
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to plot gridded data
def plotGridded_Var2D(sFileName, oTimeRun, oVarData, sTypeRun='', iFigDPI=120, sColorMap=None):

    # -------------------------------------------------------------------------------------
    # Check function
    try:
        # -------------------------------------------------------------------------------------
        # Get data values and metadata
        sVarName, a2dVarData_VAL, a2dVarData_LONS, a2dVarData_LATS, oVarData_META = configGraphData_Gridded(oVarData)

        # Get time information
        sTimeRun = oTimeRun.strftime(sTimeFormat)
        sTimeData = oVarData_META['time_dataset']

        # Define graph title
        sGraphTitle = ' == ' + \
                      oVarData_META['var_appearance'].title() + ' Map == \n == Variable: ' + \
                      sVarName + ' == \n == Time_Run: ' + sTimeRun + ' Time_Data: ' + sTimeData + ' == '
        # Define geographical box
        dVarData_LON_MIN = np.min(a2dVarData_LONS)
        dVarData_LON_MAX = np.max(a2dVarData_LONS)
        dVarData_LAT_MIN = np.min(a2dVarData_LATS)
        dVarData_LAT_MAX = np.max(a2dVarData_LATS)

        dVarData_VAL_MIN = None
        dVarData_VAL_MAX = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if "Valid_min" in oVarData_META:
                dVarData_VAL_MIN = np.float(oVarData_META["Valid_min"])
                a2dVarData_VAL[a2dVarData_VAL < dVarData_VAL_MIN] = np.nan
            if "Valid_max" in oVarData_META:
                dVarData_VAL_MAX = np.float(oVarData_META["Valid_max"])
                a2dVarData_VAL[a2dVarData_VAL > dVarData_VAL_MAX] = np.nan
            if "Valid_range" in oVarData_META:
                oVarData_VAL_RANGE = oVarData_META["Valid_range"]
                dVarData_VAL_MIN = np.float(oVarData_VAL_RANGE[0])
                dVarData_VAL_MAX = np.float(oVarData_VAL_RANGE[1])
                a2dVarData_VAL[(a2dVarData_VAL < dVarData_VAL_MIN) | (a2dVarData_VAL > dVarData_VAL_MAX)] = np.nan

        # Define colormap
        if sColorMap is None:
            sColorMap = 'Blues'
        oFigCMAP = load(sColorMap)

        if hasattr(oFigCMAP, 'vmin'):
            oFiG_VAL_MIN = float(getattr(oFigCMAP, 'vmin'))
        else:
            oFiG_VAL_MIN = dVarData_VAL_MIN
        if hasattr(oFigCMAP, 'vmax'):
            oFiG_VAL_MAX = float(getattr(oFigCMAP, 'vmax'))
        else:
            oFiG_VAL_MAX = dVarData_VAL_MAX
        if hasattr(oFigCMAP, 'ticklabel'):
            oFiG_TickLabel = getattr(oFigCMAP, 'ticklabel')
        else:
            oFiG_TickLabel = None
        if hasattr(oFigCMAP, 'tickloc'):
            oFiG_TickLoc = getattr(oFigCMAP, 'tickloc')
        else:
            oFiG_TickLoc = None
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Plot gridded data
        plot_crs = cartopy.crs.Mercator()
        data_crs = cartopy.crs.PlateCarree()

        # Create a Stamen Terrain instance.
        # stamen_terrain = cimgt.StamenTerrain()
        stamen_terrain = cimgt.Stamen('terrain-background')

        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection=plot_crs)
        ax.set_title(sGraphTitle, size=12, color='black', weight='bold')
        # ax.coastlines(resolution='10m', color='black')
        ax.stock_img()
        ax.set_extent([dVarData_LON_MIN, dVarData_LON_MAX, dVarData_LAT_MIN, dVarData_LAT_MAX])

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
        ax.add_image(stamen_terrain, 8)

        sc = ax.pcolormesh(a2dVarData_LONS, a2dVarData_LATS, a2dVarData_VAL, zorder=3,
                           cmap=oFigCMAP, vmin=oFiG_VAL_MIN, vmax=oFiG_VAL_MAX, transform=data_crs)

        divider = make_axes_locatable(ax)
        ax_cb = divider.new_horizontal(size="5%", pad=0.1, axes_class=plt.Axes)
        fig.add_axes(ax_cb)
        # fig.add_axes([0.1, 0.05, 0.8, 0.02])
        cb1 = plt.colorbar(sc, cax=ax_cb, extend='both')
        cb1.set_label(oVarData_META['var_appearance'] + ' [' + oVarData_META['units'] + ']',
                      size=12, color='gray', weight='normal')
        cb1.ax.tick_params(labelsize=10, labelcolor='gray')

        if oFiG_TickLoc and oFiG_TickLabel:
            cb1.set_ticks(oFiG_TickLoc)
            cb1.ax.set_xticklabels(oFiG_TickLabel)

        # plt.show()
        if not os.path.exists(sFileName):
            createFolderByFile(sFileName)
        fig.savefig(sFileName, dpi=iFigDPI)

        plt.close()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Write ancillary file in json format (to configure png attributes)
        if os.path.exists(sFileName):
            sFileRoot = os.path.splitext(sFileName)[0]
            writeFileGraph_JSON(sFileRoot + '.json', oVarData_META)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Exit with success
        oGraphStatus = True
        # -------------------------------------------------------------------------------------

    except BaseException:

        # -------------------------------------------------------------------------------------
        # Exit with warning
        Exc.getExc(' =====> WARNING: graph ' + sTypeRun + ' in ' + sFileName +
                   ' failed! Error(s) occurred in plot generation! ', 2, 1)
        oGraphStatus = False
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return code
    return oGraphStatus
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
