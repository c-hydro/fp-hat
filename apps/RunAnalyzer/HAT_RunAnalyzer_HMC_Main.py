#!/usr/bin/python3
"""
Hydrological Analysis Tool - RunAnalyzer

__date__ = '20200605'
__version__ = '1.0.0'
__author__ =
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
        'Flavio Pignone (flavio.pignone@cimafoundation.org',

__library__ = 'HAT'

General command line:
python3 HAT_RunAnalyzer_HMC_Main.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20200605 (1.0.0) --> Beta release
"""

# -------------------------------------------------------------------------------------
# Complete library
import logging
import warnings
import time
import os

import numpy as np
import pandas as pd

from copy import deepcopy
from argparse import ArgumentParser

from lib_utils_io import read_file_json, read_file_warning, read_file_discharge, write_file_status, read_obj, write_obj
from lib_utils_system import make_folder, fill_tags2string
from lib_utils_time import set_time
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_version = '1.0.0'
alg_release = '2020-06-05'
alg_name = 'RUN ANALYZER'
# Algorithm parameter(s)
time_format = '%Y-%m-%d %H:%M'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_json(alg_settings)

    # Set algorithm logging
    make_folder(data_settings['log']['folder_name'])
    set_logging(logger_file=os.path.join(data_settings['log']['folder_name'],
                                         data_settings['log']['file_name']))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize time information
    time_run, time_exec, time_range = set_time(
        time_run_args=alg_time, time_run_file=data_settings['time']['time_now'],
        time_format=time_format,
        time_period=data_settings['time']['time_period'],
        time_frequency=data_settings['time']['time_frequency'],
        time_rounding=data_settings['time']['time_rounding'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to freeze run basin information
    info_collections = freeze_run_info(data_settings['run'])

    # Method to search available executions
    execution_collections = search_run_execution(
        time_run,
        algorithm_execution=data_settings['data']['source']['execution'],
        run_data=data_settings['run'],
        template_tags=data_settings['template_tags'])

    # Method to search available results
    results_header, results_collections = search_run_results(
        time_range,
        algorithm_results=data_settings['data']['source']['results'],
        run_data=data_settings['run'],
        template_tags=data_settings['template_tags'])

    # Method to get run warnings
    data_collections_warning = get_run_warning(results_collections, template_fields=data_settings['template_fields'])

    # Method to get run discharges
    data_header, data_collections_discharge = get_run_discharge(results_collections, data_collections_warning,
                                                                template_fields=data_settings['template_fields'])

    # Method to analyze run execution
    analysis_collections_executions = analyze_run_execution(execution_collections,
                                                            template_fields=data_settings['template_fields'])

    # Method to analyze run results
    analysis_header, analysis_collections_results = analyze_run_results(
        time_run, data_header, results_header, data_collections_discharge,
        flag_ancillary=data_settings['flags']['update_ancillary'],
        data_ancillary=data_settings['data']['ancillary'],
        template_tags=data_settings['template_tags']
    )

    # Method to dump run status
    dump_run_status(time_run, time_exec, time_format=time_format,
                    algorithm_destination=data_settings['data']['destination'],
                    default_header=info_collections,
                    analysis_header=analysis_header,
                    analysis_execution=analysis_collections_executions,
                    analysis_results=analysis_collections_results,
                    template_tags=data_settings['template_tags'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    time_elapsed = round(time.time() - start_time, 1)

    logging.info(' ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> TIME ELAPSED: ' + str(time_elapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')

    # -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to dump run status
def dump_run_status(time_run, time_exec, time_format='%Y-%m-%d %H:%M',
                    algorithm_destination=None,
                    default_header=None,
                    analysis_header=None, analysis_execution=None, analysis_results=None,
                    template_tags=None,
                    folder_name_tag='folder_name', file_name_tag='file_name'):

    datetime_run = time_run.to_pydatetime()
    # datetime_exec = time_exec.to_pydatetime()

    time_ref = time_run.replace(hour=0, minute=0)
    time_range_ref = pd.date_range(start=time_ref, periods=2, freq='D')

    folder_name_raw = algorithm_destination[folder_name_tag]
    file_name_raw = algorithm_destination[file_name_tag]

    template_values = {'run_datetime': datetime_run, 'run_sub_path_time': datetime_run,
                       'analysis_datetime': datetime_run, 'analysis_sub_path_time': datetime_run}

    folder_name_def = fill_tags2string(folder_name_raw, template_tags, template_values)
    file_name_def = fill_tags2string(file_name_raw, template_tags, template_values)

    make_folder(folder_name_def)
    file_path_def = os.path.join(folder_name_def, file_name_def)

    logging.info(' ---> Organize html datasets ... ')

    collections_ancillary = {}
    collections_alarm = {}
    collections_alert = {}
    for run_key, run_fields in analysis_header.items():

        # DEBUG START
        # run_key = 'realtime_rf-ecmwf-0100'
        # run_fields = analysis_header[run_key]

        logging.info(' ----> RunType ' + run_key + ' ... ')

        if run_fields is not None:

            collections_ancillary[run_key] = {}
            collections_alarm[run_key] = {}
            collections_alert[run_key] = {}

            run_analysis_execution = analysis_execution[run_key]
            run_analysis_results = analysis_results[run_key]

            collections_ancillary[run_key]['description'] = run_fields['description']
            collections_ancillary[run_key]['scenario_n'] = run_fields['scenario_n']
            collections_ancillary[run_key]['section_n'] = run_fields['section_n']
            collections_ancillary[run_key]['time_modified_first'] = run_analysis_execution['time_created_first']
            collections_ancillary[run_key]['time_modified_last'] = run_fields['time_file_modified']
            collections_ancillary[run_key]['time_range'] = time_range_ref

            for point_key, point_fields in run_analysis_results.items():

                point_tag = point_fields['name']
                point_fields_alarm = point_fields['discharge_alarm']
                point_fields_alert = point_fields['discharge_alert']

                point_field_alert_select = point_fields_alert[point_fields_alert.index >= time_ref]
                point_field_alarm_select = point_fields_alarm[point_fields_alarm.index >= time_ref]

                logging.info(' -----> Point ' + point_tag + ' ... ')

                for time_id, time_range_step in enumerate(time_range_ref):

                    time_alert_control = [time_check for time_check in point_field_alert_select.index if
                                          time_check.replace(hour=0, minute=0) == time_range_step]
                    time_alarm_control = [time_check for time_check in point_field_alarm_select.index if
                                          time_check.replace(hour=0, minute=0) == time_range_step]

                    if time_alert_control:

                        if point_field_alert_select.values[time_id] != -9999:
                            point_field_alert_idx = point_field_alert_select.index[time_id]
                            point_field_alert_value = point_field_alert_select.values[time_id]

                            if time_range_step not in list(collections_alert[run_key].keys()):
                                collections_alert[run_key][time_range_step] = {}
                                collections_alert[run_key][time_range_step]['name'] = [point_tag]
                                collections_alert[run_key][time_range_step]['idx'] = [point_field_alert_idx]
                                collections_alert[run_key][time_range_step]['value'] = [point_field_alert_value]
                            else:
                                name_tmp = collections_alert[run_key][time_range_step]['point']
                                idx_tmp = collections_alert[run_key][time_range_step]['idx']
                                value_tmp = collections_alert[run_key][time_range_step]['value']

                                name_tmp.append(point_tag)
                                idx_tmp.append(point_field_alert_idx)
                                value_tmp.append(point_field_alert_value)

                                collections_alert[run_key][time_range_step]['name'] = name_tmp
                                collections_alert[run_key][time_range_step]['idx'] = idx_tmp
                                collections_alert[run_key][time_range_step]['value'] = value_tmp

                    if time_alarm_control:

                        if point_field_alarm_select.values[time_id] != -9999:
                            point_field_alarm_idx = point_field_alarm_select.index[time_id]
                            point_field_alarm_value = point_field_alarm_select.values[time_id]

                            if time_range_step not in list(collections_alarm[run_key].keys()):
                                collections_alarm[run_key][time_range_step] = {}
                                collections_alarm[run_key][time_range_step]['name'] = [point_tag]
                                collections_alarm[run_key][time_range_step]['idx'] = [point_field_alarm_idx]
                                collections_alarm[run_key][time_range_step]['value'] = [point_field_alarm_value]
                            else:
                                name_tmp = collections_alarm[run_key][time_range_step]['point']
                                idx_tmp = collections_alarm[run_key][time_range_step]['idx']
                                value_tmp = collections_alarm[run_key][time_range_step]['value']

                                name_tmp.append(point_tag)
                                idx_tmp.append(point_field_alarm_idx)
                                value_tmp.append(point_field_alarm_value)

                                collections_alarm[run_key][time_range_step]['name'] = name_tmp
                                collections_alarm[run_key][time_range_step]['idx'] = idx_tmp
                                collections_alarm[run_key][time_range_step]['value'] = value_tmp

                logging.info(' -----> Point ' + point_tag + ' ... DONE')

            logging.info(' ----> RunType ' + run_key + ' ... DONE')

        else:
            collections_ancillary[run_key] = None
            collections_alarm[run_key] = None
            collections_alert[run_key] = None

            logging.info(' ----> RunType ' + run_key + ' ... SKIPPED. Datasets are undefined.')

    logging.info(' ---> Organize html datasets ... DONE')

    logging.info(' ---> Write html datasets ... ')
    write_file_status(time_run, time_exec, time_format='%Y-%m-%d %H:%M', html_name=file_path_def,
                      run_default=default_header,
                      run_execution=analysis_execution,
                      run_ancillary=collections_ancillary,
                      run_alert=collections_alert, run_alarm=collections_alarm)
    logging.info(' ---> Write html datasets ... DONE')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to analyze run execution(s)
def analyze_run_execution(execution_collections, template_fields=None):

    logging.info(' ---> Analyze run executions ... ')

    html_collections = {}
    for run_key, run_file_list in execution_collections.items():

        logging.info(' ----> RunType ' + run_key + ' ... ')

        if run_file_list:

            time_created = []
            time_modified = []
            for file_name_raw in run_file_list:

                template_values = {'run_name': run_key}

                file_name_def = fill_tags2string(file_name_raw, template_fields, template_values)

                file_modified = pd.Timestamp(time.ctime(os.path.getmtime(file_name_def)))
                file_created = pd.Timestamp(time.ctime(os.path.getctime(file_name_def)))

                time_created.append(file_created)
                time_modified.append(file_modified)

            scenario_n = run_file_list.__len__()

            datetime_created = pd.DatetimeIndex(time_created)
            datetime_modified = pd.DatetimeIndex(time_modified)

            datetime_created_first = datetime_created.min()
            datetime_created_last = datetime_created.max()

            datetime_modified_first = datetime_modified.min()
            datetime_modified_last = datetime_modified.max()

            html_collections[run_key] = {}
            html_collections[run_key]['scenario_n'] = scenario_n
            html_collections[run_key]['time_created_first'] = datetime_created_first
            html_collections[run_key]['time_created_last'] = datetime_created_last
            html_collections[run_key]['time_modified_first'] = datetime_modified_first
            html_collections[run_key]['time_modified_last'] = datetime_modified_last

            logging.info(' ----> RunType ' + run_key + ' ... DONE')

        else:

            html_collections[run_key] = None
            logging.info(' ----> RunType ' + run_key + ' ... SKIPPED. Run is not available.')

    logging.info(' ---> Analyze run executions ... DONE')

    return html_collections

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to analyze run results
def analyze_run_results(time_run, data_header, results_header, data_collections,
                        tag_columns='data_max', data_ancillary=None, flag_ancillary=False,
                        template_tags=None):

    logging.info(' ---> Analyze run results ... ')

    # Prepare ancillary data
    folder_name_raw = data_ancillary['folder_name']
    file_name_raw = data_ancillary['file_name']

    template_values = {'run_datetime': time_run, 'run_sub_path_time': time_run}

    folder_name_def = fill_tags2string(folder_name_raw, template_tags, template_values)
    file_name_def = fill_tags2string(file_name_raw, template_tags, template_values)

    file_path_def = os.path.join(folder_name_def, file_name_def)

    if flag_ancillary:
        if os.path.exists(file_path_def):
            os.remove(file_path_def)

    if not os.path.exists(file_path_def) or flag_ancillary:
        html_header = {}
        html_collections = {}
        for run_key, run_data in data_collections.items():

            logging.info(' ----> RunType ' + run_key + ' ... ')

            # DEBUG START
            # run_key = 'realtime_rf-ecmwf-0100'
            # run_data = data_collections[run_key]

            if run_data is not None:

                html_header[run_key] = {**data_header[run_key], **results_header[run_key]}

                html_collections[run_key] = {}
                for point_key, point_data in run_data.items():

                    point_basin = point_data['Basin']
                    point_section = point_data['Section']
                    point_alarm_thr = point_data['QAlarm']
                    point_alert_thr = point_data['QAlert']
                    point_data_raw = point_data['discharge_modelled']

                    point_tag = '@'.join([point_basin, point_section])

                    logging.info(' -----> Point ' + point_tag + ' ... ')

                    point_time_n = point_data_raw.shape[0]
                    point_step_n = point_data_raw.shape[1]

                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        point_data_max = np.nanmax(point_data_raw, axis=1)

                    point_time_hourly_idx = pd.date_range(start=data_header[run_key]['time_start'],
                                                          periods=point_time_n, freq=data_header[run_key]['time_frequency'])

                    point_time_hourly_start = point_time_hourly_idx[0]
                    point_time_hourly_end = point_time_hourly_idx[-1]

                    point_df_hourly = pd.DataFrame(index=point_time_hourly_idx, data=point_data_max, columns=[tag_columns])

                    point_df_daily = point_df_hourly.loc[point_df_hourly.groupby(pd.Grouper(freq='D')).idxmax().iloc[:, 0]]
                    point_time_daily_maximum = point_df_daily.index
                    point_time_daily_default = point_df_daily.index.floor('D')

                    point_df_alarm_select = point_df_daily[point_df_daily[tag_columns] >= point_alarm_thr]
                    point_df_alert_select = point_df_daily[point_df_daily[tag_columns] >= point_alert_thr]

                    point_data_daily_default = np.zeros(shape=point_time_daily_default.size)
                    point_data_daily_default[:] = -9999.0
                    point_df_daily_default = pd.DataFrame(index=point_time_daily_default, data=point_data_daily_default,
                                                          columns=[tag_columns])

                    point_df_alarm_filled = point_df_daily_default.combine_first(point_df_alarm_select)
                    point_df_alarm_unique = point_df_alarm_filled.loc[point_df_alarm_filled.groupby(
                        pd.Grouper(freq='D')).idxmax().iloc[:, 0]]

                    point_df_alert_filled = point_df_daily_default.combine_first(point_df_alert_select)
                    point_df_alert_unique = point_df_alert_filled.loc[point_df_alert_filled.groupby(
                        pd.Grouper(freq='D')).idxmax().iloc[:, 0]]

                    html_collections[run_key][point_key] = {}
                    html_collections[run_key][point_key]['name'] = point_tag
                    html_collections[run_key][point_key]['time_start'] = point_time_hourly_start
                    html_collections[run_key][point_key]['time_end'] = point_time_hourly_end
                    html_collections[run_key][point_key]['discharge_alarm'] = point_df_alarm_unique
                    html_collections[run_key][point_key]['discharge_alert'] = point_df_alert_unique

                    logging.info(' -----> Point ' + point_tag + ' ... DONE')

                logging.info(' ----> RunType ' + run_key + ' ... DONE')

            else:
                html_header[run_key] = None
                html_collections[run_key] = None

                logging.info(' ----> RunType ' + run_key + ' ... SKIPPED. Datasets are undefined.')

        make_folder(folder_name_def)
        html_obj = {'header': html_header, 'collections': html_collections}
        write_obj(file_path_def, html_obj)

        logging.info(' ---> Analyze run results ... DONE')

    else:

        html_obj = read_obj(file_path_def)
        html_header = html_obj['header']
        html_collections = html_obj['collections']

        logging.info(' ---> Analyze run results ... SKIPPED. PREVIOUSLY SAVED')

    return html_header, html_collections

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get warning data
def get_run_warning(run_collections, tag_field='warning', template_fields=None):

    logging.info(' ---> Get warning table ... ')

    warning_collections = {}
    for run_key, run_data in run_collections.items():

        logging.info(' ----> RunType ' + run_key + ' ... ')

        warning_collections[run_key] = {}
        if run_data:

            run_fields = run_data[tag_field]
            file_step = run_fields['file_list'][0]

            if os.path.exists(file_step):
                data_header, data_collections = read_file_warning(file_step, file_template=template_fields)
                data_header['section_n'] = list(data_collections.keys()).__len__()
            else:
                data_header = None
                data_collections = None

            warning_collections[run_key]['header'] = data_header
            warning_collections[run_key]['data'] = data_collections

            logging.info(' ----> RunType ' + run_key + ' ... DONE')

        else:
            warning_collections[run_key]['header'] = None
            warning_collections[run_key]['data'] = None

            logging.info(' ----> RunType ' + run_key + ' ... SKIPPED. Warning table is not available')

    logging.info(' ---> Get warning table ... DONE')

    return warning_collections
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get discharge data
def get_run_discharge(run_collections, warning_collections, tag_field='discharge', template_fields=None):

    logging.info(' ---> Get discharge time-series ... ')

    data_header = {}
    data_collections = {}
    for run_key, run_data in run_collections.items():

        logging.info(' ----> RunType ' + run_key + ' ... ')

        if run_data:

            run_fields = run_data[tag_field]
            warning_section = warning_collections[run_key]

            warning_header = warning_section['header']
            warning_data = warning_section['data']

            data_workspace = deepcopy(warning_data)

            data_header[run_key] = {}
            data_collections[run_key] = {}
            for (data_key, data_field), data_ws in zip(warning_data.items(), data_workspace.values()):

                field_basin = data_field['Basin']
                field_section = data_field['Section']

                file_select = [elem for elem in run_fields['file_list'] if (field_basin in elem) and (field_section in elem)][0]

                if os.path.exists(file_select):
                    discharge_header, discharge_data_modelled, discharge_data_observed = read_file_discharge(
                        file_select, file_template=template_fields)
                else:
                    discharge_header = None
                    discharge_data_modelled = None
                    discharge_data_observed = None

                data_header[run_key] = {**warning_header, **discharge_header}
                data_ws['discharge_observed'] = discharge_data_observed
                data_ws['discharge_modelled'] = discharge_data_modelled

                data_collections[run_key][data_key] = data_ws

            logging.info(' ----> RunType ' + run_key + ' ... DONE')

        else:
            data_header[run_key] = None
            data_collections[run_key] = None

            logging.info(' ----> RunType ' + run_key + ' ... SKIPPED. Discharge time-series are not available')

    logging.info(' ---> Get discharge time-series ... DONE')

    return data_header, data_collections
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to freeze run information
def freeze_run_info(run_data):
    logging.info(' ---> Freeze run information ... ')
    info_collections = {}
    for run_id, run_step in run_data.items():
        run_key = run_step['ancillary']['name']
        info_collections[run_key] = {}
        for run_field, run_value in run_step['ancillary'].items():
            info_collections[run_key][run_field] = run_value
    logging.info(' ---> Freeze run information ... DONE')

    return info_collections

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to search available run
def search_run_execution(time_run, algorithm_execution, run_data=None, template_tags=None,
                         folder_name_tag='folder_name', file_name_tag='file_name'):

    logging.info(' ---> Search run executions ... ')

    execution_collections = {}

    datetime_run = time_run.to_pydatetime()
    for run_id, run_step in run_data.items():

        run_key = run_step['ancillary']['name']

        logging.info(' ----> RunType ' + run_key + ' ... ')

        folder_name_raw = algorithm_execution[folder_name_tag]
        file_name_raw = algorithm_execution[file_name_tag]

        template_values = {'run_name': run_key,
                           'run_datetime': datetime_run, 'run_sub_path_time': datetime_run}

        folder_name_def = fill_tags2string(folder_name_raw, template_tags, template_values)
        file_name_def = fill_tags2string(file_name_raw, template_tags, template_values)

        file_list = []
        for root, dirs, files in os.walk(folder_name_def, topdown=False):
            for name in files:
                if name == file_name_def:
                    file_list.append(os.path.join(root, name))

        execution_collections[run_key] = {}
        execution_collections[run_key] = file_list

        logging.info(' ----> RunType ' + run_key + ' ... DONE')

    logging.info(' ---> Search run executions ... DONE')

    return execution_collections

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to search available run results
def search_run_results(time_range_max, algorithm_results=None, run_data=None, template_tags=None,
                       folder_name_tag='folder_name', file_name_tag='file_name'):

    logging.info(' ---> Search run results ... ')

    results_header = {}
    results_collections = {}
    for run_id, run_step in run_data.items():

        run_key = run_step['ancillary']['name']

        time_period = run_step['time']['time_period']
        time_frequency = run_step['time']['time_frequency']
        time_rounding = run_step['time']['time_rounding']

        time_end = time_range_max[0]
        if time_period == 1:
            time_start = time_end.floor(time_rounding)
        else:
            time_start = pd.date_range(end=time_end.floor(time_rounding),
                                       periods=time_period, freq=time_rounding)[0]

        if time_end == time_start:
            time_range_adapt = pd.date_range(end=time_end, periods=time_period, freq=time_frequency)
        else:
            time_range_adapt = pd.date_range(start=time_start, end=time_end, freq=time_frequency)
        time_range_adapt = time_range_adapt[::-1]

        logging.info(' ----> RunType ' + run_key + ' ... ')

        run_locs = deepcopy(algorithm_results)

        results_collections[run_key] = {}
        results_header[run_key] = {}
        path_name_time = []
        path_name_list = []
        for time_step in time_range_adapt:

            datetime_step = time_step.to_pydatetime()

            for loc_key, loc_args in run_locs.items():

                template_values = {'run_name': run_key,
                                   'run_datetime': datetime_step, 'run_sub_path_time': datetime_step}

                folder_name_raw = loc_args[folder_name_tag]
                file_name_raw = loc_args[file_name_tag]

                folder_name_def = fill_tags2string(folder_name_raw, template_tags, template_values)
                file_name_def = fill_tags2string(file_name_raw, template_tags, template_values)

                if os.path.exists(folder_name_def):

                    if loc_key not in list(results_collections[run_key].keys()):
                        results_collections[run_key][loc_key] = {}
                        path_name_time = []
                        path_name_list = []

                    if not path_name_list:

                        if '*' in file_name_def:
                            file_name_list = os.listdir(folder_name_def)

                            if file_name_list.__len__() > 0:

                                for file_name_step in file_name_list:
                                    path_name_step = os.path.join(folder_name_def, file_name_step)
                                    path_name_list.append(path_name_step)
                                path_name_time.append(time_step)

                        else:
                            path_name_def = os.path.join(folder_name_def, file_name_def)
                            if os.path.exists(path_name_def):
                                path_name_list.append(path_name_def)
                                path_name_time.append(time_step)

                        if path_name_list.__len__() > 0:
                            results_collections[run_key][loc_key]['time'] = path_name_time
                            results_collections[run_key][loc_key]['file_list'] = path_name_list

        for field_key, field_value in run_step['ancillary'].items():
            results_header[run_key][field_key] = field_value
        for field_key, field_value in run_step['time'].items():
            results_header[run_key][field_key] = field_value

        logging.info(' ----> RunType ' + run_key + ' ... DONE')

    logging.info(' ---> Search run results ... DONE')

    return results_header, results_collections
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_settings, alg_time


# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set logging information
def set_logging(logger_file='log.txt', logger_format=None):
    if logger_format is None:
        logger_format = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

    # Remove old logging file
    if os.path.exists(logger_file):
        os.remove(logger_file)

    # Set level of root debugger
    logging.root.setLevel(logging.DEBUG)

    # Open logging basic configuration
    logging.basicConfig(level=logging.DEBUG, format=logger_format, filename=logger_file, filemode='w')

    # Set logger handle
    logger_handle_1 = logging.FileHandler(logger_file, 'w')
    logger_handle_2 = logging.StreamHandler()
    # Set logger level
    logger_handle_1.setLevel(logging.DEBUG)
    logger_handle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    logger_formatter = logging.Formatter(logger_format)
    logger_handle_1.setFormatter(logger_formatter)
    logger_handle_2.setFormatter(logger_formatter)

    # Add handle to logging
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)


# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == '__main__':
    main()
# ----------------------------------------------------------------------------
