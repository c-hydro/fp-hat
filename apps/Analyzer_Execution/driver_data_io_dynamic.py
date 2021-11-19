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

from lib_utils_io import read_obj, write_obj
from lib_utils_system import fill_tags2string, make_folder

from lib_utils_exec import read_file_execution_info
from lib_data_io_json import read_file_hydrograph_ts, read_file_hydrograph_info
from lib_data_io_html import write_file_summary
from lib_data_io_ascii import write_file_warnings

from lib_data_analysis import analyze_hydrograph_datasets, analyze_time_info

# Debug
# import matplotlib.pylab as plt
######################################################################################


# -------------------------------------------------------------------------------------
# Class DriverDynamic
class DriverDynamic:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, time_now, time_exec, time_run, src_dict, anc_dict, dest_dict, static_data_collection,
                 alg_ancillary=None, alg_template_tags=None,
                 tag_section_data='section_data', tag_execution_data='execution_data',
                 tag_src_reference_start='run_reference_start', tag_src_reference_end='run_reference_end',
                 tag_anc_source='run_source', tag_anc_analysis='run_analysis', tag_anc_destination='run_destination',
                 tag_dest_summary='run_summary', tag_dest_warnings='run_warnings',
                 tag_section_name='section_name', tag_basin_name='basin_name',
                 flag_cleaning_dynamic_source=True, flag_cleaning_dynamic_analysis=True,
                 flag_cleaning_dynamic_destination=True, flag_cleaning_dynamic_tmp=True, string_sep=':'):

        self.time_now = time_now
        self.time_exec = time_exec
        self.time_run = time_run

        self.tag_section_data = tag_section_data
        self.tag_execution_data = tag_execution_data

        self.tag_src_reference_start = tag_src_reference_start
        self.tag_src_reference_end = tag_src_reference_end
        self.tag_anc_source = tag_anc_source
        self.tag_anc_analysis = tag_anc_analysis
        self.tag_anc_destination = tag_anc_destination
        self.tag_dest_summary = tag_dest_summary
        self.tag_dest_warnings = tag_dest_warnings

        self.tag_section_name = tag_section_name
        self.tag_basin_name = tag_basin_name
        self.alg_ancillary = alg_ancillary
        self.alg_template_tags = alg_template_tags

        self.string_sep = string_sep

        self.section_data_collection = static_data_collection[self.tag_section_data]
        self.execution_data_collection = static_data_collection[self.tag_execution_data]

        self.domain_name = self.alg_ancillary['domain_name']

        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'

        self.section_name_list = self.collect_section_list(
            columns_tag_in=['section_name'], columns_tag_out=[self.tag_section_name])[self.tag_section_name]
        self.basin_name_list = self.collect_section_list(
            columns_tag_in=['section_domain'], columns_tag_out=[self.tag_basin_name])[self.tag_basin_name]

        self.outlet_name_list = [self.string_sep.join(
            [b.lower(), s.lower()]) for b, s in zip(self.basin_name_list, self.section_name_list)]

        self.folder_name_src_ref_start = src_dict[self.tag_src_reference_start][self.folder_name_tag]
        self.file_name_src_ref_start = src_dict[self.tag_src_reference_start][self.file_name_tag]
        self.folder_name_src_ref_end = src_dict[self.tag_src_reference_end][self.folder_name_tag]
        self.file_name_src_ref_end = src_dict[self.tag_src_reference_end][self.file_name_tag]

        self.folder_name_anc_source = anc_dict[self.tag_anc_source][self.folder_name_tag]
        self.file_name_anc_source = anc_dict[self.tag_anc_source][self.file_name_tag]
        self.folder_name_anc_analysis = anc_dict[self.tag_anc_analysis][self.folder_name_tag]
        self.file_name_anc_analysis = anc_dict[self.tag_anc_analysis][self.file_name_tag]
        self.folder_name_anc_destination = anc_dict[self.tag_anc_destination][self.folder_name_tag]
        self.file_name_anc_destination = anc_dict[self.tag_anc_destination][self.file_name_tag]

        self.folder_name_dest_summary = dest_dict[self.tag_dest_summary][self.folder_name_tag]
        self.file_name_dest_summary = dest_dict[self.tag_dest_summary][self.file_name_tag]
        self.folder_name_dest_warnings = dest_dict[self.tag_dest_warnings][self.folder_name_tag]
        self.file_name_dest_warnings = dest_dict[self.tag_dest_warnings][self.file_name_tag]

        self.exec_name_list = list(self.execution_data_collection.index)
        self.exec_values_list = list(self.execution_data_collection.values)
        self.exec_type_list = list(self.execution_data_collection.columns)

        file_collections_src_ref_start = {}
        file_collections_src_ref_end = {}
        for exec_name, exec_fields in zip(self.exec_name_list, self.exec_values_list):

            file_extra_variables = {'domain_name': self.domain_name}
            for exec_type_step, exec_field_step in zip(self.exec_type_list, exec_fields):
                file_extra_variables[exec_type_step] = exec_field_step
            file_extra_collections = {self.tag_basin_name: self.basin_name_list, self.tag_section_name: self.section_name_list}

            file_list_src_ref_start = self.define_file_string(
                    None, os.path.join(self.folder_name_src_ref_start, self.file_name_src_ref_start),
                    file_extra_variables=file_extra_variables, file_extra_collections=file_extra_collections)

            file_list_src_ref_end = self.define_file_string(
                    None, os.path.join(self.folder_name_src_ref_end, self.file_name_src_ref_end),
                    file_extra_variables=file_extra_variables, file_extra_collections=file_extra_collections)

            file_collections_src_ref_start[exec_name] = pd.Series(file_list_src_ref_start).drop_duplicates().tolist()
            file_collections_src_ref_end[exec_name] = pd.Series(file_list_src_ref_end).drop_duplicates().tolist()

        self.file_collections_src_ref_start = file_collections_src_ref_start
        self.file_collections_src_ref_end = file_collections_src_ref_end

        self.file_path_anc_source = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_anc_source, self.file_name_anc_source),
            file_extra_variables=None, file_extra_collections=None)
        self.file_path_anc_analysis = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_anc_analysis, self.file_name_anc_analysis),
            file_extra_variables=None, file_extra_collections=None)
        self.file_path_anc_destination = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_anc_destination, self.file_name_anc_destination),
            file_extra_variables=None, file_extra_collections=None)

        self.file_path_dest_summary = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_dest_summary, self.file_name_dest_summary),
            file_extra_variables=None, file_extra_collections=None)
        self.file_path_dest_warnings = self.define_file_string(
            self.time_run, os.path.join(self.folder_name_dest_warnings, self.file_name_dest_warnings),
            file_extra_variables=None, file_extra_collections=None)

        self.flag_cleaning_dynamic_source = flag_cleaning_dynamic_source
        self.flag_cleaning_dynamic_analysis = flag_cleaning_dynamic_analysis
        self.flag_cleaning_dynamic_destination = flag_cleaning_dynamic_destination
        self.flag_cleaning_dynamic_tmp = flag_cleaning_dynamic_tmp

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
        self.tag_summary_alarm_value = 'alarm_value'
        self.tag_summary_alarm_index = 'alarm_index'
        self.tag_summary_alarm_section = 'alarm_section'
        self.tag_summary_alarm_thr = 'alarm_thr'
        self.tag_summary_run_type = 'run_type'

        self.warnings_structure = {
            'alert_datasets': {
                'key_ref': self.tag_summary_alert_value,
                'key_list': [self.tag_summary_alert_value, self.tag_summary_alert_index,
                             self.tag_summary_alert_thr, self.tag_summary_run_type]
            },
            'alarm_datasets': {
                'key_ref': self.tag_summary_alert_value,
                'key_list': [self.tag_summary_alarm_value, self.tag_summary_alarm_index,
                             self.tag_summary_alarm_thr, self.tag_summary_run_type]}
        }

        self.tag_info = 'info'
        self.tag_data = 'data'
        self.tag_warnings = 'warnings'
        self.tag_time_ref_start = 'time_start'
        self.tag_time_ref_end = 'time_end'

        self.tag_file_time_create = 'time_create'
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define  filename
    def define_file_string(self, time, file_path_raw,
                           file_extra_variables=None, file_extra_collections=None):

        if file_extra_variables is None:
            file_extra_variables = {}
        if file_extra_collections is None:
            file_extra_collections = None

        alg_template_tags = self.alg_template_tags

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
    # Method to collect section information
    def collect_section_list(self, columns_tag_in=None, columns_tag_out=None):

        if columns_tag_in is None:
            columns_tag_in = ['section_domain', 'section_name']
        if columns_tag_out is None:
            columns_tag_out = ['section_domain', 'section_name']

        section_data_collection = self.section_data_collection

        section_dict = {}
        for columns_in_step, columns_out_step in zip(columns_tag_in, columns_tag_out):
            section_data_step = section_data_collection[columns_in_step].values.tolist()
            section_dict[columns_out_step] = section_data_step
        return section_dict

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
    def dump_dynamic_data(self, analysis_datasets_collections, analysis_warnings_collections):

        time_exec = self.time_exec
        time_run = self.time_run

        exec_name_list = self.exec_name_list
        outlet_name_list = self.outlet_name_list
        exec_collections = self.execution_data_collection

        warnings_structure = self.warnings_structure

        file_path_anc = self.file_path_anc_destination
        file_path_dest_summary = self.file_path_dest_summary
        file_path_dest_warnings = self.file_path_dest_warnings

        flag_clean_anc = self.flag_cleaning_dynamic_destination

        logging.info(' ---> Dump dynamic datasets [' + str(time_run) + '] ... ')

        if flag_clean_anc:
            if os.path.exists(file_path_anc):
                os.remove(file_path_anc)

        summary_collections = {}
        for exec_name_step in exec_name_list:

            logging.info(' ----> Execution ' + exec_name_step + ' ... ')
            summary_collections[exec_name_step] = {}

            attrs_exec = exec_collections[exec_collections.index == exec_name_step].to_dict('r')[0]

            data_analysis = analysis_datasets_collections[exec_name_step][self.tag_run_datasets_section]

            if data_analysis is not None:

                attrs_analysis = analysis_datasets_collections[exec_name_step][self.tag_run_datasets_attrs]
                attrs_analysis[self.tag_run_ref_start] = analysis_datasets_collections[exec_name_step][self.tag_run_ref_start]
                attrs_analysis[self.tag_run_ref_end] = analysis_datasets_collections[exec_name_step][self.tag_run_ref_end]
                attrs_analysis[self.tag_run_ref_elapsed] = analysis_datasets_collections[exec_name_step][self.tag_run_ref_elapsed]

                summary_datasets = {}
                for section_name, section_data in data_analysis.items():

                    logging.info(' -----> Section ' + section_name + ' ... ')

                    attrs_datasets = {**attrs_analysis, **attrs_exec}

                    if section_data is not None:
                        for time_step, data_step in section_data.items():

                            logging.info(' ------> Time ' + str(time_step) + ' ... ')

                            max_alert_value = data_step[self.tag_summary_alert_value]
                            max_alert_idx = data_step[self.tag_summary_alert_index]
                            max_alarm_value = data_step[self.tag_summary_alarm_value]
                            max_alarm_idx = data_step[self.tag_summary_alarm_index]
                            thr_alert_value = data_step[self.tag_summary_alert_thr]
                            thr_alarm_value = data_step[self.tag_summary_alarm_thr]

                            if time_step not in list(summary_datasets.keys()):
                                summary_datasets[time_step] = {}

                                summary_datasets[time_step][self.tag_summary_alert_value] = [max_alert_value]
                                summary_datasets[time_step][self.tag_summary_alert_index] = [max_alert_idx]
                                summary_datasets[time_step][self.tag_summary_alert_section] = [section_name]
                                summary_datasets[time_step][self.tag_summary_alert_thr] = [thr_alert_value]

                                summary_datasets[time_step][self.tag_summary_alarm_value] = [max_alarm_value]
                                summary_datasets[time_step][self.tag_summary_alarm_index] = [max_alarm_idx]
                                summary_datasets[time_step][self.tag_summary_alarm_section] = [section_name]
                                summary_datasets[time_step][self.tag_summary_alarm_thr] = [thr_alarm_value]

                                summary_datasets[time_step][self.tag_summary_run_type] = [exec_name_step]

                            else:

                                tmp_datasets = deepcopy(summary_datasets[time_step])

                                tmp_alert_value = tmp_datasets[self.tag_summary_alert_value]
                                tmp_alert_idx = tmp_datasets[self.tag_summary_alert_index]
                                tmp_alert_section = tmp_datasets[self.tag_summary_alert_section]
                                tmp_alert_thr = tmp_datasets[self.tag_summary_alert_thr]
                                tmp_alert_value.append(max_alert_value)
                                tmp_alert_idx.append(max_alert_idx)
                                tmp_alert_section.append(section_name)
                                tmp_alert_thr.append(thr_alert_value)

                                summary_datasets[time_step][self.tag_summary_alert_value] = tmp_alert_value
                                summary_datasets[time_step][self.tag_summary_alert_index] = tmp_alert_idx
                                summary_datasets[time_step][self.tag_summary_alert_section] = tmp_alert_section
                                summary_datasets[time_step][self.tag_summary_alert_thr] = tmp_alert_thr

                                tmp_alarm_value = tmp_datasets[self.tag_summary_alarm_value]
                                tmp_alarm_idx = tmp_datasets[self.tag_summary_alarm_index]
                                tmp_alarm_section = tmp_datasets[self.tag_summary_alarm_section]
                                tmp_alarm_thr = tmp_datasets[self.tag_summary_alarm_thr]
                                tmp_alarm_value.append(max_alarm_value)
                                tmp_alarm_idx.append(max_alarm_idx)
                                tmp_alarm_section.append(section_name)
                                tmp_alarm_thr.append(thr_alarm_value)

                                summary_datasets[time_step][self.tag_summary_alarm_value] = tmp_alarm_value
                                summary_datasets[time_step][self.tag_summary_alarm_index] = tmp_alarm_idx
                                summary_datasets[time_step][self.tag_summary_alarm_section] = tmp_alarm_section
                                summary_datasets[time_step][self.tag_summary_alarm_thr] = tmp_alarm_thr

                                tmp_run_type = tmp_datasets[self.tag_summary_run_type]
                                tmp_run_type.append(exec_name_step)
                                summary_datasets[time_step][self.tag_summary_run_type] = tmp_run_type

                            logging.info(' ------> Time ' + str(time_step) + ' ... DONE')

                        logging.info(' -----> Section ' + section_name + ' ... DONE')

                    else:
                        logging.info(' -----> Section ' + section_name + ' ... SKIPPED. Datasets are undefined')

            else:
                summary_datasets = None
                attrs_datasets = deepcopy(attrs_exec)

            summary_collections[exec_name_step][self.tag_data] = {}
            summary_collections[exec_name_step][self.tag_data] = summary_datasets
            summary_collections[exec_name_step][self.tag_info] = {}
            summary_collections[exec_name_step][self.tag_info] = attrs_datasets

            logging.info(' ----> Execution ' + exec_name_step + ' ... DONE')

        # Save summary bulletin
        folder_name_dest_summary, file_name_dest_summary = os.path.split(file_path_dest_summary)
        make_folder(folder_name_dest_summary)
        logging.info(' ----> Save summary bulletin ' + file_name_dest_summary + ' ... ')

        write_file_summary(time_run, time_exec, time_format='%Y-%m-%d %H:%M', html_name=file_path_dest_summary,
                           run_name=exec_name_list, run_summary=summary_collections,
                           tag_summary_data=self.tag_data, tag_summary_info=self.tag_info,
                           tag_alert_section=self.tag_summary_alert_section,
                           tag_alert_value=self.tag_summary_alert_value,
                           tag_alert_index=self.tag_summary_alert_index,
                           tag_alarm_section=self.tag_summary_alarm_section,
                           tag_alarm_value=self.tag_summary_alarm_value,
                           tag_alarm_index=self.tag_summary_alarm_index)

        logging.info(' ----> Save summary bulletin ' + file_name_dest_summary + ' ... DONE')

        # Save warnings bulletin
        warnings_collections = {}
        for warnings_key, warnings_data in analysis_warnings_collections.items():

            if warnings_data is not None:
                warnings_collections[warnings_key] = {}
                for summary_key, summary_fields in warnings_structure.items():

                    key_ref = summary_fields['key_ref']
                    key_list = summary_fields['key_list']

                    values_ref = warnings_data[key_ref]
                    index_ref = int(values_ref.index(max(values_ref)))

                    warnings_collections[warnings_key][summary_key] = {}
                    for key_step in key_list:
                        value_step = warnings_data[key_step][index_ref]
                        warnings_collections[warnings_key][summary_key][key_step] = value_step

        folder_name_dest_warnings, file_name_dest_warnings = os.path.split(file_path_dest_warnings)
        make_folder(folder_name_dest_warnings)

        logging.info(' ----> Save warnings bulletin ' + file_name_dest_warnings + ' ... ')

        write_file_warnings(file_path_dest_warnings, warnings_collections, warnings_structure)

        logging.info(' ----> Save warnings bulletin ' + file_name_dest_warnings + ' ... DONE')

        logging.info(' ---> Dump dynamic datasets [' + str(time_run) + '] ... DONE')

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
    # Method to analyze dynamic data
    def analyze_dynamic_data(self, file_workspace):

        time = self.time_run
        exec_name_list = self.exec_name_list

        exec_collections = self.execution_data_collection

        file_path_anc = self.file_path_anc_analysis
        flag_clean_anc = self.flag_cleaning_dynamic_analysis

        logging.info(' ---> Analyze dynamic datasets [' + str(time) + '] ... ')

        if flag_clean_anc:
            if os.path.exists(file_path_anc):
                os.remove(file_path_anc)

        if not os.path.exists(file_path_anc):

            analyze_warnings_collections = {}
            analyze_datasets_collections = {}
            for exec_name_step in exec_name_list:

                logging.info(' ----> Execution ' + exec_name_step + ' ... ')

                exec_data = exec_collections[exec_collections.index == exec_name_step]
                exec_run_var_sim = exec_data[self.tag_run_var_sim].values[0]
                exec_run_var_obs = exec_data[self.tag_run_var_obs].values[0]

                analyze_datasets_collections[exec_name_step] = {}
                if exec_name_step in list(file_workspace.keys()):

                    exec_workspace = file_workspace[exec_name_step]

                    exec_info_collection = deepcopy(exec_workspace[self.tag_info])
                    exec_data_collection = deepcopy(exec_workspace[self.tag_data])

                    if (exec_info_collection[self.tag_run_ref_start] is not None) and \
                            (exec_info_collection[self.tag_run_ref_start] is not None):

                        analysis_time_creation_start, analysis_time_creation_end, \
                            analysis_time_creation_elapsed = analyze_time_info(
                                exec_info_collection[self.tag_run_ref_start],
                                exec_info_collection[self.tag_run_ref_end],
                                tag_file_create=self.tag_file_time_create)

                        analysis_datasets_section, analysis_warnings_section, \
                            attrs_datasets_section = analyze_hydrograph_datasets(
                                exec_name_step, exec_data_collection,
                                tag_discharge_observed=exec_run_var_obs, tag_discharge_simulated=exec_run_var_sim,
                                tag_discharge_thr_alert=self.tag_summary_alert_thr,
                                tag_discharge_thr_alarm=self.tag_summary_alarm_thr,
                                tag_discharge_max_alert_value=self.tag_summary_alert_value,
                                tag_discharge_max_alert_index=self.tag_summary_alert_index,
                                tag_discharge_max_alarm_value=self.tag_summary_alarm_value,
                                tag_discharge_max_alarm_index=self.tag_summary_alarm_index,
                                tag_run_n=self.tag_run_n, tag_section_n=self.tag_section_n)

                        logging.info(' ----> Execution ' + exec_name_step + ' ... DONE')
                    else:
                        analysis_time_creation_start = None
                        analysis_time_creation_end = None
                        analysis_time_creation_elapsed = None
                        analysis_datasets_section = None
                        analysis_warnings_section = None
                        attrs_datasets_section = None
                        logging.info(' ----> Execution ' + exec_name_step + ' ... SKIPPED. Execution datasets are null')
                else:
                    analysis_time_creation_start = None
                    analysis_time_creation_end = None
                    analysis_time_creation_elapsed = None
                    analysis_datasets_section = None
                    analysis_warnings_section = None
                    attrs_datasets_section = None
                    logging.info(' ----> Execution ' + exec_name_step + ' ... SKIPPED. Execution not available')

                analyze_datasets_collections[exec_name_step][self.tag_run_ref_start] = analysis_time_creation_start
                analyze_datasets_collections[exec_name_step][self.tag_run_ref_end] = analysis_time_creation_end
                analyze_datasets_collections[exec_name_step][self.tag_run_ref_elapsed] = analysis_time_creation_elapsed
                analyze_datasets_collections[exec_name_step][self.tag_run_datasets_section] = analysis_datasets_section
                analyze_datasets_collections[exec_name_step][self.tag_run_datasets_attrs] = attrs_datasets_section

                if analysis_warnings_section is not None:
                    for warnings_key, warnings_data in analysis_warnings_section.items():

                        if warnings_key not in list(analyze_warnings_collections.keys()):
                            analyze_warnings_collections[warnings_key] = {}

                        if warnings_data is not None:
                            for var_key, var_value in warnings_data.items():
                                if var_key not in list(analyze_warnings_collections[warnings_key].keys()):
                                    analyze_warnings_collections[warnings_key][var_key] = var_value
                                else:
                                    warning_value_tmp = analyze_warnings_collections[warnings_key][var_key]
                                    warning_value_tmp.extend(var_value)
                                    analyze_warnings_collections[warnings_key][var_key] = warning_value_tmp
                        else:
                            analyze_warnings_collections[warnings_key] = None

            folder_name_anc, file_name_anc = os.path.split(file_path_anc)
            make_folder(folder_name_anc)

            analyze_collections = {self.tag_data: analyze_datasets_collections,
                                   self.tag_warnings: analyze_warnings_collections}

            write_obj(file_path_anc, analyze_collections)

        else:

            analyze_collections = read_obj(file_path_anc)
            analyze_datasets_collections = analyze_collections[self.tag_data]
            analyze_warnings_collections = analyze_collections[self.tag_warnings]

        logging.info(' ---> Analyze dynamic datasets [' + str(time) + '] ... DONE')

        return analyze_datasets_collections, analyze_warnings_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize dynamic data
    def organize_dynamic_data(self):

        time = self.time_run

        outlet_name_list = self.outlet_name_list
        exec_name_list = self.exec_name_list

        exec_collections = self.execution_data_collection

        file_collections_src_ref_start = self.file_collections_src_ref_start
        file_collections_src_ref_end = self.file_collections_src_ref_end

        file_path_anc = self.file_path_anc_source
        flag_clean_anc = self.flag_cleaning_dynamic_source

        logging.info(' ---> Organize dynamic datasets [' + str(time) + '] ... ')

        if flag_clean_anc:
            if os.path.exists(file_path_anc):
                os.remove(file_path_anc)

        if not os.path.exists(file_path_anc):

            file_workspace = {}
            for exec_name_step in exec_name_list:

                logging.info(' ----> Execution ' + exec_name_step + ' ... ')

                file_path_src_ref_start = file_collections_src_ref_start[exec_name_step]
                file_path_src_ref_end = file_collections_src_ref_end[exec_name_step]

                exec_data = exec_collections[exec_collections.index == exec_name_step]
                exec_time_period = exec_data[self.tag_time_period].values[0]
                exec_time_frequency = exec_data[self.tag_time_frequency].values[0]
                exec_time_rounding = exec_data[self.tag_time_rounding].values[0]

                time_search = self.define_time_search(time,
                                                      time_period=exec_time_period, time_frequency=exec_time_frequency,
                                                      time_rounding=exec_time_rounding, time_reverse=True)

                file_workspace[exec_name_step] = {}
                file_workspace[exec_name_step][self.tag_info] = {}
                file_workspace[exec_name_step][self.tag_data] = {}
                file_workspace[exec_name_step][self.tag_info][self.tag_run_ref_start] = None
                file_workspace[exec_name_step][self.tag_info][self.tag_time_ref_start] = None
                file_workspace[exec_name_step][self.tag_info][self.tag_run_ref_end] = None
                file_workspace[exec_name_step][self.tag_info][self.tag_time_ref_end] = None
                file_workspace[exec_name_step][self.tag_data] = None

                for time_step in time_search:

                    logging.info(' -----> Time  ' + str(time_step) + ' ... ')

                    logging.info(' ------> Reference run_start datasets ... ')
                    if file_workspace[exec_name_step]['info']['run_start'] is None:
                        if file_path_src_ref_start.__len__() == 1:

                            file_path_src_start_raw = file_path_src_ref_start[0]
                            file_path_src_start_def = self.define_file_string(time_step, file_path_src_start_raw)

                            if file_path_src_start_def.endswith('.x'):
                                if os.path.exists(file_path_src_start_def):
                                    file_info_start = read_file_execution_info(file_path_src_start_def)
                                else:
                                    file_info_start = None
                            else:
                                logging.error(' ------> Reference run_start datasets ... FAILED')
                                raise NotImplementedError('Case not implemented in source reference type start')

                            file_check_start = all(elem is None for elem in list([file_info_start]))
                            if file_check_start:
                                file_insert_start = False
                                logging.info(' ------> Reference run_start datasets ... SKIPPED. Datasets not defined')
                            else:
                                file_insert_start = True
                                logging.info(' ------> Reference run_start datasets ... DONE')
                        else:
                            logging.error(' ------> Reference run_start datasets ... FAILED')
                            raise NotImplementedError('Case not implemented in source reference file start')
                    else:
                        logging.info(' ------> Reference run_start datasets ... SKIPPED. Datasets already selected')
                        file_insert_start = False

                    logging.info(' ------> Reference run_end datasets ... ')
                    if file_workspace[exec_name_step]['info']['run_end'] is None:
                        if file_path_src_ref_end.__len__() == 1:
                            logging.error(' ------> Reference run_end datasets ... FAILED')
                            raise NotImplementedError('Case not implemented in source reference file end')
                        elif file_path_src_ref_end.__len__() > 1:

                            if file_path_src_ref_end[0].endswith('.json'):

                                file_info_end = {}
                                file_data_end = {}
                                for outlet_name_step, file_path_src_end_raw in zip(outlet_name_list,
                                                                                   file_path_src_ref_end):

                                    file_path_src_end_def = self.define_file_string(time_step, file_path_src_end_raw)

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
                                    logging.info(' ------> Reference run_end datasets ... SKIPPED. Datasets not defined')
                                else:
                                    file_insert_end = True
                                    logging.info(' ------> Reference run_end datasets ... DONE')
                            else:
                                logging.error(' ------> Reference run_end datasets ... FAILED')
                                raise NotImplementedError('Case not implemented in source reference type end')
                        else:
                            logging.error(' ------> Reference run_end datasets ... FAILED')
                            raise NotImplementedError('Case not implemented in source reference file end')
                    else:
                        logging.info(' ------> Reference run_end datasets ... SKIPPED. Datasets already selected')
                        file_insert_end = False

                    # Store reference source information and datasets
                    if file_insert_start:
                        file_workspace[exec_name_step][self.tag_info][self.tag_run_ref_start] = file_info_start
                        file_workspace[exec_name_step][self.tag_info][self.tag_time_ref_start] = time_step
                    elif file_insert_end:
                        file_workspace[exec_name_step][self.tag_info][self.tag_run_ref_end] = file_info_end
                        file_workspace[exec_name_step][self.tag_info][self.tag_time_ref_end] = time_step
                        file_workspace[exec_name_step][self.tag_data] = file_data_end

                    logging.info(' -----> Time  ' + str(time_step) + ' ... DONE')

                logging.info(' ----> Execution ' + exec_name_step + ' ... DONE')

            folder_name_anc, file_name_anc = os.path.split(file_path_anc)
            make_folder(folder_name_anc)

            write_obj(file_path_anc, file_workspace)

        else:

            file_workspace = read_obj(file_path_anc)

        logging.info(' ---> Organize dynamic datasets [' + str(time) + '] ... DONE')

        return file_workspace

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
