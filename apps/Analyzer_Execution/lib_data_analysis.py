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

import pandas as pd
from copy import deepcopy

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to analyze data hydrograph
def analyze_hydrograph_datasets(run_name, file_datasets,
                                tag_discharge_observed='discharge_observed',
                                tag_discharge_simulated='discharge_simulated',
                                tag_discharge_thr_alert='section_discharge_thr_alert',
                                tag_discharge_thr_alarm='section_discharge_thr_alarm',
                                tag_discharge_max_alert_value='discharge_alert_max_value',
                                tag_discharge_max_alert_index='discharge_alert_max_index',
                                tag_discharge_max_alarm_value='discharge_alarm_max_value',
                                tag_discharge_max_alarm_index='discharge_alarm_max_index',
                                tag_section_n='section_n', tag_run_n='run_n',
                                tag_run_type='run_type'):

    section_n = file_datasets.__len__()

    analysis_warnings_section = {}
    analysis_datasets_section = {}
    attrs_ts_collections = None
    for section_tag, section_datasets in file_datasets.items():

        logging.info(' ----> Analyze section ' + section_tag + ' ... ')

        section_dframe = section_datasets[0]
        section_attrs = section_datasets[1]

        section_ts_vars = section_attrs['run_var'].split(',')
        # data_thr_alert = float(section_attrs[tag_discharge_thr_alert])
        # data_thr_alarm = float(section_attrs[tag_discharge_thr_alarm])

        # DEBUG
        data_thr_alert = 1
        data_thr_alarm = 10

        section_ts_time = section_dframe.index
        section_ts_days = section_ts_time[1:].normalize().unique()

        # Create analysis datasets section
        if section_ts_vars.__len__() == 1:

            run_n = 1

            section_ts_collections = {}
            for section_ts_step in section_ts_days:

                section_ts_collections[section_ts_step] = {}
                section_ts_collections[section_ts_step][tag_discharge_max_alert_value] = {}
                section_ts_collections[section_ts_step][tag_discharge_max_alert_index] = {}
                section_ts_collections[section_ts_step][tag_discharge_max_alarm_value] = {}
                section_ts_collections[section_ts_step][tag_discharge_max_alarm_index] = {}

                ts_day = section_ts_step.day
                ts_month = section_ts_step.month
                ts_year = section_ts_step.year

                section_dframe_day = section_dframe.loc[(section_dframe.index.day == ts_day) &
                                                        (section_dframe.index.month == ts_month) &
                                                        (section_dframe.index.year == ts_year), :]

                section_ts_day_sim = section_dframe_day[tag_discharge_simulated]
                section_ts_day_obs = section_dframe_day[tag_discharge_observed]

                section_ts_thr_alert = section_ts_day_sim.where(section_ts_day_sim > data_thr_alert)
                section_ts_thr_alarm = section_ts_day_sim.where(section_ts_day_sim > data_thr_alarm)

                section_ts_alert_max_value = section_ts_thr_alert.max(skipna=True)
                section_ts_alert_max_index = section_ts_thr_alert.idxmax(skipna=True)

                section_ts_alarm_max_value = section_ts_thr_alarm.max(skipna=True)
                section_ts_alarm_max_index = section_ts_thr_alarm.idxmax(skipna=True)

                section_ts_collections[section_ts_step][tag_discharge_max_alert_value] = section_ts_alert_max_value
                section_ts_collections[section_ts_step][tag_discharge_max_alert_index] = section_ts_alert_max_index
                section_ts_collections[section_ts_step][tag_discharge_max_alarm_value] = section_ts_alarm_max_value
                section_ts_collections[section_ts_step][tag_discharge_max_alarm_index] = section_ts_alarm_max_index
                section_ts_collections[section_ts_step][tag_discharge_thr_alert] = data_thr_alert
                section_ts_collections[section_ts_step][tag_discharge_thr_alarm] = data_thr_alarm
                section_ts_collections[section_ts_step][tag_run_type] = run_name

            if attrs_ts_collections is None:
                attrs_ts_collections = {tag_run_n: run_n, tag_section_n: section_n, tag_run_type: run_name}
        else:

            run_n = section_ts_vars.__len__()

            section_ts_collections = {}
            for section_ts_step in section_ts_days:

                section_ts_collections[section_ts_step] = {}
                section_ts_collections[section_ts_step][tag_discharge_max_alert_value] = {}
                section_ts_collections[section_ts_step][tag_discharge_max_alert_index] = {}
                section_ts_collections[section_ts_step][tag_discharge_max_alarm_value] = {}
                section_ts_collections[section_ts_step][tag_discharge_max_alarm_index] = {}
                section_ts_collections[section_ts_step][tag_discharge_thr_alert] = {}
                section_ts_collections[section_ts_step][tag_discharge_thr_alarm] = {}

                ts_day = section_ts_step.day
                ts_month = section_ts_step.month
                ts_year = section_ts_step.year

                section_ts_alert_max_value_list = []
                section_ts_alert_max_index_list = []
                section_ts_alarm_max_value_list = []
                section_ts_alarm_max_index_list = []
                for section_ts_var in section_ts_vars:

                    tag_discharge_simulated_var = tag_discharge_simulated.format(section_ts_var)
                    tag_discharge_observed_var = tag_discharge_observed.format(section_ts_var)

                    section_dframe_day = section_dframe.loc[(section_dframe.index.day == ts_day) &
                                                            (section_dframe.index.month == ts_month) &
                                                            (section_dframe.index.year == ts_year), :]

                    section_ts_sim_var = section_dframe_day[tag_discharge_simulated_var]
                    section_ts_obs_var = section_dframe_day[tag_discharge_observed_var]

                    section_ts_thr_alert_var = section_ts_sim_var.where(section_ts_sim_var > data_thr_alert)
                    section_ts_thr_alarm_var = section_ts_sim_var.where(section_ts_sim_var > data_thr_alarm)

                    section_ts_alert_max_value_var = section_ts_thr_alert_var.max(skipna=True)
                    section_ts_alert_max_index_var = section_ts_thr_alert_var.idxmax(skipna=True)

                    section_ts_alarm_max_value_var = section_ts_thr_alarm_var.max(skipna=True)
                    section_ts_alarm_max_index_var = section_ts_thr_alarm_var.idxmax(skipna=True)

                    if section_ts_alert_max_index_var not in section_ts_alert_max_index_list:
                        section_ts_alert_max_value_list.append(section_ts_alert_max_value_var)
                        section_ts_alert_max_index_list.append(section_ts_alert_max_index_var)
                    if section_ts_alarm_max_index_var not in section_ts_alarm_max_index_list:
                        section_ts_alarm_max_value_list.append(section_ts_alarm_max_value_var)
                        section_ts_alarm_max_index_list.append(section_ts_alarm_max_index_var)

                section_ts_thr_alert_max = pd.Series([section_ts_alert_max_value_list])
                section_ts_thr_alert_max.index = section_ts_alert_max_index_list
                section_ts_thr_alarm_max = pd.Series([section_ts_alarm_max_value_list])
                section_ts_thr_alarm_max.index = section_ts_alarm_max_index_list

                if section_ts_thr_alert_max.shape[0] == 1:
                    section_ts_alert_max_value = section_ts_thr_alert_max.values[0]
                    section_ts_alert_max_index = section_ts_thr_alert_max.index[0]
                else:
                    section_ts_alert_max_value = section_ts_thr_alert_max.max(skipna=True)
                    section_ts_alert_max_index = section_ts_thr_alert_max.idxmax(skipna=True)

                if section_ts_thr_alarm_max.shape[0] == 1:
                    section_ts_alarm_max_value = section_ts_thr_alarm_max.values[0]
                    section_ts_alarm_max_index = section_ts_thr_alarm_max.index[0]
                else:
                    section_ts_alarm_max_value = section_ts_thr_alarm_max.max(skipna=True)
                    section_ts_alarm_max_index = section_ts_thr_alarm_max.idxmax(skipna=True)

                if isinstance(section_ts_alert_max_value, list):
                    if section_ts_alert_max_value.__len__() == 1:
                        section_ts_alert_max_value = section_ts_alert_max_value[0]
                    else:
                        raise NotImplementedError('Analysis hydrograph format max alert value in unsupported format')

                if isinstance(section_ts_alarm_max_value, list):
                    if section_ts_alarm_max_value.__len__() == 1:
                        section_ts_alarm_max_value = section_ts_alarm_max_value[0]
                    else:
                        raise NotImplementedError('Analysis hydrograph format max alarm value in unsupported format')

                section_ts_collections[section_ts_step][tag_discharge_max_alert_value] = section_ts_alert_max_value
                section_ts_collections[section_ts_step][tag_discharge_max_alert_index] = section_ts_alert_max_index
                section_ts_collections[section_ts_step][tag_discharge_max_alarm_value] = section_ts_alarm_max_value
                section_ts_collections[section_ts_step][tag_discharge_max_alarm_index] = section_ts_alarm_max_index
                section_ts_collections[section_ts_step][tag_discharge_thr_alert] = data_thr_alert
                section_ts_collections[section_ts_step][tag_discharge_thr_alarm] = data_thr_alarm
                section_ts_collections[section_ts_step][tag_run_type] = run_name

                if attrs_ts_collections is None:
                    attrs_ts_collections = {tag_run_n: run_n, tag_section_n: section_n, tag_run_type: run_name}

        # Create analysis warning section
        if section_tag not in list(analysis_warnings_section.keys()):
            analysis_warnings_section[section_tag] = {}
            for section_time, section_data in section_ts_collections.items():
                for section_key, section_value in section_data.items():
                    if section_key in list(analysis_warnings_section[section_tag].keys()):
                        section_value_tmp = deepcopy(analysis_warnings_section[section_tag][section_key])
                        section_value_tmp.append(section_value)
                        analysis_warnings_section[section_tag][section_key] = section_value_tmp
                    else:
                        analysis_warnings_section[section_tag][section_key] = {}
                        analysis_warnings_section[section_tag][section_key] = [section_value]

        analysis_datasets_section[section_tag] = section_ts_collections

        logging.info(' ----> Analyze section ' + section_tag + ' ... DONE')

    return analysis_datasets_section, analysis_warnings_section, attrs_ts_collections

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to analyze time information
def analyze_time_info(file_info_start, file_info_end, tag_file_create='file_create'):

    time_creation_start = define_time_creation(
        file_info_start, tag_file_create=tag_file_create)
    time_creation_end = define_time_creation(
        file_info_end, tag_file_create=tag_file_create)

    time_creation_elapsed = time_creation_end[0] - time_creation_start[0]

    if isinstance(time_creation_start, list) and (time_creation_start.__len__() == 1):
        time_creation_start = time_creation_start[0]
    else:
        raise NotImplementedError('Time creation start format not supported yet')

    if isinstance(time_creation_end, list) and (time_creation_end.__len__() == 1):
        time_creation_end = time_creation_end[0]
    else:
        raise NotImplementedError('Time creation end format not supported yet')

    if time_creation_start > time_creation_end:
        time_creation_end = None
        time_creation_elapsed = None
    elif time_creation_start <= time_creation_end:
        pass
    else:
        raise NotImplementedError('Analyze time information case not implemented yet')

    return time_creation_start, time_creation_end, time_creation_elapsed

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define file creation
def define_time_creation(file_info, tag_file_create='file_create'):

    if isinstance(file_info, dict):

        if tag_file_create in list(file_info.keys()):
            file_time_creation = [file_info[tag_file_create]]
        else:
            file_time_list = []
            for file_values in file_info.values():
                if tag_file_create in list(file_values.keys()):
                    file_time_step = file_values[tag_file_create]
                    file_time_list.append(file_time_step)

            file_time_idx = pd.DatetimeIndex(file_time_list)
            file_time_creation = [file_time_idx.max()]
    else:
        raise NotImplementedError('File info obj is not defined by known format')

    return file_time_creation
# -------------------------------------------------------------------------------------
