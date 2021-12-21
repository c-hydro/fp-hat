"""
Library Features:

Name:          lib_graph_ts_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""
#######################################################################################
# Libraries
import logging
import os
import math
import json
import pandas as pd
import numpy as np

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to read ts table
def read_ts_table(file_name):
    if os.path.exists(file_name):
        with open(file_name) as file_handle:
            file_table = json.load(file_handle)
    else:
        log_stream.error(' ===> Fx table "' + file_name + '" does not exist.')
        raise IOError('Fx table is not available in the selected location')
    return file_table
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute ensemble avg
def compute_ts_ensemble_avg(dframe_variable, variable_axis=1):
    dframe_variable_tmp = dframe_variable.mean(axis=variable_axis)

    variable_values_tmp = dframe_variable_tmp.values
    variable_index_tmp = dframe_variable_tmp.index

    if variable_values_tmp.shape.__len__() == 1:
        variable_values_avg = np.reshape(variable_values_tmp, [variable_values_tmp.shape[0], 1])
        variable_index_avg = variable_index_tmp
    else:
        log_stream.error(' ===> TimeSeries average ensembles is not 1D format')
        raise NotImplementedError('Case not implemented yet')

    dframe_variable_avg = pd.DataFrame(index=variable_index_avg, data=variable_values_avg)

    return dframe_variable_avg
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute variable peaks
def compute_ts_peaks(dframe_variable, peak_value_min=0, peak_timestr_min=None):

    dframe_cols = list(dframe_variable.columns)

    dframe_peaks = pd.DataFrame(index=dframe_cols, columns=['peak', 'time'])
    for col_name in dframe_cols:
        series_variable = dframe_variable[col_name]

        if peak_timestr_min is not None:
            if isinstance(peak_timestr_min, str):
                peak_timestamp_min = pd.Timestamp(peak_timestr_min)
                series_variable.loc[series_variable.index < peak_timestamp_min] = np.nan
            else:
                log_stream.error(' ===> TimePeak reference format is not allowed')
                raise NotImplementedError('Case not implemented yet')

        peak_value = series_variable.max(axis=0)
        peak_idx_time = series_variable.idxmax(axis=0)

        if peak_value > peak_value_min:
            dframe_peaks.loc[col_name, 'peak'] = peak_value
        dframe_peaks.loc[col_name, 'time'] = peak_idx_time

    return dframe_peaks

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute variable(s) quantile(s)
def compute_ts_quantile(dframe_variable_ensemble,
                        variable_qtls_name='qtls', variable_qtls_list=None, variable_qtls_axis=1):

    if variable_qtls_list is None:
        variable_qtls_list = [0, 0.25, 0.5, 0.75, 1]

    dframe_variable_qtls = dframe_variable_ensemble.quantile(variable_qtls_list, axis=variable_qtls_axis)

    for variable_id, variable_qtls in enumerate(dframe_variable_qtls.index):
        dframe_variable_ensemble[variable_qtls_name + str(variable_qtls)] = dframe_variable_qtls.values[variable_id]

    return dframe_variable_ensemble

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to configure time-series axes
def configure_ts_axes(dframe_data, time_format='%m-%d %H'):

    tick_time_period = list(dframe_data.index)
    tick_time_idx = dframe_data.index
    tick_time_labels = [tick_label.strftime(time_format) for tick_label in dframe_data.index]

    return tick_time_period, tick_time_idx, tick_time_labels
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get discharge axis limits
def set_ax_limits_discharge(min_value_dyn=0, max_value_dyn=100, min_value_default=0, max_value_default=100,
                            min_add_percentage=0, max_add_percentage=10, max_add_difference=30):

    def cmp_percentage_part(part, whole):
        return float(whole)/100 * float(part)

    def round_value(perc_value, perc_ceil_round=10):
        return float(int(math.ceil(perc_value / perc_ceil_round)) * perc_ceil_round)

    if min_value_dyn is not None:
        if min_value_dyn > min_value_default:
            min_value_add = cmp_percentage_part(min_add_percentage, min_value_dyn)
            min_value_ax = min_value_dyn + min_value_add
        else:
            min_value_ax = min_value_default
    else:
        min_value_ax = min_value_default

    if max_value_dyn is not None:
        if max_value_dyn > max_value_default:

            max_value_dyn = round_value(max_value_dyn)
            max_value_add = cmp_percentage_part(max_add_percentage, max_value_dyn)
            max_value_add = round_value(max_value_add)

            if max_value_add > max_add_difference:
                max_value_add = max_add_difference

            max_value_ax = max_value_dyn + max_value_add
        else:
            max_value_ax = max_value_default
    else:
        max_value_ax = max_value_default

    return min_value_ax, max_value_ax
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get time-series attributes
def get_ts_attrs(attrs_ts,
                 tag_section_name='section_name', tag_basin_name='section_domain',
                 tag_section_thr_alarm_discharge='section_discharge_thr_alarm',
                 tag_section_thr_alert_discharge='section_discharge_thr_alert',
                 tag_section_drainage_area='section_drained_area'):

    if tag_section_name in list(attrs_ts.keys()):
        section_name = attrs_ts[tag_section_name]
    else:
        section_name = 'NA'
    if tag_basin_name in list(attrs_ts.keys()):
        section_domain = attrs_ts[tag_basin_name]
    else:
        section_domain = 'NA'

    if tag_section_thr_alert_discharge in list(attrs_ts.keys()):
        section_discharge_thr_alert = attrs_ts[tag_section_thr_alert_discharge]
    else:
        section_discharge_thr_alert = -9999.0
    if tag_section_thr_alarm_discharge in list(attrs_ts.keys()):
        section_discharge_thr_alarm = attrs_ts[tag_section_thr_alarm_discharge]
    else:
        section_discharge_thr_alarm = -9999.0

    if tag_section_drainage_area in list(attrs_ts.keys()):
        section_drained_area = attrs_ts[tag_section_drainage_area]
    else:
        section_drained_area = -9999.0

    return section_name, section_domain, section_discharge_thr_alert, section_discharge_thr_alarm, section_drained_area
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to configure time-series attributes
def configure_ts_attrs(attrs_data,
                       tag_run_time='time_run', tag_restart_time='time_restart', tag_start_time='time_start',
                       tag_run_name='run_name', tag_run_domain='run_domain',
                       tag_section_name='section_name', tag_basin_name='section_domain',
                       tag_section_thr_alarm_discharge='section_discharge_thr_alarm',
                       tag_section_thr_alert_discharge='section_discharge_thr_alert',
                       tag_section_drainage_area='section_drained_area'):

    if attrs_data is not None:
        attrs_ts = {}
        for attr_key, attr_value in attrs_data.items():

            if attr_key == tag_run_time:
                attrs_ts[tag_run_time] = pd.Timestamp(attr_value)
            if attr_key == tag_restart_time:
                attrs_ts[tag_restart_time] = pd.Timestamp(attr_value)
            if attr_key == tag_start_time:
                attrs_ts[tag_start_time] = pd.Timestamp(attr_value)
            elif attr_key == tag_run_name:
                attrs_ts[tag_run_name] = attr_value
            elif attr_key == tag_section_name:
                attrs_ts[tag_section_name] = attr_value
            elif attr_key == tag_basin_name:
                attrs_ts[tag_basin_name] = attr_value
            elif attr_key == tag_section_thr_alarm_discharge:
                if isinstance(attr_value, str):
                    attrs_ts[tag_section_thr_alarm_discharge] = float(attr_value)
                else:
                    attrs_ts[tag_section_thr_alarm_discharge] = attr_value
            elif attr_key == tag_section_thr_alert_discharge:
                if isinstance(attr_value, str):
                    attrs_ts[tag_section_thr_alert_discharge] = float(attr_value)
                else:
                    attrs_ts[tag_section_thr_alert_discharge] = attr_value
            elif attr_key == tag_section_drainage_area:
                if isinstance(attr_value, str):
                    attrs_ts[tag_section_drainage_area] = float(attr_value)
                else:
                    attrs_ts[tag_section_drainage_area] = attr_value
            elif attr_key == tag_run_domain:
                attrs_ts[tag_run_domain] = attr_value

    else:
        attrs_ts = None

    return attrs_ts
# -------------------------------------------------------------------------------------
