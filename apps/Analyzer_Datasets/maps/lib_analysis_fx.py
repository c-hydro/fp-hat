"""
Class Features

Name:          lib_analysis_fx
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210819'
Version:       '1.0.0'
"""

#######################################################################################
# Libraries
import logging
import re
import numpy as np
import pandas as pd
import xarray as xr

from copy import deepcopy

from lib_info_args import logger_name, time_format_algorithm

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to verify temporal window settings
def verify_temporal_window(time_reference, time_period, time_step=1):

    if not isinstance(time_period, pd.DatetimeIndex):
        time_period = pd.DatetimeIndex(time_period)

    if time_reference in time_period:
        idx_start = time_period.get_loc(time_reference)
    else:
        idx_start = None

    idx_end = None
    if idx_start is not None:
        idx_end = idx_start + time_step - 1

    flag_temporal_window = False
    if (idx_start is not None) and (idx_end is not None):
        if time_period.shape[0] > idx_end:
            flag_temporal_window = True

    if not flag_temporal_window:
        log_stream.warning(' ===> Temporal window do not include all the needed step for computing variable')
        log_stream.warning(' ===> Due to this issue of the time period, the variable will be not plotted.')

    return flag_temporal_window

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to split temporal window
def split_temporal_window(temporal_window):

    temporal_period = re.findall(r'\d+', temporal_window)
    if temporal_period.__len__() > 0:
        temporal_period = int(temporal_period[0])
    else:
        temporal_period = 1
    temporal_frequency = re.findall("[a-zA-Z]+", temporal_window)[0]

    return temporal_period, temporal_frequency
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to select data array using the reference time
def select_temporal_darray(time_reference, var_darray, var_time_period):

    if not isinstance(var_time_period, pd.DatetimeIndex):
        var_time_period = pd.DatetimeIndex(var_time_period)

    if time_reference in var_time_period:
        idx_start = var_time_period.get_loc(time_reference)
    else:
        idx_start = None

    if idx_start is not None:
        if var_darray.ndim == 3:
            var_darray_selected = deepcopy(var_darray[:, :, idx_start:])
        elif var_darray.ndim == 2:
            log_stream.warning(' ===> Select DataArray is 2D. Normally a 3D data array is expects. '
                               'Script will be used only one step to perform all computations.')
            var_darray_selected = deepcopy(var_darray)
        else:
            log_stream.error(' ===> Select DataArray must be 3D (in some case 2D case is accepted.')
            raise RuntimeError('Data array format is not accepted by the script')
    else:
        var_darray_selected = None
        log_stream.warning(' ===> Select DataArray in using the reference time failed. Time is not in the DataArray')

    return var_darray_selected

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute accumulated variable
def var_cmp_accumulated(var_time, var_darray_src, var_darray_terrain,
                        var_temporal_window=None, var_temporal_direction=None,
                        var_coord_time='time'):

    if var_temporal_window is None:
        var_temporal_window = ['3H']

    if var_temporal_direction is None:
        var_temporal_direction = 'right'

    var_collection_cmp = {}
    for var_t_win in var_temporal_window:

        var_t_period, var_t_frequency = split_temporal_window(var_t_win)

        if var_temporal_direction == 'left':

            var_darray_sorted = var_darray_src.sortby(var_coord_time, ascending=False)

            # var_time_end = pd.Timestamp(var_darray_sorted[var_coord_time].values[0]).strftime(time_format_algorithm)
            # var_time_range = pd.date_range(end=var_time_end, periods=var_t_period, freq=var_t_frequency)
            # var_time_start = var_time_range[0].strftime(time_format_algorithm)

            var_time_flag = verify_temporal_window(var_time, var_darray_sorted[var_coord_time].values, var_t_period)

            var_darray_selected = select_temporal_darray(var_time, var_darray_sorted,
                                                         var_darray_sorted[var_coord_time].values)

            var_time_end = pd.Timestamp(var_darray_selected[var_coord_time].values[0]).strftime(time_format_algorithm)
            var_time_range = pd.date_range(end=var_time_end, periods=var_t_period, freq=var_t_frequency)
            var_time_start = var_time_range[0].strftime(time_format_algorithm)

            if var_time_flag and (var_darray_selected is not None):
                var_darray_tmp = var_darray_sorted.sel(time=slice(var_time_end, var_time_start))
            else:
                var_darray_tmp = None

        elif var_temporal_direction == 'right':

            var_darray_sorted = var_darray_src.sortby(var_coord_time, ascending=True)

            # var_time_start = pd.Timestamp(var_darray_sorted[var_coord_time].values[0]).strftime(time_format_algorithm)
            # var_time_end = pd.date_range(
            #    start=var_time_start, periods=var_t_period, freq=var_t_frequency)[-1].strftime(time_format_algorithm)#

            var_time_flag = verify_temporal_window(var_time, var_darray_sorted[var_coord_time].values, var_t_period)

            var_darray_selected = select_temporal_darray(var_time, var_darray_sorted,
                                                         var_darray_sorted[var_coord_time].values)

            var_time_start = pd.Timestamp(var_darray_selected[var_coord_time].values[0]).strftime(time_format_algorithm)
            var_time_end = pd.date_range(start=var_time_start, periods=var_t_period,
                                         freq=var_t_frequency)[-1].strftime(time_format_algorithm)

            if var_time_flag and (var_darray_selected is not None):
                var_darray_tmp = var_darray_sorted.sel(time=slice(var_time_start, var_time_end))
            else:
                var_darray_tmp = None

        else:
            log_stream.error(' ===> Temporal direction "' + var_temporal_direction + '" flag is not allowed')
            raise IOError('Available flags for temporal direction are: right, left and center')

        if var_darray_tmp is not None:
            var_darray_accumulated = var_darray_tmp.sum('time')
            var_darray_masked = var_darray_accumulated.where(np.isfinite(var_darray_terrain.values), np.nan)
        else:
            var_darray_masked = None

        if var_darray_masked is not None:
            if isinstance(var_darray_masked, xr.DataArray):

                var_attrs_masked = var_darray_masked.attrs

                var_attrs_time = {'time_from': pd.Timestamp(var_time_start), 'time_to': pd.Timestamp(var_time_end),
                                  'time_window': var_t_win, 'time_direction': var_temporal_direction}
                var_attrs_tmp = {**var_attrs_masked, **var_attrs_time}

                var_darray_masked.attrs = var_attrs_tmp

            else:
                log_stream.error(' ===> Analysis object must be in DataArray format.')
                raise RuntimeError('Check the procedure to analyze the datasets.')

        var_collection_cmp[var_t_win] = var_darray_masked

        '''
        # Debug
        import matplotlib.pylab as plt
        plt.figure()
        plt.imshow(var_darray_masked.values)
        plt.colorbar()

        plt.figure()
        plt.imshow(var_darray_terrain)
        plt.colorbar()
        plt.show()
        
        import matplotlib.pylab as plt
        plt.figure()
        plt.imshow(var_darray_masked.values)
        plt.colorbar()
        plt.clim(0, 100)
        plt.show()
        '''

    return var_collection_cmp
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute averaged variable
def var_cmp_average(var_time, var_darray_src, var_darray_terrain,
                    var_temporal_window=None, var_temporal_direction=None,
                    var_coord_time='time'):

    if var_temporal_window is None:
        var_temporal_window = ['3H']

    if var_temporal_direction is None:
        var_temporal_direction = 'right'

    var_collection_cmp = {}
    for var_t_win in var_temporal_window:

        var_t_period, var_t_frequency = split_temporal_window(var_t_win)

        if var_temporal_direction == 'left':

            var_darray_sorted = var_darray_src.sortby(var_coord_time, ascending=False)

            # var_time_end = pd.Timestamp(var_darray_sorted[var_coord_time].values[0]).strftime(time_format_algorithm)
            # var_time_range = pd.date_range(end=var_time_end, periods=var_t_period, freq=var_t_frequency)
            # var_time_start = var_time_range[0].strftime(time_format_algorithm)

            var_time_flag = verify_temporal_window(var_time, var_darray_sorted[var_coord_time].values, var_t_period)

            var_darray_selected = select_temporal_darray(var_time, var_darray_sorted,
                                                         var_darray_sorted[var_coord_time].values)

            var_time_end = pd.Timestamp(var_darray_selected[var_coord_time].values[0]).strftime(time_format_algorithm)
            var_time_range = pd.date_range(end=var_time_end, periods=var_t_period, freq=var_t_frequency)
            var_time_start = var_time_range[0].strftime(time_format_algorithm)

            if var_time_flag and (var_darray_selected is not None):
                var_darray_tmp = var_darray_sorted.sel(time=slice(var_time_end, var_time_start))
            else:
                var_darray_tmp = None

        elif var_temporal_direction == 'right':

            var_darray_sorted = var_darray_src.sortby(var_coord_time, ascending=True)

            # var_time_start = pd.Timestamp(var_darray_sorted[var_coord_time].values[0]).strftime(time_format_algorithm)
            # var_time_end = pd.date_range(start=var_time_start, periods=var_t_period,
            # freq=var_t_frequency)[-1].strftime(time_format_algorithm)

            var_time_flag = verify_temporal_window(var_time, var_darray_sorted[var_coord_time].values, var_t_period)

            var_darray_selected = select_temporal_darray(var_time, var_darray_sorted,
                                                         var_darray_sorted[var_coord_time].values)

            var_time_start = pd.Timestamp(var_darray_selected[var_coord_time].values[0]).strftime(time_format_algorithm)
            var_time_end = pd.date_range(start=var_time_start, periods=var_t_period,
                                         freq=var_t_frequency)[-1].strftime(time_format_algorithm)

            if var_time_flag and (var_darray_selected is not None):
                var_darray_tmp = var_darray_sorted.sel(time=slice(var_time_start, var_time_end))
            else:
                var_darray_tmp = None
        else:
            log_stream.error(' ===> Temporal direction "' + var_temporal_direction + '" flag is not allowed')
            raise IOError('Available flags for temporal direction are: right and left')

        if var_darray_tmp is not None:
            var_darray_average = var_darray_tmp.mean('time')
            var_darray_masked = var_darray_average.where(np.isfinite(var_darray_terrain.values), np.nan)
        else:
            var_darray_masked = None

        if var_darray_masked is not None:
            if isinstance(var_darray_masked, xr.DataArray):

                var_attrs_masked = var_darray_masked.attrs

                var_attrs_time = {'time_from': pd.Timestamp(var_time_start), 'time_to': pd.Timestamp(var_time_end),
                                  'time_window': var_t_win, 'time_direction': var_temporal_direction}
                var_attrs_tmp = {**var_attrs_masked, **var_attrs_time}

                var_darray_masked.attrs = var_attrs_tmp

            else:
                log_stream.error(' ===> Analysis object must be in DataArray format.')
                raise RuntimeError('Check the procedure to analyze the datasets.')

        var_collection_cmp[var_t_win] = var_darray_masked

        '''
        # Debug
        plt.figure()
        plt.imshow(var_darray_masked.values)
        plt.colorbar()

        plt.figure()
        plt.imshow(var_darray_terrain)
        plt.colorbar()
        plt.show()
        '''

    return var_collection_cmp
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute instantaneous variable
def var_cmp_instantaneous(var_time, var_darray_src, var_darray_terrain,
                          var_temporal_window=None, var_temporal_direction=None,
                          var_coord_time='time'):

    if var_temporal_window is None:
        var_temporal_window = ['last']

    if var_temporal_direction is None:
        var_temporal_direction = 'left'

    var_collection_cmp = {}
    for var_t_win in var_temporal_window:

        if var_temporal_direction == 'left':

            var_darray_sorted = var_darray_src.sortby(var_coord_time, ascending=False)

            var_time_end = pd.Timestamp(var_darray_sorted[var_coord_time].values[0]).strftime(time_format_algorithm)
            var_time_start = pd.Timestamp(var_darray_sorted[var_coord_time].values[-1]).strftime(time_format_algorithm)
            # var_time_period = var_darray_sorted[var_coord_time].values.shape[0]
            # var_time_range = pd.date_range(end=var_time_end, start=var_time_start, periods=var_time_period)

            if var_t_win == 'first':
                var_darray_tmp = var_darray_sorted.sel(time=slice(var_time_start, var_time_start))
            elif var_t_win == 'last':
                var_darray_tmp = var_darray_sorted.sel(time=slice(var_time_end, var_time_end))
            else:
                log_stream.error(' ===> Temporal window"' + var_t_win + '" flag is not allowed')
                raise IOError('Available flags for temporal window are: first and last')

        elif var_temporal_direction == 'right':

            var_darray_sorted = var_darray_src.sortby(var_coord_time, ascending=True)

            var_time_start = pd.Timestamp(var_darray_sorted[var_coord_time].values[0]).strftime(time_format_algorithm)
            var_time_end = pd.Timestamp(var_darray_sorted[var_coord_time].values[-1]).strftime(time_format_algorithm)
            # var_time_period = var_darray_sorted[var_coord_time].values.shape[0]
            # var_time_range = pd.date_range(end=var_time_end, start=var_time_start, periods=var_time_period)

            if var_t_win == 'first':
                var_darray_tmp = var_darray_sorted.sel(time=slice(var_time_start, var_time_start))
            elif var_t_win == 'last':
                var_darray_tmp = var_darray_sorted.sel(time=slice(var_time_end, var_time_end))
            else:
                log_stream.error(' ===> Temporal window"' + var_t_win + '" flag is not allowed')
                raise IOError('Available flags for temporal window are: first and last')
        else:
            log_stream.error(' ===> Temporal direction "' + var_temporal_direction + '" flag is not allowed')
            raise IOError('Available flags for temporal direction are: right and left')

        if var_darray_tmp is not None:
            var_darray_instantaneous = var_darray_tmp.mean('time')
            var_darray_masked = var_darray_instantaneous.where(np.isfinite(var_darray_terrain.values), np.nan)
        else:
            var_darray_masked = None

        if var_darray_masked is not None:
            if isinstance(var_darray_masked, xr.DataArray):

                var_attrs_masked = var_darray_masked.attrs

                var_attrs_time = {'time_from': pd.Timestamp(var_time_start), 'time_to': pd.Timestamp(var_time_end),
                                  'time_window': var_t_win, 'time_direction': var_temporal_direction}
                var_attrs_tmp = {**var_attrs_masked, **var_attrs_time}

                var_darray_masked.attrs = var_attrs_tmp

            else:
                log_stream.error(' ===> Analysis object must be in DataArray format.')
                raise RuntimeError('Check the procedure to analyze the datasets.')

        var_collection_cmp[var_t_win] = var_darray_masked

        '''
        # Debug
        import matplotlib.pylab as plt
        plt.figure()
        plt.imshow(var_darray_masked.values)
        plt.colorbar()

        plt.figure()
        plt.imshow(var_darray_terrain)
        plt.colorbar()
        plt.show()
        '''

    return var_collection_cmp
# -------------------------------------------------------------------------------------
