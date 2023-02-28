"""
Library Features:

Name:          lib_data_analysis
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging

import numpy as np
import pandas as pd
from copy import deepcopy

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# method to select discharge columns by tag
def filter_discharge_ts_by_tag(section_dframe,
                               tag_discharge_simulated='discharge_simulated',
                               tag_discharge_observed='discharge_observed'):

    if '{:}' in tag_discharge_simulated:
        tag_root_simulated = tag_discharge_simulated.strip('{:}')
        tag_root_simulated = tag_root_simulated.strip('_')
    else:
        tag_root_simulated = deepcopy(tag_discharge_simulated)
    if '{:}' in tag_discharge_observed:
        tag_root_observed = tag_discharge_simulated.strip('{:}')
        tag_root_observed = tag_root_observed.strip('_')
    else:
        tag_root_observed = deepcopy(tag_discharge_observed)

    section_dframe_simulated = section_dframe[section_dframe.columns[
        section_dframe.columns.str.contains(tag_root_simulated, na=False, case=False)]]
    section_dframe_observed = section_dframe[section_dframe.columns[
        section_dframe.columns.str.contains(tag_root_observed, na=False, case=False)]]

    return section_dframe_simulated, section_dframe_observed

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to select discharge columns by limits
def filter_discharge_ts_by_limits(section_dframe_generic, section_attrs, discharge_min=0, discharge_max=None):

    ts_vars = section_attrs['run_var'].split(',')
    if isinstance(ts_vars, str):
        ts_n_exp = 1
    else:
        ts_n_exp = ts_vars.__len__()

    # remove nans ts
    section_dframe_tmp = section_dframe_generic.dropna(axis=1, how='all')
    # keep ts ge min
    if discharge_min is not None:
        index_finite = section_dframe_tmp.ge(discharge_min).any()
        section_dframe_tmp = section_dframe_tmp.loc[:, index_finite]
    # keep th le max
    if discharge_max is not None:
        index_finite = section_dframe_tmp.le(discharge_max).any()
        section_dframe_tmp = section_dframe_tmp.loc[:, index_finite]

    section_dframe_filtered = deepcopy(section_dframe_tmp)
    if not section_dframe_filtered.empty:
        ts_n_filter = list(section_dframe_filtered.columns).__len__()
    else:
        ts_n_filter = 0
        log_stream.warning(' ===> The filtered DataFrame by limits is empty')

    section_dframe_filtered.attrs['ts_exp'] = ts_n_exp
    section_dframe_filtered.attrs['ts_filter'] = ts_n_filter

    return section_dframe_filtered
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to analyze discharge time series
def analyze_discharge_ts(run_name, file_datasets, time_start=None, time_end=None,
                         time_format='%Y-%m-%d %H:%M', sep_format=',',
                         tag_discharge_observed='discharge_observed',
                         tag_discharge_simulated='discharge_simulated',
                         tag_discharge_thr_alert='section_discharge_thr_alert',
                         tag_discharge_thr_alarm='section_discharge_thr_alarm',
                         tag_discharge_max_alert_value='discharge_alert_max_value',
                         tag_discharge_max_alert_index='discharge_alert_max_index',
                         tag_discharge_max_alert_run='discharge_alert_max_run',
                         tag_discharge_max_alarm_value='discharge_alarm_max_value',
                         tag_discharge_max_alarm_index='discharge_alarm_max_index',
                         tag_discharge_max_alarm_run='discharge_alarm_max_run',
                         tag_section_n='section_n', tag_run_n='run_n', tag_run_expected='run_expected',
                         tag_run_type='run_type'):

    # info start routine
    log_stream.info(' ----> Analyze discharge time-series  ... ')

    # check common datasets
    if file_datasets is not None:

        # get section number
        section_n = file_datasets.__len__()
        # iterate over section(s)
        analysis_datasets_section, attrs_ts_collections = {}, None
        for section_tag, section_datasets in file_datasets.items():

            # info start section
            log_stream.info(' -----> Section "' + section_tag + '" ... ')

            # check section datasets
            if section_datasets is not None:

                # get section dframe and attr(s)
                section_dframe, section_attrs = section_datasets[0], section_datasets[1]

                # select dframe using the time start and time end
                if (time_start is not None) and (time_end is not None):
                    section_dframe_select = section_dframe.loc[
                        (section_dframe.index >= time_start) &
                        (section_dframe.index <= time_end)]
                elif (time_start is not None) and (time_end is None):
                    section_dframe_select = section_dframe.loc[
                        (section_dframe.index >= time_start)]
                elif (time_start is None) and (time_end is not None):
                    section_dframe_select = section_dframe.loc[
                        (section_dframe.index <= time_end)]
                elif (time_start is None) and (time_end is None):
                    section_dframe_select = deepcopy(section_dframe)
                else:
                    log_stream.error(' ===> The "time_start" and "time_end" case is not supported')
                    raise NotImplemented('Case not implemented yet')

                # get alert and alarm thr(s)
                data_thr_alert = float(section_attrs['section_discharge_thr_alert'])
                data_thr_alarm = float(section_attrs['section_discharge_thr_alarm'])

                # check alert and alarm thr(s)
                if data_thr_alert < 0:
                    log_stream.warning(' ===> The alert threshold is equal to "' + str(data_thr_alert) +
                                       '" is less then 0. The threshold is set to NoneType')
                    data_thr_alert = None
                if data_thr_alarm < 0:
                    log_stream.warning(' ===> The alarm threshold is equal to "' + str(data_thr_alarm) +
                                       '" is less then 0. The threshold is set to NoneType')
                    data_thr_alarm = None

                if (data_thr_alert is not None) and (data_thr_alarm is not None):
                    if data_thr_alert >= data_thr_alarm:
                        log_stream.warning(' ===> The alert threshold "' + str(data_thr_alert) +
                                           '" is equal or greater than the alarm threshold "' +
                                           str(data_thr_alarm) + '"')
                '''
                # DEBUG
                data_thr_alert, data_thr_alarm = 1, 10
                '''
                # get times and normalize to days
                section_ts_time = section_dframe_select.index
                section_ts_days = section_ts_time[1:].normalize().unique()

                # filter dframe according to the tag
                section_dframe_simulated, section_dframe_observed = filter_discharge_ts_by_tag(
                    section_dframe_select,
                    tag_discharge_simulated=tag_discharge_simulated, tag_discharge_observed=tag_discharge_observed)
                # filter dframe by limits and nans
                section_dframe_simulated = filter_discharge_ts_by_limits(section_dframe_simulated, section_attrs)

                section_thr_collections = {}
                for section_ts_step in section_ts_days:

                    # info time start
                    log_stream.info(' ------> Time "' + str(section_ts_step) + '" ... ')

                    # init the alert and alarm data selection
                    section_thr_collections[section_ts_step] = {}
                    section_thr_collections[section_ts_step][tag_discharge_max_alert_value] = {}
                    section_thr_collections[section_ts_step][tag_discharge_max_alert_index] = {}
                    section_thr_collections[section_ts_step][tag_discharge_max_alert_run] = {}
                    section_thr_collections[section_ts_step][tag_discharge_max_alarm_value] = {}
                    section_thr_collections[section_ts_step][tag_discharge_max_alarm_index] = {}
                    section_thr_collections[section_ts_step][tag_discharge_max_alarm_run] = {}

                    # select dframe by day
                    ts_day, ts_month, ts_year = section_ts_step.day, section_ts_step.month, section_ts_step.year
                    section_dframe_day = section_dframe_simulated.loc[
                                         (section_dframe_simulated.index.day == ts_day) &
                                         (section_dframe_simulated.index.month == ts_month) &
                                         (section_dframe_simulated.index.year == ts_year), :]

                    # check alert thr
                    log_stream.info(' -------> Select alert value, time and run ... ')
                    section_thr_alert_max = None
                    section_thr_alert_idxmax_list, section_thr_alert_run_list = None, None
                    # section_thr_alert_idxmax_str, section_thr_alert_run_str = None, None
                    if (data_thr_alert is not None) and (data_thr_alarm is not None):

                        # select dataframe based on threshold value(s)
                        section_dframe_thr_alert = section_dframe_day.where(
                            (section_dframe_day.values >= data_thr_alert) &
                            (section_dframe_day.values < data_thr_alarm)).dropna()

                        # check not empty dataframe
                        if not section_dframe_thr_alert.empty:

                            '''
                            # debug
                            if section_tag == 'misa:misa':
                                if 'discharge_simulated_001' in list(section_dframe_thr_alert.columns):
                                    section_dframe_thr_alert['discharge_simulated_001']['2023-02-28 02:00:00'] = 52.71
                            '''

                            section_thr_alert_max = section_dframe_thr_alert.max(skipna=True, axis=1).max()

                            log_stream.info(' --------> Threshold analysis ... ')
                            log_stream.info('      :::: Discharge value: "' + str(section_thr_alert_max) +
                                            '" Discharge Threshold: "' + str(data_thr_alert) + '"')

                            section_thr_alert_idxmax_list, section_thr_alert_run_list = [], []
                            idx_i, idx_j = np.where(section_dframe_thr_alert.values == section_thr_alert_max)
                            for step_n, (step_i, step_j) in enumerate(zip(idx_i, idx_j)):
                                section_thr_alert_idxmax = section_dframe_thr_alert.index[step_i]
                                section_thr_alert_run = section_dframe_thr_alert.columns[step_j]

                                section_thr_alert_idxmax_list.append(section_thr_alert_idxmax)
                                section_thr_alert_run_list.append(section_thr_alert_run)

                                log_stream.info('      :::: [' + str(step_n + 1) + '] Discharge Time: "'
                                                + str(section_thr_alert_idxmax) +
                                                '" Discharge Run: "' + section_thr_alert_run + '"')

                            # section_thr_alert_run_str = sep_format.join(section_thr_alert_run_list)
                            # section_thr_alert_idxmax_tmp = [elem.strftime(time_format)
                            #                                 for elem in section_thr_alert_idxmax_list]
                            # section_thr_alert_idxmax_str = sep_format.join(section_thr_alert_idxmax_tmp)

                            # info thr end
                            log_stream.info(' -------> Select alert value, time and run ... DONE')
                        else:
                            log_stream.info(' -------> Select alert value, time and run ... SKIPPED. '
                                            'All values are less than the threshold')
                    else:
                        log_stream.info(' -------> Select alert value, time and run ... SKIPPED. '
                                        'Threshold is undefined')

                    # check thr alarm
                    log_stream.info(' -------> Select alarm value, time and run ... ')
                    section_thr_alarm_max = None
                    section_thr_alarm_idxmax_list, section_thr_alarm_run_list = None, None
                    # section_thr_alarm_idxmax_str, section_thr_alarm_run_str = None, None
                    if data_thr_alarm is not None:

                        # select dataframe based on threshold value(s)
                        section_dframe_thr_alarm = section_dframe_day.where(
                            section_dframe_day.values > data_thr_alarm).dropna()

                        # check not empty dataframe
                        if not section_dframe_thr_alarm.empty:
                            section_thr_alarm_max = section_dframe_thr_alarm.max(skipna=True, axis=1).max()

                            log_stream.info(' --------> Threshold analysis ... ')
                            log_stream.info('      :::: Discharge value: "' + str(section_thr_alarm_max) +
                                            '" Discharge Threshold: "' + str(data_thr_alarm) + '"')

                            section_thr_alarm_idxmax_list, section_thr_alarm_run_list = [], []
                            idx_i, idx_j = np.where(section_dframe_thr_alarm.values == section_thr_alarm_max)
                            for step_n, (step_i, step_j) in enumerate(zip(idx_i, idx_j)):

                                section_thr_alarm_idxmax = section_dframe_thr_alarm.index[step_i]
                                section_thr_alarm_run = section_dframe_thr_alarm.columns[step_j]

                                section_thr_alarm_idxmax_list.append(section_thr_alarm_idxmax)
                                section_thr_alarm_run_list.append(section_thr_alarm_run)

                                log_stream.info('      :::: [' + str(step_n + 1) + '] Discharge Time: "'
                                                + str(section_thr_alarm_idxmax) +
                                                '" Discharge Run: "' + section_thr_alarm_run + '"')

                            # section_thr_alarm_run_str = sep_format.join(section_thr_alarm_run_list)
                            # section_thr_alarm_idxmax_tmp = [elem.strftime(time_format)
                            #                                 for elem in section_thr_alarm_idxmax_list]
                            # section_thr_alarm_idxmax_str = sep_format.join(section_thr_alarm_idxmax_tmp)

                            # info thr end
                            log_stream.info(' -------> Select alarm value, time and run ... DONE')
                        else:
                            log_stream.info(' -------> Select alarm value, time and run ... SKIPPED. '
                                            'All values are less than the threshold')
                    else:
                        log_stream.info(' -------> Select alarm value, time and run ... SKIPPED. '
                                        'Threshold is undefined')

                    # collect the alert and alarm data selection
                    section_thr_collections[section_ts_step][tag_discharge_max_alert_value] = section_thr_alert_max
                    section_thr_collections[section_ts_step][tag_discharge_max_alert_index] = section_thr_alert_idxmax_list
                    section_thr_collections[section_ts_step][tag_discharge_max_alert_run] = section_thr_alert_run_list
                    section_thr_collections[section_ts_step][tag_discharge_max_alarm_value] = section_thr_alarm_max
                    section_thr_collections[section_ts_step][tag_discharge_max_alarm_index] = section_thr_alarm_idxmax_list
                    section_thr_collections[section_ts_step][tag_discharge_max_alarm_run] = section_thr_alarm_run_list
                    section_thr_collections[section_ts_step][tag_discharge_thr_alert] = data_thr_alert
                    section_thr_collections[section_ts_step][tag_discharge_thr_alarm] = data_thr_alarm
                    section_thr_collections[section_ts_step][tag_run_type] = run_name

                    # collect the alert and alarm attributes
                    if attrs_ts_collections is None:
                        run_n_filtered = section_dframe_simulated.attrs['ts_filter']
                        run_n_expected = section_dframe_simulated.attrs['ts_exp']
                        attrs_ts_collections = {tag_run_n: run_n_filtered, tag_run_expected: run_n_expected,
                                                tag_section_n: section_n, tag_run_type: run_name}

                    # info time end
                    log_stream.info(' ------> Time "' + str(section_ts_step) + '" ... DONE')

                # merge in a common object
                analysis_datasets_section[section_tag] = section_thr_collections

                # info section end
                log_stream.info(' -----> Section "' + section_tag + '" ... DONE')

            else:
                # section datasets not available
                analysis_datasets_section[section_tag] = None
                log_stream.info(' -----> Section "' + section_tag + '" ... SKIPPED. Datasets is undefined')

        # info routine end
        log_stream.info(' ----> Analyze discharge time-series  ... DONE')

    else:
        # common datasets not available
        analysis_datasets_section, attrs_ts_collections = None, None
        # info routine end
        log_stream.info(' ----> Analyze discharge time-series  ... SKIPPED. Datasets are undefined')

    return analysis_datasets_section, attrs_ts_collections

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to analyze time information
def analyze_time_info(file_info_start, file_info_end, tag_file_reference='file_create'):

    time_ref_start = define_time_reference(
        file_info_start, tag_file_reference=tag_file_reference)
    time_ref_end = define_time_reference(
        file_info_end, tag_file_reference=tag_file_reference)

    if (time_ref_start is not None) and (time_ref_end is not None):
        time_ref_elapsed = time_ref_end[0] - time_ref_start[0]

        if isinstance(time_ref_start, list) and (time_ref_start.__len__() == 1):
            time_ref_start = time_ref_start[0]
        else:
            log_stream.error(' ===> The format of "time_ref_start" is not supported')
            raise NotImplemented('Case not implemented yet')

        if isinstance(time_ref_end, list) and (time_ref_end.__len__() == 1):
            time_ref_end = time_ref_end[0]
        else:
            log_stream.error(' ===> The format of "time_ref_end" is not supported')
            raise NotImplemented('Case not implemented yet')

        if time_ref_start > time_ref_end:
            log_stream.warning(' ===> The case between "time_ref_start" < "time_ref_end" is not expected')
            time_ref_end, time_ref_elapsed = None, None
        elif time_ref_start <= time_ref_end:
            pass
        else:
            log_stream.error(' ===> The case between "time_ref_start" and "time_ref_end" is not supported')
            raise NotImplemented('Case not implemented yet')

    elif (time_ref_start is not None) and (time_ref_end is None):
        time_ref_end, time_ref_elapsed = None, None
    else:
        log_stream.error(' ===> The case of "time_ref_start" and ""time_ref_end" is not supported')
        raise NotImplemented('Case not implemented yet')

    return time_ref_start, time_ref_end, time_ref_elapsed

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define file reference
def define_time_reference(file_info, tag_file_reference='file_create'):

    if file_info is not None:
        if isinstance(file_info, dict):

            if tag_file_reference in list(file_info.keys()):
                file_time_reference = [file_info[tag_file_reference]]
            else:
                file_time_list = []
                for file_key, file_values in file_info.items():
                    if file_values is not None:
                        if tag_file_reference in list(file_values.keys()):
                            file_time_step = file_values[tag_file_reference]
                            file_time_list.append(file_time_step)
                    else:
                        log_stream.warning(' ===> Define time reference for section "' +
                                           file_key + '" is not possible. All fields are undefined.')
                if file_time_list:
                    file_time_idx = pd.DatetimeIndex(file_time_list)
                    file_time_reference = [file_time_idx.max()]
                else:
                    file_time_reference = None
                    log_stream.warning(' ===> Time list object is not defined, All datasets are undefined.')
        else:
            log_stream.error(' ===> Define time reference is not possible; the info object format is not supported')
            raise NotImplemented('Case not implemented yet')
    else:
        file_time_reference = None

    return file_time_reference
# -------------------------------------------------------------------------------------
