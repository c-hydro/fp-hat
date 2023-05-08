"""
Class Features

Name:          driver_data_io_dynamic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""

######################################################################################
# Library
import logging
import os

import pandas as pd

from copy import deepcopy

from lib_utils_time import define_time_boundaries

from lib_utils_io import read_obj, write_obj
from lib_utils_system import fill_tags2string, make_folder

from lib_utils_exec import read_file_execution_info
from lib_data_io_json import read_file_hydrograph_ts, read_file_hydrograph_info

from lib_bulletin_data_analysis import organize_bulletin_info
from lib_bulletin_data_analysis import organize_bulletin_warnings_generic, organize_bulletin_warnings_section
from lib_bulletin_data_analysis import select_bulletin_time
from lib_bulletin_io_html import write_bulletin_summary
from lib_bulletin_io_xml import write_bulletin_warnings as write_bulletin_warn_xml
from lib_bulletin_io_ascii import write_bulletin_warnings as write_bulletin_warn_csv
from lib_bulletin_data_utils import merge_bulletin_datasets, init_bulletin_attrs, merge_bulletin_attrs

from lib_data_analysis import analyze_discharge_ts, analyze_time_info

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
######################################################################################


# -------------------------------------------------------------------------------------
# Class DriverDynamic
class DriverDynamic:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, time_now, time_exec, time_run, time_rounding='H', time_frequency='H',
                 src_dict=None, anc_dict=None, dest_dict=None,
                 static_data_collection=None,
                 alg_ancillary=None, alg_template_tags=None,
                 tag_section_data='section_data', tag_execution_data='execution_data',
                 tag_src_reference_start='run_reference_start', tag_src_reference_end='run_reference_end',
                 tag_anc_source='run_source', tag_anc_analysis='run_analysis', tag_anc_destination='run_destination',
                 tag_dest_summary='run_summary',
                 tag_dest_warnings_maximum='run_warnings_maximum', tag_dest_warnings_daily='run_warnings_daily',
                 tag_section_name='section_name', tag_section_catchment='section_catchment',
                 flag_cleaning_dynamic_source=True, flag_cleaning_dynamic_analysis=True,
                 flag_cleaning_dynamic_destination=True, flag_cleaning_dynamic_tmp=True,
                 string_sep=':'):

        self.time_now = time_now
        self.time_exec = time_exec
        self.time_run = time_run
        self.time_rounding = time_rounding
        self.time_frequency = time_frequency

        self.tag_section_data = tag_section_data
        self.tag_execution_data = tag_execution_data

        self.tag_src_reference_start = tag_src_reference_start
        self.tag_src_reference_end = tag_src_reference_end
        self.tag_anc_source = tag_anc_source
        self.tag_anc_analysis = tag_anc_analysis
        self.tag_anc_destination = tag_anc_destination
        self.tag_dest_summary = tag_dest_summary
        self.tag_dest_warnings_maximum = tag_dest_warnings_maximum
        self.tag_dest_warnings_daily = tag_dest_warnings_daily

        self.tag_section_name = tag_section_name
        self.tag_section_catchment = tag_section_catchment
        self.alg_ancillary = alg_ancillary
        self.alg_template_tags = alg_template_tags

        self.string_sep = string_sep

        self.sections_dframe = static_data_collection[self.tag_section_data]
        self.exec_dframe = static_data_collection[self.tag_execution_data]

        # get domain name information
        self.domain_name_list = self.alg_ancillary['domain_name']
        if not isinstance(self.domain_name_list, list):
            self.domain_name_list = [self.domain_name_list]
        # get title name information
        if 'title_name' in list(self.alg_ancillary.keys()):
            self.title_name = self.alg_ancillary['title_name']
        else:
            self.title_name = 'Bulletin of Operational Chain'
        # get time settings information
        if 'time_settings' in list(self.alg_ancillary.keys()):
            self.time_mode = self.alg_ancillary['time_settings']['time_mode']
            self.time_window_left = self.alg_ancillary['time_settings']['time_window_left']
            self.time_window_right = self.alg_ancillary['time_settings']['time_window_right']
        else:
            self.time_mode, self.time_window_left, self.time_window_right = 'LOCAL', None, None

        self.domain_name_list = self.alg_ancillary['domain_name']
        if not isinstance(self.domain_name_list, list):
            self.domain_name_list = [self.domain_name_list]

        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'
        self.status_active_tag = 'active'

        self.section_data_obj = self.filter_data_by_key(
            self.sections_dframe, key_value=self.domain_name_list, key_column='reference_db')
        self.section_name_obj = self.extract_data_by_key(
            self.section_data_obj, key_column=self.tag_section_name)
        self.section_catchment_obj = self.extract_data_by_key(
            self.section_data_obj, key_column=self.tag_section_catchment)

        self.outlet_name_obj = self.merge_data_by_key(
            self.section_catchment_obj, self.section_name_obj, obj_data_separator=self.string_sep)

        # define exec object(s)
        self.exec_name_list = list(self.exec_dframe.index)
        self.exec_values_list = list(self.exec_dframe.values)
        self.exec_type_list = list(self.exec_dframe.columns)

        # source folder(s) and file(s)
        file_obj_src_ref_start, file_obj_src_ref_end = {}, {}
        exec_name_obj, view_warn_obj, view_exec_obj = {}, {}, {}
        for exec_name, exec_fields in zip(self.exec_name_list, self.exec_values_list):

            for domain_name_step in self.domain_name_list:

                folder_name_src_ref_start = src_dict[domain_name_step][self.tag_src_reference_start][self.folder_name_tag]
                file_name_src_ref_start = src_dict[domain_name_step][self.tag_src_reference_start][self.file_name_tag]
                folder_name_src_ref_end = src_dict[domain_name_step][self.tag_src_reference_end][self.folder_name_tag]
                file_name_src_ref_end = src_dict[domain_name_step][self.tag_src_reference_end][self.file_name_tag]

                exec_dframe_step = self.exec_dframe.loc[self.exec_dframe['run_name'] == exec_name]
                if exec_dframe_step['run_domain_reference'].values[0].lower() == domain_name_step.lower():

                    # get run domain information to add in the bulletin
                    run_view_warn_step = exec_dframe_step['view_warnings'].values[0]
                    run_view_exec_step = exec_dframe_step['view_execution'].values[0]

                    if domain_name_step not in list(file_obj_src_ref_start.keys()):
                        file_obj_src_ref_start[domain_name_step] = {}
                    if domain_name_step not in list(file_obj_src_ref_end.keys()):
                        file_obj_src_ref_end[domain_name_step] = {}

                    section_name_list = self.section_name_obj[domain_name_step]
                    section_catchment_list = self.section_catchment_obj[domain_name_step]

                    file_extra_variables = dict(zip(self.exec_type_list, exec_fields))
                    file_extra_variables['domain_name'] = domain_name_step
                    file_extra_collections = {self.tag_section_catchment: section_catchment_list,
                                              self.tag_section_name: section_name_list}

                    file_list_src_ref_start = self.define_file_string(
                            None, os.path.join(folder_name_src_ref_start, file_name_src_ref_start),
                            file_extra_variables=file_extra_variables, file_extra_collections=file_extra_collections)
                    file_list_src_ref_start = self.filter_file_string(file_list_src_ref_start)

                    file_list_src_ref_end = self.define_file_string(
                            None, os.path.join(folder_name_src_ref_end, file_name_src_ref_end),
                            file_extra_variables=file_extra_variables, file_extra_collections=file_extra_collections)
                    file_list_src_ref_end = self.filter_file_string(file_list_src_ref_end)

                    file_obj_src_ref_start[domain_name_step][exec_name] = file_list_src_ref_start
                    file_obj_src_ref_end[domain_name_step][exec_name] = file_list_src_ref_end

                    if domain_name_step not in list(exec_name_obj.keys()):
                        exec_name_obj[domain_name_step] = [exec_name]
                    else:
                        tmp_exec = exec_name_obj[domain_name_step]
                        tmp_exec.append(exec_name)
                        exec_name_obj[domain_name_step] = tmp_exec

                    if domain_name_step not in list(view_warn_obj.keys()):
                        view_warn_obj[domain_name_step] = [run_view_warn_step]
                    else:
                        run_view_warn_tmp = view_warn_obj[domain_name_step]
                        run_view_warn_tmp.append(run_view_warn_step)
                        view_warn_obj[domain_name_step] = run_view_warn_tmp
                    if domain_name_step not in list(view_exec_obj.keys()):
                        view_exec_obj[domain_name_step] = [run_view_exec_step]
                    else:
                        run_view_exec_tmp = view_exec_obj[domain_name_step]
                        run_view_exec_tmp.append(run_view_exec_step)
                        view_exec_obj[domain_name_step] = run_view_exec_tmp

        self.file_obj_src_ref_start = file_obj_src_ref_start
        self.file_obj_src_ref_end = file_obj_src_ref_end

        # ancillary folder(s) and file(s)
        self.folder_name_anc_source = anc_dict[self.tag_anc_source][self.folder_name_tag]
        self.file_name_anc_source = anc_dict[self.tag_anc_source][self.file_name_tag]
        self.folder_name_anc_analysis = anc_dict[self.tag_anc_analysis][self.folder_name_tag]
        self.file_name_anc_analysis = anc_dict[self.tag_anc_analysis][self.file_name_tag]
        self.folder_name_anc_destination = anc_dict[self.tag_anc_destination][self.folder_name_tag]
        self.file_name_anc_destination = anc_dict[self.tag_anc_destination][self.file_name_tag]

        # destination folder(s), file(s) and status
        self.folder_name_dest_summary = dest_dict[self.tag_dest_summary][self.folder_name_tag]
        self.file_name_dest_summary = dest_dict[self.tag_dest_summary][self.file_name_tag]
        if self.status_active_tag in list(dest_dict[self.tag_dest_summary].keys()):
            self.status_dest_summary = dest_dict[self.tag_dest_summary][self.status_active_tag]
        else:
            self.status_dest_summary = True
        self.folder_name_dest_warn_max = dest_dict[self.tag_dest_warnings_maximum][self.folder_name_tag]
        self.file_name_dest_warn_max = dest_dict[self.tag_dest_warnings_maximum][self.file_name_tag]
        if self.status_active_tag in list(dest_dict[self.tag_dest_warnings_maximum].keys()):
            self.status_dest_warn_max = dest_dict[self.tag_dest_warnings_maximum][self.status_active_tag]
        else:
            self.status_dest_warn_max = True
        self.folder_name_dest_warn_daily = dest_dict[self.tag_dest_warnings_daily][self.folder_name_tag]
        self.file_name_dest_warn_daily = dest_dict[self.tag_dest_warnings_daily][self.file_name_tag]
        if self.status_active_tag in list(dest_dict[self.tag_dest_warnings_daily].keys()):
            self.status_dest_warn_daily = dest_dict[self.tag_dest_warnings_daily][self.status_active_tag]
        else:
            self.status_dest_warn_daily = True

        self.exec_name_obj = exec_name_obj
        self.view_warn_obj = view_warn_obj
        self.view_exec_obj = view_exec_obj

        # define file ancillary reference
        self.file_path_anc_source = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_anc_source, self.file_name_anc_source),
            file_extra_variables=None, file_extra_collections=None)
        self.file_path_anc_analysis = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_anc_analysis, self.file_name_anc_analysis),
            file_extra_variables=None, file_extra_collections=None)
        self.file_path_anc_destination = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_anc_destination, self.file_name_anc_destination),
            file_extra_variables=None, file_extra_collections=None)

        # define file destination reference
        self.file_path_dest_summary = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_dest_summary, self.file_name_dest_summary),
            file_extra_variables=None, file_extra_collections=None)
        self.file_path_dest_warn_max = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_dest_warn_max, self.file_name_dest_warn_max),
            file_extra_variables=None, file_extra_collections=None)
        self.file_path_dest_warn_daily = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_dest_warn_daily, self.file_name_dest_warn_daily),
            file_extra_variables=None, file_extra_collections=None)

        # define time boundaries to select analysis period
        self.time_select_start = define_time_boundaries(
            self.time_run, time_period=self.time_window_left,
            time_frequency=self.time_frequency, time_direction='left', time_index='first')
        self.time_select_end = define_time_boundaries(
            self.time_run, time_period=self.time_window_right,
            time_frequency=self.time_frequency, time_direction='right', time_index='last')

        # flags
        self.flag_cleaning_dynamic_source = flag_cleaning_dynamic_source
        self.flag_cleaning_dynamic_analysis = flag_cleaning_dynamic_analysis
        self.flag_cleaning_dynamic_destination = flag_cleaning_dynamic_destination
        self.flag_cleaning_dynamic_tmp = flag_cleaning_dynamic_tmp

        # tags
        self.tag_time_period = 'time_period'
        self.tag_time_frequency = 'time_frequency'
        self.tag_time_rounding = 'time_rounding'
        self.tag_run_description = 'run_description'
        self.tag_run_var_sim = 'run_variable_sim'
        self.tag_run_var_obs = 'run_variable_obs'

        self.tag_run_ref_start = 'run_start'
        self.tag_run_ref_end = 'run_end'
        self.tag_run_ref_elapsed = 'run_elapsed'
        self.tag_run_datasets_section = 'run_datasets_section'
        self.tag_run_datasets_attrs = 'run_datasets_attrs'
        self.tag_run_n = 'run_n'
        self.tag_section_n = 'section_n'
        self.tag_run_type = 'run_type'

        self.tag_summary_alert_value = 'alert_value'
        self.tag_summary_alert_index = 'alert_index'
        self.tag_summary_alert_section = 'alert_section'
        self.tag_summary_alert_thr = 'alert_thr'
        self.tag_summary_alert_run = 'alert_run'
        self.tag_summary_alarm_value = 'alarm_value'
        self.tag_summary_alarm_index = 'alarm_index'
        self.tag_summary_alarm_section = 'alarm_section'
        self.tag_summary_alarm_thr = 'alarm_thr'
        self.tag_summary_alarm_run = 'alarm_run'
        self.tag_summary_run_name = 'run_name'
        self.tag_summary_run_description = 'run_description'

        self.tag_info = 'info'
        self.tag_data = 'data'
        self.tag_time_ref_start = 'time_start'
        self.tag_time_ref_end = 'time_end'

        self.tag_file_time_reference = 'time_modified'

        self.tag_bulletin_info = 'bulletin_info'
        self.tag_bulletin_thr = 'bulletin_thr'
        self.tag_bulletin_sections_generic = 'bulletin_sections_generic'
        self.tag_bulletin_sections_max = 'bulletin_sections_max'
        self.tag_bulletin_sections_today = 'bulletin_sections_today'
        self.tag_bulletin_sections_tomorrow = 'bulletin_sections_tomorrow'
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to filter file string
    @staticmethod
    def filter_file_string(file_list_src):
        file_list_filter = []
        for file_list_step in file_list_src:
            if file_list_step not in file_list_filter:
                file_list_filter.append(file_list_step)
        return file_list_filter
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to merge data by key
    @staticmethod
    def merge_data_by_key(obj_data_in_1, obj_data_in_2, obj_data_separator=':', obj_data_case='lower'):
        obj_data_out = {}
        for (obj_key_1, obj_list_1), (obj_key_2, obj_list_2) in zip(obj_data_in_1.items(), obj_data_in_2.items()):
            assert obj_key_1 == obj_key_2, 'obj key is not the same, impossible to merge the lists'

            if obj_data_case == 'lower':
                obj_list_out = [obj_data_separator.join([b.lower(), s.lower()]) for b, s in zip(obj_list_1, obj_list_2)]
            elif obj_data_case == 'upper':
                obj_list_out = [obj_data_separator.join([b.upper(), s.upper()]) for b, s in zip(obj_list_1, obj_list_2)]
            else:
                obj_list_out = [obj_data_separator.join([b, s]) for b, s in zip(obj_list_1, obj_list_2)]

            obj_data_out[obj_key_1] = obj_list_out
        return obj_data_out
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to filter data by key
    @staticmethod
    def filter_data_by_key(dframe_data, key_value, key_column='domain_name'):

        obj_data = {}
        if not isinstance(key_value, list):
            key_value = [key_value]

        for key_step in key_value:

            key_selection = key_step.lower()
            dframe_data['tag_selection'] = dframe_data[key_column].str.lower()
            dframe_step = dframe_data[dframe_data['tag_selection'] == key_selection]
            # dframe_step.pop('domain_selection')

            if not dframe_step.empty:
                key_dataframe = dframe_step[key_column].values[0]
                if dframe_step[key_column].values[0] != key_step:
                    log_stream.warning(' ===> Select DataFrame rows is returned by defining lower case keys.'
                                       ' Key value in the dataframe "' + key_dataframe +
                                       '" and key selection "' + key_step +
                                       '" are different.')
            else:
                log_stream.warning(' ===> Select DataFrame rows by value returned empty DataFrame')

            obj_data[key_step] = dframe_step

        return obj_data
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to extract data by key
    @staticmethod
    def extract_data_by_key(obj_data_in, key_column=None):

        if key_column is None:
            key_column = 'section_catchment'

        obj_data_out = {}
        for obj_key_tmp, obj_dframe_tmp in obj_data_in.items():
            obj_data_tmp = obj_dframe_tmp[key_column].values.tolist()
            obj_data_out[obj_key_tmp] = obj_data_tmp
        return obj_data_out
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define time period search
    @staticmethod
    def define_time_search(time_step, time_period=1, time_frequency='H', time_rounding='H', time_reverse=False):

        time_step = time_step.floor(time_rounding)
        time_range = pd.date_range(end=time_step, periods=time_period, freq=time_frequency)

        if time_reverse:
            time_range = time_range[::-1]

        return time_range
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define filename
    def define_file_string(self, time, file_path_raw,
                           file_extra_variables=None, file_extra_collections=None):

        if file_extra_variables is None:
            file_extra_variables = {}
        if file_extra_collections is None:
            file_extra_collections = None

        alg_template_tags = self.alg_template_tags

        if file_extra_collections is not None:
            if 'basin_name' not in list(file_extra_collections.keys()):
                if 'section_catchment' in list(file_extra_collections.keys()):
                    file_extra_collections['basin_name'] = deepcopy(file_extra_collections['section_catchment'])

        alg_template_values_raw = {
            'source_datetime': time,
            'source_sub_path_time': time,
            'ancillary_datetime': time,
            'ancillary_sub_path_time': time,
            'destination_datetime': time,
            'destination_sub_path_time': time,
            'run_name': None,
            'run_sub_path_datasets': None,
            'run_sub_path_execution': None,
            'domain_name': None,
            'section_name': None,
            'basin_name': None
        }

        if file_extra_collections is not None:
            file_n = None
            file_values_list = []
            for id_values, file_values in enumerate(file_extra_collections.values()):
                if file_n is None:
                    file_n = file_values.__len__()
                file_values_list.append(file_values)
            file_keys_list = []
            for id_key, file_key in enumerate(file_extra_collections.keys()):
                file_keys_list.append([file_key] * file_n)

            file_collections = {}
            for file_id, (file_keys_step, file_values_step) in enumerate(zip(file_keys_list, file_values_list)):
                for id, (key_step, value_step) in enumerate(zip(file_keys_step, file_values_step)):
                    if id not in list(file_collections.keys()):
                        file_collections[id] = [key_step, value_step]
                    else:
                        list_tmp = file_collections[id]
                        list_tmp.extend([key_step, value_step])
                        file_collections[id] = list_tmp

            file_path_obj = []
            for file_fields in file_collections.values():
                file_keys = file_fields[0::2]
                file_values = file_fields[1::2]

                alg_template_values_def = deepcopy(alg_template_values_raw)
                for file_key, file_value in zip(file_keys, file_values):
                    alg_template_values_def[file_key] = file_value

                alg_template_values = {**alg_template_values_def, **file_extra_variables}

                file_path_def = fill_tags2string(file_path_raw, alg_template_tags, alg_template_values)
                file_path_obj.append(file_path_def)
        else:

            file_path_obj = fill_tags2string(file_path_raw, alg_template_tags, alg_template_values_raw)

        return file_path_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean dynamic tmp
    def clean_dynamic_tmp(self):

        flag_cleaning_tmp = self.flag_cleaning_dynamic_tmp

        file_path_anc_source = self.file_path_anc_source
        file_path_anc_analysis = self.file_path_anc_analysis
        file_path_anc_destination = self.file_path_anc_destination

        file_path_anc_list = [file_path_anc_source, file_path_anc_analysis, file_path_anc_destination]
        if flag_cleaning_tmp:
            for file_path_anc_step in file_path_anc_list:
                if os.path.exists(file_path_anc_step):
                    os.remove(file_path_anc_step)

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to dump dynamic data
    def dump_dynamic_data(self, analysis_datasets_collections,
                          time_last_run_datasets_collections, time_period_datasets_collections):

        # get reference time(s)
        time_exec, time_run, time_mode = self.time_exec, self.time_run, self.time_mode
        # get bulletin title
        title_name = self.title_name

        # get domain list
        domain_name_list = self.domain_name_list
        # get execution and view object(s)
        exec_name_obj = self.exec_name_obj
        view_warn_obj, view_exec_obj = self.view_warn_obj, self.view_exec_obj

        # get execution and section dataframe(s)
        exec_dframe = self.exec_dframe
        sections_dframe = self.sections_dframe

        # get ancillary and destination file
        file_path_anc = self.file_path_anc_destination
        file_path_dest_summary = self.file_path_dest_summary
        file_path_dest_warn_max = self.file_path_dest_warn_max
        file_path_dest_warn_daily = self.file_path_dest_warn_daily

        # get status destination file
        status_dest_summary = self.status_dest_summary
        status_dest_warn_max, status_dest_warn_daily = self.status_dest_warn_max, self.status_dest_warn_daily

        # get ancillary flag
        flag_clean_anc = self.flag_cleaning_dynamic_destination

        # info time start
        log_stream.info(' ---> Dump dynamic datasets [' + str(time_run) + '] ... ')

        # check ancillary flag and file
        if flag_clean_anc:
            if os.path.exists(file_path_anc):
                os.remove(file_path_anc)

        # organize bulletin start
        log_stream.info(' ----> Organize summary bulletin  ... ')

        # check ancillary file
        if not os.path.exists(file_path_anc):

            # iterate over domains list
            summary_collections = {}
            for domain_name_step in domain_name_list:

                # info domain start
                log_stream.info(' -----> Domain reference "' + domain_name_step + '" ... ')

                # get analysis and time collections
                analysis_datasets_domain = analysis_datasets_collections[domain_name_step]
                time_last_datasets_domain = time_last_run_datasets_collections[domain_name_step]
                time_period_datasets_domain = time_period_datasets_collections[domain_name_step]

                # get exec list (checking the domain availability in the execution obj)
                if domain_name_step in list(exec_name_obj.keys()):
                    exec_name_list = exec_name_obj[domain_name_step]
                else:
                    log_stream.error(' ===> Domain "' + domain_name_step + '" not included in the "exec_name_obj"')
                    raise RuntimeError('Domain must be included in the "exec_name_obj" to correctly get the datasets')
                # get view warn and execution list
                view_warn_list = view_warn_obj[domain_name_step]
                view_exec_list = view_exec_obj[domain_name_step]

                # iterate over executions and view list(s)
                for exec_name_step, view_warn_step, view_exec_step in zip(exec_name_list,
                                                                          view_warn_list, view_exec_list):

                    # info execution start
                    log_stream.info(' ------> Analyze execution reference "' + exec_name_step + '" ... ')

                    # get run data and attributes (1)
                    attrs_exec = exec_dframe[exec_dframe.index == exec_name_step].to_dict('r')[0]
                    run_name = attrs_exec[self.tag_summary_run_name]
                    run_description = attrs_exec[self.tag_summary_run_description]

                    # get time last and period data
                    data_time_last = time_last_datasets_domain[exec_name_step]
                    data_time_period = time_period_datasets_domain[exec_name_step]

                    # compute time last run available
                    time_list = [elem for elem in data_time_last if elem is not None]
                    time_idx = pd.DatetimeIndex(time_list)
                    run_time_last = time_idx.max().ceil(freq='min')

                    # get extend attributes of run (some basic information) (3)
                    attrs_extend = {
                        'domain_name': domain_name_step,
                        'run_time_last': run_time_last,
                        'run_time_period': data_time_period,
                        'view_warnings': view_warn_step, 'view_execution': view_exec_step,
                        self.tag_summary_run_name: run_name, self.tag_summary_run_description: run_description}

                    # get analysis data and attributes (2)
                    data_analysis = analysis_datasets_domain[exec_name_step][self.tag_run_datasets_section]
                    attrs_analysis = analysis_datasets_domain[exec_name_step][self.tag_run_datasets_attrs]

                    # add time attributes to analysis attributes
                    if attrs_analysis is None:
                        attrs_analysis = {}

                    attrs_analysis[self.tag_run_ref_start] = analysis_datasets_domain[exec_name_step][
                        self.tag_run_ref_start]
                    attrs_analysis[self.tag_run_ref_end] = analysis_datasets_domain[exec_name_step][
                        self.tag_run_ref_end]
                    attrs_analysis[self.tag_run_ref_elapsed] = analysis_datasets_domain[exec_name_step][
                        self.tag_run_ref_elapsed]

                    # define datasets attributes
                    attrs_datasets = {**attrs_analysis, **attrs_exec, **attrs_extend}

                    # check analysis availability
                    if data_analysis is not None:

                        summary_datasets = {}
                        for section_name, section_data in data_analysis.items():

                            log_stream.info(' -------> Section "' + section_name + '" ... ')

                            if section_data is not None:
                                for time_step, data_step in section_data.items():

                                    log_stream.info(' --------> Time "' + str(time_step) + '" ... ')

                                    max_alert_value = data_step[self.tag_summary_alert_value]
                                    max_alert_idx = data_step[self.tag_summary_alert_index]
                                    max_alert_run = data_step[self.tag_summary_alert_run]
                                    max_alarm_value = data_step[self.tag_summary_alarm_value]
                                    max_alarm_idx = data_step[self.tag_summary_alarm_index]
                                    max_alarm_run = data_step[self.tag_summary_alarm_run]
                                    thr_alert_value = data_step[self.tag_summary_alert_thr]
                                    thr_alarm_value = data_step[self.tag_summary_alarm_thr]

                                    if max_alert_run is not None and section_name == 'misa:misa':
                                        print('ciao')

                                    if time_step not in list(summary_datasets.keys()):
                                        summary_datasets[time_step] = {}

                                        summary_datasets[time_step][self.tag_summary_alert_value] = [max_alert_value]
                                        summary_datasets[time_step][self.tag_summary_alert_index] = [max_alert_idx]
                                        summary_datasets[time_step][self.tag_summary_alert_run] = [max_alert_run]
                                        summary_datasets[time_step][self.tag_summary_alert_section] = [section_name]
                                        summary_datasets[time_step][self.tag_summary_alert_thr] = [thr_alert_value]

                                        summary_datasets[time_step][self.tag_summary_alarm_value] = [max_alarm_value]
                                        summary_datasets[time_step][self.tag_summary_alarm_index] = [max_alarm_idx]
                                        summary_datasets[time_step][self.tag_summary_alarm_run] = [max_alarm_run]
                                        summary_datasets[time_step][self.tag_summary_alarm_section] = [section_name]
                                        summary_datasets[time_step][self.tag_summary_alarm_thr] = [thr_alarm_value]

                                        summary_datasets[time_step][self.tag_summary_run_name] = [run_name]
                                        summary_datasets[time_step][self.tag_summary_run_description] = [run_description]

                                    else:

                                        tmp_datasets = deepcopy(summary_datasets[time_step])

                                        tmp_alert_value = tmp_datasets[self.tag_summary_alert_value]
                                        tmp_alert_idx = tmp_datasets[self.tag_summary_alert_index]
                                        tmp_alert_run = tmp_datasets[self.tag_summary_alert_run]
                                        tmp_alert_section = tmp_datasets[self.tag_summary_alert_section]
                                        tmp_alert_thr = tmp_datasets[self.tag_summary_alert_thr]

                                        tmp_alert_value.append(max_alert_value)
                                        tmp_alert_idx.append(max_alert_idx)
                                        tmp_alert_run.append(max_alert_run)
                                        tmp_alert_section.append(section_name)
                                        tmp_alert_thr.append(thr_alert_value)

                                        summary_datasets[time_step][self.tag_summary_alert_value] = tmp_alert_value
                                        summary_datasets[time_step][self.tag_summary_alert_index] = tmp_alert_idx
                                        summary_datasets[time_step][self.tag_summary_alert_run] = tmp_alert_run
                                        summary_datasets[time_step][self.tag_summary_alert_section] = tmp_alert_section
                                        summary_datasets[time_step][self.tag_summary_alert_thr] = tmp_alert_thr

                                        tmp_alarm_value = tmp_datasets[self.tag_summary_alarm_value]
                                        tmp_alarm_idx = tmp_datasets[self.tag_summary_alarm_index]
                                        tmp_alarm_run = tmp_datasets[self.tag_summary_alarm_run]
                                        tmp_alarm_section = tmp_datasets[self.tag_summary_alarm_section]
                                        tmp_alarm_thr = tmp_datasets[self.tag_summary_alarm_thr]
                                        tmp_alarm_value.append(max_alarm_value)
                                        tmp_alarm_idx.append(max_alarm_idx)
                                        tmp_alarm_run.append(max_alarm_run)
                                        tmp_alarm_section.append(section_name)
                                        tmp_alarm_thr.append(thr_alarm_value)

                                        summary_datasets[time_step][self.tag_summary_alarm_value] = tmp_alarm_value
                                        summary_datasets[time_step][self.tag_summary_alarm_index] = tmp_alarm_idx
                                        summary_datasets[time_step][self.tag_summary_alarm_run] = tmp_alarm_run
                                        summary_datasets[time_step][self.tag_summary_alarm_section] = tmp_alarm_section
                                        summary_datasets[time_step][self.tag_summary_alarm_thr] = tmp_alarm_thr

                                        tmp_run_name = tmp_datasets[self.tag_summary_run_name]
                                        tmp_run_name.append(run_name)
                                        summary_datasets[time_step][self.tag_summary_run_name] = tmp_run_name

                                        tmp_run_description = tmp_datasets[self.tag_summary_run_description]
                                        tmp_run_description.append(run_description)
                                        summary_datasets[time_step][self.tag_summary_run_description] = tmp_run_description

                                    log_stream.info(' --------> Time "' + str(time_step) + '" ... DONE')

                                log_stream.info(' -------> Section "' + section_name + '" ... DONE')

                            else:
                                log_stream.info(' -------> Section "' + section_name +
                                                '" ... SKIPPED. Datasets are undefined')

                            # info execution end
                            log_stream.info(' ------> Analyze execution reference "' +
                                            exec_name_step + '" ... DONE')

                    else:
                        # info execution end
                        log_stream.info(' ------> Analyze execution reference "' + exec_name_step +
                                        '" ... SKIPPED. All datasets are undefined')
                        summary_datasets = None

                    # add information to summary collections start
                    log_stream.info(' ------> Organize execution reference "' + exec_name_step + '" ... ')
                    if exec_name_step not in list(summary_collections.keys()):

                        # set datasets to the summary collections
                        summary_collections[exec_name_step] = {}

                        summary_collections[exec_name_step][self.tag_data] = {}
                        summary_collections[exec_name_step][self.tag_data] = summary_datasets
                        summary_collections[exec_name_step][self.tag_info] = {}
                        summary_collections[exec_name_step][self.tag_info] = init_bulletin_attrs(attrs_datasets)

                    else:
                        # merge datasets with the previously saved in the summary collections
                        tmp_datasets = summary_collections[exec_name_step][self.tag_data]
                        tmp_attrs = summary_collections[exec_name_step][self.tag_info]

                        # check the datasets
                        if tmp_datasets is None:
                            summary_collections[exec_name_step][self.tag_data] = summary_datasets
                        else:
                            summary_merged = merge_bulletin_datasets(summary_datasets, tmp_datasets)
                            summary_collections[exec_name_step][self.tag_data] = summary_merged

                        if tmp_attrs is None:
                            summary_collections[exec_name_step][self.tag_info] = init_bulletin_attrs(attrs_datasets)
                        else:
                            attrs_merged = merge_bulletin_attrs(init_bulletin_attrs(attrs_datasets), tmp_attrs)
                            summary_collections[exec_name_step][self.tag_info] = attrs_merged

                        # add information to summary collections start
                        log_stream.info(' ------> Organize execution reference "' + exec_name_step + '" ... DONE')

                # info domain end
                log_stream.info(' -----> Domain reference "' + domain_name_step + '" ... DONE')

            # organize bulletin end
            log_stream.info(' ----> Organize summary bulletin ... DONE')

            # organize bulletin info
            log_stream.info(' ----> Organize info bulletin  ... ')
            bulletin_dframe_info, bulletin_dframe_thr = organize_bulletin_info(exec_name_obj, summary_collections)
            log_stream.info(' ----> Organize info bulletin  ... DONE')

            # organize bulletin thr generic
            log_stream.info(' ----> Organize section bulletin generic ... ')
            bulletin_dframe_sections_generic = organize_bulletin_warnings_generic(
                exec_name_obj, summary_collections, sections_dframe)
            log_stream.info(' ----> Organize section bulletin generic ... DONE')

            # organize bulletin thr max
            log_stream.info(' ----> Organize section bulletin maximum ... ')
            bulletin_dframe_sections_max = organize_bulletin_warnings_section(
                bulletin_dframe_sections_generic, sections_dframe)
            log_stream.info(' ----> Organize section bulletin maximum ... DONE')

            # organize bulletin thr today
            log_stream.info(' ----> Organize section bulletin today ... ')
            bulletin_dframe_sections_today = select_bulletin_time(
                time_run, bulletin_dframe_sections_generic, time_mode='today')
            bulletin_dframe_today = organize_bulletin_warnings_section(
                bulletin_dframe_sections_today, sections_dframe)
            log_stream.info(' ----> Organize section bulletin today ... DONE')

            # organize bulletin thr tomorrow
            log_stream.info(' ----> Organize section bulletin tomorrow ... ')
            bulletin_dframe_sections_tomorrow = select_bulletin_time(
                time_run, bulletin_dframe_sections_generic, time_mode='tomorrow')
            bulletin_dframe_tomorrow = organize_bulletin_warnings_section(
                bulletin_dframe_sections_tomorrow, sections_dframe)
            log_stream.info(' ----> Organize section bulletin tomorrow ... DONE')

            # save datasets to ancillary file
            folder_name_anc, file_name_anc = os.path.split(file_path_anc)
            make_folder(folder_name_anc)

            bulletin_collections = {
                self.tag_bulletin_info: bulletin_dframe_info,
                self.tag_bulletin_thr: bulletin_dframe_thr,
                self.tag_bulletin_sections_generic: bulletin_dframe_sections_generic,
                self.tag_bulletin_sections_max: bulletin_dframe_sections_max,
                self.tag_bulletin_sections_today: bulletin_dframe_today,
                self.tag_bulletin_sections_tomorrow: bulletin_dframe_tomorrow}

            write_obj(file_path_anc, bulletin_collections)

        else:
            # read datasets from ancillary file
            bulletin_collections = read_obj(file_path_anc)
            bulletin_dframe_info = bulletin_collections[self.tag_bulletin_info]
            bulletin_dframe_thr = bulletin_collections[self.tag_bulletin_thr]
            bulletin_dframe_sections_generic = bulletin_collections[self.tag_bulletin_sections_generic]
            bulletin_dframe_sections_max = bulletin_collections[self.tag_bulletin_sections_max]
            bulletin_dframe_sections_today = bulletin_collections[self.tag_bulletin_sections_today]
            bulletin_dframe_sections_tomorrow = bulletin_collections[self.tag_bulletin_sections_tomorrow]

        # save bulletin summary
        log_stream.info(' ----> Save bulletin summary' + file_path_dest_summary + ' ... ')
        if status_dest_summary:
            folder_name_dest_summary, file_name_dest_summary = os.path.split(file_path_dest_summary)
            make_folder(folder_name_dest_summary)

            write_bulletin_summary(
                time_run, time_exec, time_mode=time_mode, time_format='%Y-%m-%d %H:%M',
                file_name=file_path_dest_summary,
                bulletin_dframe_info=bulletin_dframe_info,
                bulletin_dframe_thr=bulletin_dframe_thr,
                tag_op_chain=title_name)

            log_stream.info(' ----> Save bulletin summary ' + file_path_dest_summary + ' ... DONE')
        else:
            log_stream.info(' ----> Save bulletin summary ' + file_path_dest_summary +
                            ' ... SKIPPED. File is not activated')

        # save bulletin warnings max
        log_stream.info(' ----> Save bulletin warnings max ' + file_path_dest_warn_max + ' ... ')
        if status_dest_warn_max:
            folder_name_dest_warn_max, file_name_dest_warn_max = os.path.split(file_path_dest_warn_max)
            make_folder(folder_name_dest_warn_max)

            write_bulletin_warn_xml(
                time_run, time_exec,
                file_name=file_path_dest_warn_max,
                bulletin_dframe=bulletin_dframe_sections_max, sections_dframe=sections_dframe)

            log_stream.info(' ----> Save bulletin warnings max ' + file_path_dest_warn_max + ' ... DONE')
        else:
            log_stream.info(' ----> Save bulletin warnings max ' + file_path_dest_warn_max +
                            ' ... SKIPPED. File is not activated')

        # save bulletin warnings daily
        log_stream.info(' ----> Save bulletin warnings daily ' + file_path_dest_warn_daily + ' ... ')
        if status_dest_warn_daily:
            folder_name_dest_warn_daily, file_name_dest_warn_daily = os.path.split(file_path_dest_warn_daily)
            make_folder(folder_name_dest_warn_daily)

            write_bulletin_warn_csv(
                time_run, time_exec,
                file_name=file_path_dest_warn_daily,
                bulletin_dframe_today=bulletin_dframe_sections_today,
                bulletin_dframe_tomorrow=bulletin_dframe_sections_tomorrow,
                sections_dframe=sections_dframe)

            log_stream.info(' ----> Save bulletin warnings daily ' + file_path_dest_warn_daily + ' ... DONE')
        else:
            log_stream.info(' ----> Save bulletin warnings daily ' + file_path_dest_warn_daily +
                            ' ... SKIPPED. File is not activated')

        # info time end
        log_stream.info(' ---> Dump dynamic datasets [' + str(time_run) + '] ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to analyze dynamic data
    def analyze_dynamic_data(self, file_workspace):

        # get reference time(s)
        time = self.time_run
        time_select_start, time_select_end = self.time_select_start, self.time_select_end

        # get domain list
        domain_name_list = self.domain_name_list
        # get execution and view object(s)
        exec_name_obj = self.exec_name_obj
        view_warn_obj, view_exec_obj = self.view_warn_obj, self.view_exec_obj

        # get execution dataframe
        exec_dframe = self.exec_dframe
        # get ancillary object(s)
        file_path_anc = self.file_path_anc_analysis
        flag_clean_anc = self.flag_cleaning_dynamic_analysis

        # info routine start
        log_stream.info(' ---> Analyze dynamic datasets [' + str(time) + '] ... ')

        # check ancillary flag and file
        if flag_clean_anc:
            if os.path.exists(file_path_anc):
                os.remove(file_path_anc)

        # check ancillary file
        if not os.path.exists(file_path_anc):

            # cycles over domain name(s)
            analyze_warnings_collections, analyze_datasets_collections = {}, {}
            for domain_name_step in domain_name_list:

                # info domain start
                log_stream.info(' ----> Domain reference "' + domain_name_step + '" ... ')

                # get file information for selected domain
                domain_workspace = file_workspace[domain_name_step]

                # get exec list (checking the domain availability in the execution obj)
                if domain_name_step in list(exec_name_obj.keys()):
                    exec_name_list = exec_name_obj[domain_name_step]
                else:
                    log_stream.error(' ===> Domain "' + domain_name_step + '" not included in the "exec_name_obj"')
                    raise RuntimeError('Domain must be included in the "exec_name_obj" to correctly get the datasets')
                # get view warn list
                view_warn_list = view_warn_obj[domain_name_step]

                # init workspace using domain tag
                if analyze_warnings_collections is None:
                    analyze_warnings_collections = {}
                analyze_warnings_collections[domain_name_step] = {}
                if analyze_datasets_collections is None:
                    analyze_datasets_collections = {}
                analyze_datasets_collections[domain_name_step] = {}

                # cycles over execution name(s) and view option(s)
                for exec_name_step, view_warn_step in zip(exec_name_list, view_warn_list):

                    # info execution start
                    log_stream.info(' ----> Execution reference "' + exec_name_step + '" ... ')

                    exec_data = exec_dframe[exec_dframe.index == exec_name_step]
                    exec_run_var_sim = exec_data[self.tag_run_var_sim].values[0]
                    exec_run_var_obs = exec_data[self.tag_run_var_obs].values[0]

                    analyze_datasets_collections[domain_name_step][exec_name_step] = {}
                    if exec_name_step in list(domain_workspace.keys()):

                        exec_workspace = domain_workspace[exec_name_step]

                        exec_info_collection = deepcopy(exec_workspace[self.tag_info])
                        exec_data_collection = deepcopy(exec_workspace[self.tag_data])

                        if (exec_info_collection[self.tag_run_ref_start] is not None) and \
                                (exec_info_collection[self.tag_run_ref_start] is not None):

                            analysis_time_reference_start, analysis_time_reference_end, \
                                analysis_time_reference_elapsed = analyze_time_info(
                                    exec_info_collection[self.tag_run_ref_start],
                                    exec_info_collection[self.tag_run_ref_end],
                                    tag_file_reference=self.tag_file_time_reference)

                            analysis_datasets_section, attrs_datasets_section = analyze_discharge_ts(
                                    exec_name_step, exec_data_collection,
                                    time_start=time_select_start, time_end=time_select_end,
                                    tag_discharge_observed=exec_run_var_obs,
                                    tag_discharge_simulated=exec_run_var_sim,
                                    tag_discharge_thr_alert=self.tag_summary_alert_thr,
                                    tag_discharge_thr_alarm=self.tag_summary_alarm_thr,
                                    tag_discharge_max_alert_value=self.tag_summary_alert_value,
                                    tag_discharge_max_alert_index=self.tag_summary_alert_index,
                                    tag_discharge_max_alert_run=self.tag_summary_alert_run,
                                    tag_discharge_max_alarm_value=self.tag_summary_alarm_value,
                                    tag_discharge_max_alarm_index=self.tag_summary_alarm_index,
                                    tag_discharge_max_alarm_run=self.tag_summary_alarm_run,
                                    tag_run_n=self.tag_run_n, tag_section_n=self.tag_section_n)

                            # info execution end (done)
                            log_stream.info(' ----> Execution reference "' + exec_name_step + '" ... DONE')
                        else:
                            # info execution end (datasets are null)
                            analysis_time_reference_start, analysis_time_reference_end = None, None
                            analysis_time_reference_elapsed, attrs_datasets_section = None, None
                            analysis_datasets_section = None
                            log_stream.info(' ----> Execution reference "' + exec_name_step + '" ... SKIPPED. '
                                            'Execution datasets are null')
                    else:
                        # info execution end (execution not available)
                        analysis_time_reference_start, analysis_time_reference_end = None, None
                        analysis_time_reference_elapsed, attrs_datasets_section = None, None
                        analysis_datasets_section = None
                        log_stream.info(' ----> Execution reference "' + exec_name_step +
                                        '" ... SKIPPED. Execution not available')

                    # organize common workspace
                    analyze_datasets_collections[domain_name_step][exec_name_step][self.tag_run_ref_start] = analysis_time_reference_start
                    analyze_datasets_collections[domain_name_step][exec_name_step][self.tag_run_ref_end] = analysis_time_reference_end
                    analyze_datasets_collections[domain_name_step][exec_name_step][self.tag_run_ref_elapsed] = analysis_time_reference_elapsed
                    analyze_datasets_collections[domain_name_step][exec_name_step][self.tag_run_datasets_section] = analysis_datasets_section
                    analyze_datasets_collections[domain_name_step][exec_name_step][self.tag_run_datasets_attrs] = attrs_datasets_section

                # info domain end
                log_stream.info(' ----> Domain reference "' + domain_name_step + '" ... DONE')

            # dump ancillary obj to file
            folder_name_anc, file_name_anc = os.path.split(file_path_anc)
            make_folder(folder_name_anc)

            analyze_collections = {self.tag_data: analyze_datasets_collections}
            write_obj(file_path_anc, analyze_collections)

        else:
            # get ancillary obj from file
            analyze_collections = read_obj(file_path_anc)
            analyze_datasets_collections = analyze_collections[self.tag_data]

        # info routine end
        log_stream.info(' ---> Analyze dynamic datasets [' + str(time) + '] ... DONE')

        return analyze_datasets_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize dynamic data
    def organize_dynamic_data(self):

        # get reference time(s)
        time = self.time_run

        # get domain list
        domain_name_list = self.domain_name_list
        # get execution and view object(s)
        exec_name_obj = self.exec_name_obj
        view_warn_obj, view_exec_obj = self.view_warn_obj, self.view_exec_obj
        # get outlet obj
        outlet_name_obj = self.outlet_name_obj
        # execution dframe
        exec_dframe = self.exec_dframe

        # get source obj
        file_obj_src_ref_start = self.file_obj_src_ref_start
        file_obj_src_ref_end = self.file_obj_src_ref_end
        # get ancillary obj
        file_path_anc = self.file_path_anc_source
        flag_clean_anc = self.flag_cleaning_dynamic_source

        # info routine start
        log_stream.info(' ---> Organize dynamic datasets [' + str(time) + '] ... ')

        # check ancillary flag and file
        if flag_clean_anc:
            if os.path.exists(file_path_anc):
                os.remove(file_path_anc)

        # check ancillary file
        if not os.path.exists(file_path_anc):

            # cycles over domain name(s)
            file_workspace, history_time_last_workspace, history_time_period_workspace = None, None, None
            for domain_name_step in domain_name_list:

                # info domain start
                log_stream.info(' ----> Domain reference "' + domain_name_step + '" ... ')

                # get domain information
                outlet_name_list = outlet_name_obj[domain_name_step]
                file_collections_src_ref_start = file_obj_src_ref_start[domain_name_step]
                file_collections_src_ref_end = file_obj_src_ref_end[domain_name_step]

                # check domain availability in the execution obj
                if domain_name_step in list(exec_name_obj.keys()):
                    exec_name_list = exec_name_obj[domain_name_step]
                else:
                    log_stream.error(' ===> Domain "' + domain_name_step + '" not included in the "exec_name_obj"')
                    raise RuntimeError('Domain must be included in the "exec_name_obj" to correctly get the datasets')

                # init file workspace using domain tag
                if file_workspace is None:
                    file_workspace = {}
                file_workspace[domain_name_step] = {}
                # init history workspace using domain tag
                if history_time_last_workspace is None:
                    history_time_last_workspace = {}
                history_time_last_workspace[domain_name_step] = {}
                if history_time_period_workspace is None:
                    history_time_period_workspace = {}
                history_time_period_workspace[domain_name_step] = {}

                # cycles over execution name(s)
                for exec_name_step in exec_name_list:

                    # info execution start
                    log_stream.info(' -----> Execution reference "' + exec_name_step + '" ... ')

                    file_path_src_ref_start = file_collections_src_ref_start[exec_name_step]
                    file_path_src_ref_end = file_collections_src_ref_end[exec_name_step]

                    exec_data = exec_dframe[exec_dframe.index == exec_name_step]
                    exec_time_period = exec_data[self.tag_time_period].values[0]
                    exec_time_frequency = exec_data[self.tag_time_frequency].values[0]
                    exec_time_rounding = exec_data[self.tag_time_rounding].values[0]

                    time_search = self.define_time_search(
                        time, time_period=exec_time_period, time_frequency=exec_time_frequency,
                        time_rounding=exec_time_rounding, time_reverse=True)

                    # initialize file workspace
                    file_workspace[domain_name_step][exec_name_step] = {}
                    file_workspace[domain_name_step][exec_name_step][self.tag_info] = {}
                    file_workspace[domain_name_step][exec_name_step][self.tag_data] = {}
                    file_workspace[domain_name_step][exec_name_step][self.tag_info][self.tag_run_ref_start] = None
                    file_workspace[domain_name_step][exec_name_step][self.tag_info][self.tag_time_ref_start] = None
                    file_workspace[domain_name_step][exec_name_step][self.tag_info][self.tag_run_ref_end] = None
                    file_workspace[domain_name_step][exec_name_step][self.tag_info][self.tag_time_ref_end] = None
                    file_workspace[domain_name_step][exec_name_step][self.tag_data] = None
                    # initialize history workspace
                    history_time_last_workspace[domain_name_step][exec_name_step] = {}
                    history_time_period_workspace[domain_name_step][exec_name_step] = {}

                    # iterate to find actual running experiments
                    for time_step in time_search:

                        # info time start
                        log_stream.info(' ------> Time  "' + str(time_step) + '" ... ')

                        log_stream.info(' -------> Reference run_start datasets ... ')
                        if file_workspace[domain_name_step][exec_name_step]['info']['run_start'] is None:

                            if file_path_src_ref_start.__len__() == 1:

                                file_path_src_start_raw = file_path_src_ref_start[0]
                                file_path_src_start_def = self.define_file_string(time_step, file_path_src_start_raw)

                                if file_path_src_start_def.endswith('.x'):
                                    if os.path.exists(file_path_src_start_def):
                                        file_info_start = read_file_execution_info(file_path_src_start_def)
                                    else:
                                        file_info_start = None
                                elif file_path_src_start_def.endswith('.txt'):
                                    if os.path.exists(file_path_src_start_def):
                                        file_info_start = read_file_execution_info(file_path_src_start_def)
                                    else:
                                        file_info_start = None
                                else:
                                    log_stream.error(' ===> Reference run_start datasets ... FAILED')
                                    raise NotImplementedError('Case not implemented in source reference type start')

                                file_check_start = all(elem is None for elem in list([file_info_start]))
                                if file_check_start:
                                    file_insert_start = False
                                    log_stream.info(' -------> Reference run_start datasets ... SKIPPED. '
                                                    'Some Datasets are not defined')
                                else:
                                    file_insert_start = True
                                    log_stream.info(' -------> Reference run_start datasets ... DONE')
                            else:
                                file_info_start, file_insert_start = None, False
                                log_stream.info(' -------> Reference run_start datasets ... SKIPPED. '
                                                'All Datasets are not defined')
                        else:
                            log_stream.info(' -------> Reference run_start datasets ... SKIPPED. '
                                            'Datasets already selected')
                            file_info_start, file_insert_start = None, False

                        log_stream.info(' -------> Reference run_end datasets ... ')
                        if file_workspace[domain_name_step][exec_name_step]['info']['run_end'] is None:

                            file_info_end, file_data_end = {}, {}
                            if file_path_src_ref_end.__len__() >= 1:

                                if file_path_src_ref_end[0].endswith('.json'):

                                    for outlet_name_step, file_path_src_end_raw in zip(outlet_name_list,
                                                                                       file_path_src_ref_end):

                                        file_path_src_end_def = self.define_file_string(
                                            time_step, file_path_src_end_raw)

                                        if os.path.exists(file_path_src_end_def):
                                            file_info_src_ref_end = read_file_hydrograph_info(file_path_src_end_def)
                                            file_data_src_ref_end = read_file_hydrograph_ts(file_path_src_end_def)
                                        else:
                                            file_info_src_ref_end = None
                                            file_data_src_ref_end = None

                                        file_info_end[outlet_name_step] = file_info_src_ref_end
                                        file_data_end[outlet_name_step] = file_data_src_ref_end

                                    file_check_end = all(elem is None for elem in list(file_info_end.values()))
                                    if file_check_end:
                                        file_insert_end = False
                                        log_stream.info(' -------> Reference run_end datasets ... SKIPPED. '
                                                        'Some datasets are not defined')
                                    else:
                                        file_insert_end = True
                                        log_stream.info(' -------> Reference run_end datasets ... DONE')
                                else:
                                    log_stream.error(' ===> Reference run_end datasets ... FAILED')
                                    raise NotImplementedError('Case not implemented in source reference type end')
                            else:

                                file_info_end, file_data_end = None, None
                                file_insert_end = False
                                log_stream.info(' -------> Reference run_end datasets ... SKIPPED. '
                                                'All datasets are not defined')

                        else:
                            log_stream.info(' -------> Reference run_end datasets ... SKIPPED. '
                                            'Datasets already selected')
                            file_info_end, file_data_end, file_insert_end = None, None, False

                        log_stream.info(' -------> Search available datasets ... ')
                        history_time_list = []
                        if file_path_src_ref_end.__len__() >= 1:

                            if file_path_src_ref_end[0].endswith('.json'):

                                for outlet_name_step, file_path_raw in zip(outlet_name_list, file_path_src_ref_end):

                                    file_path_history = self.define_file_string(time_step, file_path_raw)

                                    if os.path.exists(file_path_history):
                                        file_info_history = read_file_hydrograph_info(file_path_history)
                                        time_reference = file_info_history['time_modified']
                                    else:
                                        time_reference = None

                                    history_time_list.append(time_reference)

                                check_history = all(elem is None for elem in history_time_list)
                                if check_history:
                                    history_time_ref = None
                                    log_stream.info(' -------> Search available datasets  ... ALL NOT FOUND')
                                else:
                                    history_time_tmp = [elem for elem in history_time_list if elem is not None]
                                    history_time_idx = pd.DatetimeIndex(history_time_tmp)
                                    history_time_ref = history_time_idx.max().ceil(freq='min')
                                    log_stream.info(' -------> Search available datasets ... DONE')
                            else:
                                log_stream.error(' ===> Search available datasets ... FAILED')
                                raise NotImplementedError('Case not implemented in source reference type end')
                        else:
                            history_time_ref = None
                            log_stream.info(' -------> Search available datasets ... ALL NOT AVAILABLE.')

                        # Store history time last information
                        log_stream.info(' -------> Update history time last information ... ')
                        if not history_time_last_workspace[domain_name_step][exec_name_step]:
                            history_time_last_workspace[domain_name_step][exec_name_step] = [history_time_ref]
                        else:
                            history_time_tmp = history_time_last_workspace[domain_name_step][exec_name_step]
                            history_time_tmp.append(history_time_ref)
                            history_time_last_workspace[domain_name_step][exec_name_step] = history_time_tmp
                        log_stream.info(' -------> Update history time last information ... DONE')
                        # Store history information
                        log_stream.info(' -------> Update history time period information ... ')
                        if not history_time_period_workspace[domain_name_step][exec_name_step]:
                            time_search = sorted(time_search)
                            time_from, time_to = time_search[0], time_search[-1]
                            history_time_period_workspace[domain_name_step][exec_name_step] = [time_from, time_to]
                        log_stream.info(' -------> Update history time period information ... DONE')

                        # Store reference source information and datasets for start step
                        log_stream.info(' -------> Update start process information ... ')
                        if file_insert_start:
                            file_workspace[domain_name_step][exec_name_step][
                                self.tag_info][self.tag_run_ref_start] = file_info_start
                            file_workspace[domain_name_step][exec_name_step][
                                self.tag_info][self.tag_time_ref_start] = time_step
                            log_stream.info(' -------> Update start process information ... DONE')
                        else:
                            log_stream.info(' -------> Update start process information ... SKIPPED. '
                                            'Information are not available')
                        # Store reference source information and datasets for end step
                        log_stream.info(' -------> Update end process information ... ')
                        if file_insert_end:
                            file_workspace[domain_name_step][exec_name_step][
                                self.tag_info][self.tag_run_ref_end] = file_info_end
                            file_workspace[domain_name_step][exec_name_step][
                                self.tag_info][self.tag_time_ref_end] = time_step
                            file_workspace[domain_name_step][exec_name_step][
                                self.tag_data] = file_data_end
                            log_stream.info(' -------> Update end process information ... DONE')
                        else:
                            log_stream.info(' -------> Update end process information ... SKIPPED. '
                                            'Information are not available')

                        # info time end
                        log_stream.info(' ------> Time  "' + str(time_step) + '" ... DONE')

                    # info execution end
                    log_stream.info(' -----> Execution reference "' + exec_name_step + '" ... DONE')

                # info domain end
                log_stream.info(' ----> Domain reference "' + domain_name_step + '" ... DONE')

            # store data in a workspace file
            log_stream.info(' ----> Freeze dynamic datasets ... ')
            if file_workspace is not None:
                folder_name_anc, file_name_anc = os.path.split(file_path_anc)
                make_folder(folder_name_anc)
                # merge file and history workspace
                data_collections = {'file_workspace': file_workspace,
                                    'history_time_last_workspace': history_time_last_workspace,
                                    'history_time_period_workspace': history_time_period_workspace}
                # save data collections
                write_obj(file_path_anc, data_collections)
                log_stream.info(' ----> Freeze dynamic datasets ... DONE')
            else:
                log_stream.info(' ----> Freeze dynamic datasets ... SKIPPED. All datasets are undefined')
        else:
            # get data collections
            data_collections = read_obj(file_path_anc)
            # get file and history workspace
            file_workspace = data_collections['file_workspace']
            history_time_last_workspace = data_collections['history_time_last_workspace']
            history_time_period_workspace = data_collections['history_time_period_workspace']

        # info routine end
        log_stream.info(' ---> Organize dynamic datasets [' + str(time) + '] ... DONE')

        return file_workspace, history_time_last_workspace, history_time_period_workspace

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
