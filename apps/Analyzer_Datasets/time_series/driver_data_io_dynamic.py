"""
Class Features

Name:          driver_data_io_dynamic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210408'
Version:       '1.0.0'
"""

######################################################################################
# Library
import logging
import os
import numpy as np
import pandas as pd
import xarray as xr

from copy import deepcopy

from lib_data_io_nc import read_file_collections, filter_file_collections, set_time_collections

from lib_utils_io import read_obj, write_obj, create_dset, write_dset
from lib_utils_system import fill_tags2string, make_folder
from lib_info_args import logger_name, time_format_algorithm, zip_extension

from driver_graphs_timeseries import DriverGraph

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
import matplotlib.pylab as plt
######################################################################################


# -------------------------------------------------------------------------------------
# Class DriverDynamic
class DriverDynamic:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, time_reference,
                 src_dict, anc_dict=None, anl_dict=None, dst_dict=None,
                 static_data_collection=None,
                 registry_data_collection=None,
                 alg_info=None, alg_template=None,
                 tag_terrain_data='terrain', tag_section_data='sections', tag_table_graph_data='table_graph_lut',
                 tag_static_source='source', tag_static_destination='destination',
                 tag_dynamic_source='source', tag_dynamic_destination='destination',
                 flag_cleaning_dynamic_src=True, flag_cleaning_dynamic_anl=True, flag_cleaning_dynamic_dst=True,
                 flag_cleaning_dynamic_tmp=True):

        self.time_reference = time_reference
        self.time_str = time_reference.strftime(time_format_algorithm)

        self.src_dict = src_dict
        self.anc_dict = anc_dict
        self.anl_dict = anl_dict
        self.dst_dict = dst_dict

        self.tag_terrain_data = tag_terrain_data
        self.tag_section_data = tag_section_data
        self.tag_table_graph_data = tag_table_graph_data

        self.tag_static_source = tag_static_source
        self.tag_static_destination = tag_static_destination
        self.tag_dynamic_source = tag_dynamic_source
        self.tag_dynamic_destination = tag_dynamic_destination

        self.info_domain_name = alg_info['domain_name']
        self.info_variable_limits = alg_info['variable_limits']

        self.alg_template_run = alg_template['run']
        self.alg_template_time = alg_template['time']
        self.alg_template_registry = alg_template['registry']
        self.alg_template_list = list({**self.alg_template_run, **self.alg_template_time}.keys())

        self.static_data_terrain = static_data_collection[self.tag_terrain_data]
        self.static_data_section = static_data_collection[self.tag_section_data]
        self.static_data_table_graph = static_data_collection[self.tag_table_graph_data]

        self.registry_data_collection = registry_data_collection

        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'
        self.filter_type_tag = 'type'

        self.run_mode_tag = 'run_mode'
        self.run_description_tag = 'run_description'
        self.run_n_tag = 'run_n'
        self.run_variables_tag = 'run_variables'
        self.graph_dependencies_tag = 'graph_dependencies'
        self.graph_description_tag = 'graph_description'
        self.graph_fx_tag = 'graph_fx'
        self.graph_name_tag = 'graph_tag_name'

        self.time_search_period_tag = 'time_search_period'
        self.time_search_freq_tag = 'time_search_frequency'

        self.section_name_type = 'section'
        if self.static_data_section.attrs:
            for attr_key, attr_value in self.static_data_section.attrs.items():
                if attr_key.lower() == self.filter_type_tag.lower():
                    self.section_name_type = attr_value
                    break

        self.str_delimiter = ':'

        self.dst_dict_plot = self.dst_dict['collections']['plot']
        self.dst_dict_info = self.dst_dict['collections']['info']
        self.dst_dict_datasets = self.dst_dict['collections']['datasets']

        self.run_name_list = self.define_run_name(src_dict)
        self.run_info_list = self.define_run_name(self.dst_dict_info)
        self.run_plot_list = self.define_run_name(self.dst_dict_plot)
        self.run_datasets_list = self.define_run_name(self.dst_dict_datasets)

        if set(self.run_info_list) != set(self.run_plot_list):
            log_stream.error(' ===> Destination datasets "info" and "plot" do not have the same keys, '
                             'Check your settings')
            log_stream.error(" Info keys: " + str(set(self.run_info_list)) +
                             " :: Plot keys: " + str(set(self.run_plot_list)))
            raise Exception("Keys in destination datasets are not correctly defined")

        self.run_search_period = self.define_run_common_field(
            src_dict, field_select=self.time_search_period_tag, field_cmp='max')
        self.run_n = self.define_run_common_field(
            src_dict, field_select=self.run_n_tag, field_cmp='max')
        self.run_search_freq = self.define_run_common_field(
            src_dict, field_select=self.time_search_freq_tag, field_cmp='unique')
        self.run_time_range = self.define_run_time_range(time_reference, time_period=self.run_search_period,
                                                         time_frequency=self.run_search_freq)

        self.run_point_order, self.run_point_name = self.define_point_name(name_type=self.section_name_type)
        self.run_point_registry = self.define_point_registry(name_type=self.section_name_type)

        self.run_file_collections_src = self.define_run_file_name_struct(
            self.src_dict, run_args={'run_key': self.run_name_list}, run_time_period=self.run_time_range)
        self.run_file_collections_anc = self.define_run_file_name_struct(
            self.anc_dict, run_args={'run_key': self.run_name_list}, run_time_period=self.run_time_range)
        self.run_file_collections_anl = self.define_run_file_name_struct(
            self.anl_dict, run_args={'run_key': []}, run_time_period=pd.DatetimeIndex([self.time_reference]))

        self.run_file_collections_dst_plot = self.define_run_file_name_struct(
            self.dst_dict_plot,
            run_args={'run_key': self.run_plot_list,
                      'basin_name:section_name': self.run_point_name,
                      'section_order': self.run_point_order},
            run_time_period=pd.DatetimeIndex([self.time_reference]))
        self.run_file_collections_dst_info = self.define_run_file_name_struct(
            self.dst_dict_info,
            run_args={'run_key': self.run_info_list,
                      'basin_name:section_name': self.run_point_name,
                      'section_order': self.run_point_order},
            run_time_period=pd.DatetimeIndex([self.time_reference]))
        self.run_file_collections_dst_datasets = self.define_run_file_name_struct(
            self.dst_dict_datasets,
            run_args={'run_key': self.run_datasets_list,
                      'basin_name:section_name': self.run_point_name,
                      'section_order': self.run_point_order},
            run_time_period=pd.DatetimeIndex([self.time_reference]))

        self.run_file_filter_src, self.run_file_filter_anc = self.filter_run_file_name_struct(
            self.run_file_collections_src, self.run_file_collections_anc)

        self.flag_cleaning_dynamic_src = flag_cleaning_dynamic_src
        self.flag_cleaning_dynamic_anl = flag_cleaning_dynamic_anl
        self.flag_cleaning_dynamic_dst = flag_cleaning_dynamic_dst
        self.flag_cleaning_dynamic_tmp = flag_cleaning_dynamic_tmp

        self.coord_name_time = 'times'
        self.dim_name_time = 'time'

        self.dims_order_1d = [self.dim_name_time]

        self.data_header_ancillary = 'header'
        self.data_values_ancillary = 'datasets'
        self.data_attrs_ancillary = 'attributes'

        self.run_attributes_removed = ['outlet_name', 'basin_name', 'plant_name', 'section_name']

        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define point registry
    def define_point_registry(self, name_lower=True, name_type=None,
                              str_delimiter_registry=','):

        if (name_type.__len__() == 1) and (name_type[0] is None):
            name_type = name_type[0]

        if name_lower:
            section_domain = self.static_data_section['section_domain'].str.lower()
        else:
            section_domain = self.static_data_section['section_domain']
        section_type = self.static_data_section['section_type']

        run_point_domain_list = section_domain.values.tolist()
        run_point_type_list = section_type.values.tolist()

        run_plot_list = self.run_plot_list

        point_registry_list = []
        for run_point_domain_step, run_point_type_step in zip(run_point_domain_list, run_point_type_list):
            if name_type is not None:
                if run_point_type_step.lower() in name_type.lower():
                    point_registry_tmp = str_delimiter_registry.join([run_point_domain_step] + run_plot_list)
                    point_registry_list.append(point_registry_tmp)
            else:
                point_registry_tmp = str_delimiter_registry.join([run_point_domain_step] + run_plot_list)
                point_registry_list.append(point_registry_tmp)

        point_registry_list = sorted(list(set(point_registry_list)))

        return point_registry_list

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define point name
    def define_point_name(self, name_type=None, str_delimiter_name=':'):

        if (name_type.__len__() == 1) and (name_type[0] is None):
            name_type = name_type[0]

        section_name_list = self.static_data_section['section_name'].values.tolist()
        section_domain_list = self.static_data_section['section_domain'].values.tolist()
        section_type_list = self.static_data_section['section_type'].values.tolist()
        section_order_list = self.static_data_section['section_domain_order'].values.tolist()

        section_order_selection = []
        section_point_selection = []
        for section_name_step, section_domain_step, section_order_step, section_type_step in zip(
                section_name_list, section_domain_list, section_order_list, section_type_list):

            if name_type is not None:
                if section_type_step.lower() in name_type.lower():
                    section_point_tmp = str_delimiter_name.join([section_domain_step, section_name_step])
                    section_point_selection.append(section_point_tmp)
                    section_order_selection.append(section_order_step)
            else:
                section_point_tmp = str_delimiter_name.join([section_domain_step, section_name_step])
                section_point_selection.append(section_point_tmp)
                section_order_selection.append(section_order_step)

        return section_order_selection, section_point_selection
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to filter filename(s) struct
    @staticmethod
    def filter_run_file_name_struct(run_file_collections, anc_file_collections, str_delimiter=':'):

        file_dframe = None
        anc_dframe = None
        for (run_name, run_fields), (anc_name, anc_fields) in zip(
                run_file_collections.items(), anc_file_collections.items()):

            file_ws = []
            anc_ws = []
            for (run_time, run_file), (anc_time, anc_file) in zip(run_fields.items(), anc_fields.items()):
                file_list = []
                id_list = []
                for file_id, file_name in enumerate(run_file):
                    if os.path.exists(file_name):
                        file_list.append(file_name)
                        id_list.append(file_id)

                if id_list.__len__() >= 1:
                    anc_list = [anc_file[0]]
                else:
                    anc_list = []

                if file_list.__len__() > 1:
                    file_string = str_delimiter.join(file_list)
                elif file_list.__len__() == 0:
                    file_string = None
                else:
                    file_string = file_list[0]
                if anc_list.__len__() > 1:
                    anc_string = str_delimiter.join(anc_list)
                elif anc_list.__len__() == 0:
                    anc_string = None
                else:
                    anc_string = anc_list[0]

                file_ws.append(file_string)
                anc_ws.append(anc_string)

            file_array = np.asarray(file_ws)
            anc_array = np.asarray(anc_ws)
            file_series = pd.Series(data=file_array, index=list(run_fields.keys()))
            anc_series = pd.Series(data=anc_array, index=list(anc_fields.keys()))

            if file_dframe is None:
                file_dframe = file_series.to_frame(name=run_name)
            else:
                file_dframe[run_name] = file_series
            if anc_dframe is None:
                anc_dframe = anc_series.to_frame(name=run_name)
            else:
                anc_dframe[run_name] = anc_series

        run_file_filter = {}
        anc_file_filter = {}
        for file_column, anc_column in zip(list(file_dframe.columns), list(anc_dframe.columns)):
            file_series_raw = file_dframe[file_column]
            anc_series_raw = anc_dframe[anc_column]
            file_series_filter = file_series_raw[file_series_raw.notnull()]
            anc_series_filter = anc_series_raw[file_series_raw.notnull()]

            run_file_filter[file_column] = file_series_filter
            anc_file_filter[file_column] = anc_series_filter

        return run_file_filter, anc_file_filter

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define filename(s) struct
    def define_run_file_name_struct(self, run_dict,
                                    run_args=None, run_time_period=None):

        alg_template_run = self.alg_template_run
        alg_template_time = self.alg_template_time

        alg_template_raw = {**alg_template_run, **alg_template_time}

        if 'run_key' in list(run_args.keys()):
            run_list = run_args['run_key']
        else:
            log_stream.error(' ===> Bad definition or "run_key" in the run arguments dictionary')
            raise Exception("Key not defined")

        if run_list.__len__() == 0:
            run_list = [None]

        ancillary_args = deepcopy(run_args)
        ancillary_args.pop('run_key', None)

        if ancillary_args.__len__() == 1:
            if 'basin_name:section_name' in list(ancillary_args.keys()):
                ancillary_list_point = ancillary_args['basin_name:section_name']
                ancillary_keys_point = ['basin_name:section_name'.split(self.str_delimiter)] * ancillary_list_point.__len__()

                ancillary_list_order = ['NA'] * ancillary_list_point.__len__()
                ancillary_keys_order = ['section_order'] * ancillary_list_point.__len__()
            else:
                log_stream.error(' ===> Ancillary tag "basin_name:section_name" is not defined.')
                raise RuntimeError('Check your static collections to solve the error')

        elif ancillary_args.__len__() == 2:

            if 'basin_name:section_name' in list(ancillary_args.keys()):
                ancillary_list_point = ancillary_args['basin_name:section_name']
                ancillary_keys_point = ['basin_name:section_name'.split(self.str_delimiter)] * ancillary_list_point.__len__()
            else:
                log_stream.error(' ===> Ancillary tag "basin_name:section_name" is not defined.')
                raise RuntimeError('Check your static collections to solve the error')
            if 'section_order' in list(ancillary_args.keys()):
                ancillary_list_order = ancillary_args['section_order']
                ancillary_keys_order = ['section_order'] * ancillary_list_order.__len__()
            else:
                log_stream.error(' ===> Ancillary tag "section_order" is not defined.')
                raise RuntimeError('Check your static collections to solve the error')

        else:
            ancillary_keys_point = None
            ancillary_list_point = None
            ancillary_keys_order = None
            ancillary_list_order = None

        if not isinstance(run_list, list):
            run_list = [run_list]

        run_file_collections = {}
        for run_key in run_list:

            if run_key is not None:
                run_fields = run_dict[run_key]
                run_folder_step = run_fields[self.folder_name_tag]
                run_file_step = run_fields[self.file_name_tag]
            else:
                run_fields = deepcopy(run_dict)
                run_folder_step = run_fields[self.folder_name_tag]
                run_file_step = run_fields[self.file_name_tag]

            if self.run_n_tag in list(run_fields.keys()):
                run_n = run_fields[self.run_n_tag]
            else:
                run_n = 1
            run_tag = self.define_run_n_range(n_max=run_n)

            run_path_step = os.path.join(run_folder_step, run_file_step)

            if run_key is not None:
                run_file_collections[run_key] = {}
            for run_time_step in run_time_period:

                run_file_list = []
                if run_key is not None:
                    run_file_collections[run_key][run_time_step] = {}
                else:
                    run_file_collections[run_time_step] = {}
                for run_tag_step in run_tag:

                    alg_template_filled = {}
                    for alg_template_key, alg_template_value in alg_template_time.items():
                        alg_template_filled[alg_template_key] = run_time_step
                    alg_template_filled['ensemble_name'] = run_tag_step

                    if ancillary_list_point is not None:
                        ancillary_dict_point = []
                        for anc_key_pnt, anc_value_pnt, anc_key_ord, anc_value_ord in zip(
                                ancillary_keys_point, ancillary_list_point, ancillary_keys_order, ancillary_list_order):

                            anc_value_pnt_parts = anc_value_pnt.split(self.str_delimiter)
                            anc_value_ord_parts = anc_value_ord.split(self.str_delimiter)

                            if not isinstance(anc_key_ord, list):
                                anc_key_ord = [anc_key_ord]

                            anc_keys = anc_key_pnt + anc_key_ord
                            anc_values = anc_value_pnt_parts + anc_value_ord_parts

                            ancillary_iterator = zip(anc_keys, anc_values)
                            ancillary_dict = dict(ancillary_iterator)
                            ancillary_dict_point.append(ancillary_dict)
                    else:
                        ancillary_dict_point = None

                    if ancillary_dict_point is not None:
                        for ancillary_value_step, ancillary_dict_step in zip(ancillary_list_point, ancillary_dict_point):
                            alg_template_filled = {**alg_template_filled, **ancillary_dict_step}
                            run_path_filled = fill_tags2string(run_path_step, alg_template_raw, alg_template_filled)
                            run_path_dict = {ancillary_value_step: run_path_filled}
                            run_file_list.append(run_path_dict)
                    else:
                        run_path_filled = fill_tags2string(run_path_step, alg_template_raw, alg_template_filled)
                        run_file_list.append(run_path_filled)

                if run_key is not None:
                    run_file_collections[run_key][run_time_step] = run_file_list
                else:
                    run_file_collections[run_time_step] = run_file_list

        return run_file_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define run time range
    @staticmethod
    def define_run_time_range(time_reference, time_period=1, time_frequency='H', time_reverse=True):

        if time_period < 1:
            log_stream.warning(' ===> Run time period less than 1, Set to 1 by the algorithm')
            time_period = 1
        time_range = pd.date_range(end=time_reference, periods=time_period, freq=time_frequency)

        if time_reverse:
            time_range = time_range[::-1]

        return time_range

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define run n
    @staticmethod
    def define_run_n_range(n_min=1, n_max=1, n_step=1, n_format="{:03d}"):

        n_name = np.arange(n_min, n_max + 1, n_step).tolist()
        n_range = np.arange(1, n_name.__len__() + 1, 1).tolist()

        n_list = []
        for i_name, i_range in zip(n_name, n_range):
            n_list.append(n_format.format(i_range))

        return n_list

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define run common field
    @staticmethod
    def define_run_common_field(data_dict, field_select=None, field_cmp=None):

        fields_common_values = []
        for data_key, data_fields in data_dict.items():
            for field_key, field_value in data_fields.items():
                if field_key == field_select:
                    fields_common_values.append(field_value)

        if fields_common_values.__len__() >= 1:
            if field_cmp == 'max':
                fields_common_value = max(fields_common_values)
            elif field_cmp == 'min':
                fields_common_value = min(fields_common_values)
            elif field_cmp == 'unique':
                fields_common_value = list(set(fields_common_values))
                if fields_common_value.__len__() == 1:
                    fields_common_value = fields_common_value[0]
                else:
                    log_stream.error(' ===> Run common fields is not defined unique')
                    raise NotImplementedError('Case not implemented yet')
            else:
                log_stream.error(' ===> Run common fields method is unavailable')
                raise NotImplementedError('Case not implemented yet')
        else:
            fields_common_value = None
            log_stream.warning(' ===> Run common field "' + field_select +
                               '" is empty. Variable is initialized by None')

        return fields_common_value

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define run name
    @staticmethod
    def define_run_name(data_dict, data_fields_exclude=None):

        if data_fields_exclude is None:
            data_fields_exclude = ['__comment__', '_comment_', 'comment', '']

        var_list_tmp = list(data_dict.keys())
        var_list_def = [var_name for var_name in var_list_tmp if var_name not in data_fields_exclude]

        return var_list_def

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean dynamic tmp
    def clean_dynamic_tmp(self):

        time_str = self.time_str
        file_collections_anc = self.run_file_collections_anc

        flag_cleaning_tmp = self.flag_cleaning_dynamic_tmp

        log_stream.info(' ----> Clean tmp datasets [' + time_str + '] ... ')

        for file_collection_type, file_collection_fields in file_collections_anc.items():
            log_stream.info(' -----> Run name "' + file_collection_type + '" ... ')
            if flag_cleaning_tmp:
                for file_time, file_path in file_collection_fields.items():

                    if (isinstance(file_path, list)) and (file_path.__len__() == 1):
                        file_path = file_path[0]
                    else:
                        log_stream.error(' ===> File path format is not allowed')
                        raise NotImplementedError('Case not implemented yet')

                    log_stream.info(' ------> Delete filename "' + file_path + '" ... ')
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        log_stream.info(' ------> Delete filename "' + file_path + '" ... DONE')
                    else:
                        log_stream.info(' ------> Delete filename "' + file_path + '" ... SKIPPED. File does not exist')

                log_stream.info(' -----> Run name "' + file_collection_type + '" ... DONE')
            else:
                log_stream.info(' -----> Run name "' + file_collection_type + '" ... SKIPPED. Flag not activated')

        log_stream.info(' ----> Clean tmp datasets [' + time_str + '] ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to check graph dependencies
    @staticmethod
    def check_graph_deps(data_collections, deps_collections):

        check_deps_list = []
        for deps_key in deps_collections.keys():
            if deps_key not in list(data_collections):
                check_deps_list.append(False)
                log_stream.warning(' ===> Graph dependencies "' + deps_key +
                                   '" is undefined. Graph will be deactivated. Check your datasets')
            else:
                check_deps_list.append(True)

        if all(check_deps_list):
            check_deps_flag = True
        else:
            check_deps_flag = False

        return check_deps_flag
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to dump dynamic data
    def dump_dynamic_data(self, run_analysis_collections):

        time_str = self.time_str

        dst_dict_plot = self.dst_dict_plot
        dst_dict_info = self.dst_dict_info
        dst_dict_datasets = self.dst_dict_datasets

        static_data_section = self.static_data_section
        static_data_table_graph = self.static_data_table_graph

        run_file_collections_dst_plot = self.run_file_collections_dst_plot
        run_file_collections_dst_info = self.run_file_collections_dst_info
        run_file_collections_dst_datasets = self.run_file_collections_dst_datasets

        flag_dynamic_dst = self.flag_cleaning_dynamic_dst

        log_stream.info(' ----> Dump dynamic datasets [' + time_str + '] ... ')

        if run_analysis_collections is not None:

            for (run_type_key, run_type_plot), run_type_info, run_type_datasets in zip(
                    run_file_collections_dst_plot.items(), run_file_collections_dst_info.values(),
                    run_file_collections_dst_datasets.values()):

                # Debug
                # run_type_key = 'time_series_nwp_deterministic_ecmwf0100'
                # run_type_key = 'time_series_nwp_probabilistic_lami2i'
                # run_type_key = 'time_series_nwp_probabilistic_comparison'
                # run_type_plot = run_file_collections_dst_plot[run_type_key]
                # run_type_info = run_file_collections_dst_info[run_type_key]
                # run_type_datasets = run_file_collections_dst_datasets[run_type_key]

                log_stream.info(' -----> Run name "' + run_type_key + '" ... ')

                run_time_stamp_plot = list(run_type_plot.keys())[0]
                run_file_name_collections_plot = list(run_type_plot.values())[0]
                run_file_name_collections_info = list(run_type_info.values())[0]
                run_file_name_collections_datasets = list(run_type_datasets.values())[0]

                if run_type_key in list(dst_dict_plot.keys()):
                    graph_deps = dst_dict_plot[run_type_key][self.graph_dependencies_tag]
                    graph_fx = dst_dict_plot[run_type_key][self.graph_fx_tag]
                    graph_tag_name = dst_dict_plot[run_type_key][self.graph_name_tag]
                else:
                    log_stream.error(' ===> Graph type "' + run_type_key + '" is not defined in settings file')
                    raise IOError('Check your settings file to add or remove the graph type selected')

                for run_section_info, run_section_file_plot, run_section_file_info, run_section_file_datasets in zip(
                        static_data_section.iterrows(),
                        run_file_name_collections_plot, run_file_name_collections_info, run_file_name_collections_datasets):

                    run_section_info = run_section_info[1]

                    run_section_name = run_section_info['section_name']
                    run_section_domain = run_section_info['section_domain']
                    run_section_tag = self.str_delimiter.join([run_section_domain, run_section_name])

                    # DEBUG START
                    # section_idx = 76 # Arzilla:FoceArzilla
                    # run_section_info = static_data_section.iloc[section_idx]
                    # run_section_name = run_section_info['section_name']
                    # run_section_domain = run_section_info['section_domain']
                    # run_section_tag = self.str_delimiter.join([run_section_domain, run_section_name])
                    # run_section_file_plot = run_file_name_collections_plot[section_idx]
                    # run_section_file_info = run_file_name_collections_info[section_idx]
                    # run_section_file_datasets = run_file_name_collections_datasets[section_idx]
                    # DEBUG END

                    log_stream.info(' ------> Domain "' + run_section_tag + '" ... ')

                    if run_section_tag in list(run_section_file_plot.keys()):
                        graph_section_file_plot = deepcopy(run_section_file_plot[run_section_tag])
                        graph_section_file_plot = fill_tags2string(graph_section_file_plot,
                                                                   self.alg_template_registry, {'tag_name': graph_tag_name})
                    else:
                        log_stream.error(' ===> Domain tag "' + run_section_tag + '" is not defined in expected file keys')
                        raise RuntimeError('Keys of "plot" destination datasets are not defined as expected')
                    if run_section_tag in list(run_section_file_info.keys()):
                        graph_section_file_info = deepcopy(run_section_file_info[run_section_tag])
                        graph_section_file_info = fill_tags2string(graph_section_file_info,
                                                                   self.alg_template_registry, {'tag_name': graph_tag_name})

                    else:
                        log_stream.error(' ===> Domain tag "' + run_section_tag + '" is not defined in expected file keys')
                        raise RuntimeError('Keys of "info" destination datasets are not defined as expected')

                    if run_section_tag in list(run_section_file_datasets.keys()):
                        graph_section_file_datasets = deepcopy(run_section_file_datasets[run_section_tag])
                        graph_section_file_datasets = fill_tags2string(graph_section_file_datasets,
                                                                   self.alg_template_registry, {'tag_name': graph_tag_name})

                    else:
                        log_stream.error(' ===> Domain tag "' + run_section_tag + '" is not defined in expected file keys')
                        raise RuntimeError('Keys of "datasets" destination datasets are not defined as expected')

                    if run_section_tag in list(run_analysis_collections.keys()):
                        graph_analysis_collections = run_analysis_collections[run_section_tag]
                    else:
                        log_stream.error(' ===> Domain tag "' + run_section_tag + '" is not defined in expected file keys')
                        raise RuntimeError('Keys of "analysis" destination datasets are not defined as expected')

                    if flag_dynamic_dst:
                        if os.path.exists(graph_section_file_plot):
                            os.remove(graph_section_file_plot)
                        if os.path.exists(graph_section_file_info):
                            os.remove(graph_section_file_info)
                        if os.path.exists(graph_section_file_datasets):
                            os.remove(graph_section_file_datasets)

                    if (not os.path.exists(graph_section_file_plot)) or (not os.path.exists(graph_section_file_info)) \
                            or (not os.path.exists(graph_section_file_datasets)):

                        flag_graph_deps = self.check_graph_deps(graph_analysis_collections, graph_deps)
                        if flag_graph_deps:

                            driver_graph = DriverGraph(
                                file_name_graph=graph_section_file_plot,
                                file_name_info=graph_section_file_info,
                                file_name_datasets=graph_section_file_datasets,
                                ts_obj=graph_analysis_collections, ts_deps=graph_deps,
                                fx_name=graph_fx['name'], fx_attrs=graph_fx['attrs'], fx_map=graph_fx['map'],
                                fx_table=static_data_table_graph
                            )

                            driver_graph.compute_data()

                            log_stream.info(' ------> Domain "' + run_section_tag + '" ... DONE')
                        else:
                            log_stream.info(' ------> Domain "' + run_section_tag + '" ... FAILED')

                    else:
                        log_stream.info(' ------> Domain "' + run_section_tag +
                                        '" ... SKIPPED. Datasets previously plotted and dumped')

                log_stream.info(' -----> Run name "' + run_type_key + '" ... DONE')

            log_stream.info(' ----> Dump dynamic datasets [' + time_str + '] ... DONE')

        else:
            log_stream.info(' ----> Dump dynamic datasets [' + time_str + '] ... SKIPPED. All datasets are undefined')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize dynamic data
    def analyze_dynamic_data(self, run_data_collections):

        time_str = self.time_str
        info_var_limits = self.info_variable_limits

        static_data_section = self.static_data_section

        run_file_collections_anl = self.run_file_collections_anl

        flag_dynamic_src = self.flag_cleaning_dynamic_src
        flag_dynamic_anl = self.flag_cleaning_dynamic_anl

        log_stream.info(' ----> Analyze dynamic datasets [' + time_str + '] ... ')

        if flag_dynamic_src:
            if not flag_dynamic_anl:
                log_stream.warning(
                    ' ==> Due to activation of dynamic source flag, analysis flag will be activated too')
                flag_dynamic_anl = True

        run_time_reference = set_time_collections(run_data_collections)

        if run_time_reference is not None:

            run_time_dict = {self.coord_name_time: run_time_reference}
            run_dframe_reference = pd.DataFrame(index=run_time_reference)

            run_file_path = list(run_file_collections_anl.values())[0]
            run_file_time = list(run_file_collections_anl.keys())[0]

            if isinstance(run_file_path, list):
                run_file_path = run_file_path[0]

            if flag_dynamic_anl:
                if os.path.exists(run_file_path):
                    os.remove(run_file_path)

            run_analysis_collections = {}
            if not os.path.exists(run_file_path):

                for run_type_key, run_type_fields in run_data_collections.items():

                    log_stream.info(' -----> Run "' + run_type_key + '"  ... ')

                    if run_type_fields is not None:
                        run_type_time = run_type_fields[self.data_header_ancillary][self.coord_name_time]
                        run_type_workspace = run_type_fields[self.data_values_ancillary]
                        run_type_attrs = run_type_fields[self.data_attrs_ancillary]

                        run_description = run_type_attrs[self.run_description_tag]

                        run_type_attrs_upd = deepcopy(run_type_attrs)
                        for attr_key in self.run_attributes_removed:
                            if attr_key in list(run_type_attrs.keys()):
                                run_type_attrs_upd.pop(attr_key, None)
                        run_type_attrs_upd['time_length'] = run_time_reference.__len__()
                        run_type_attrs_upd['time_period'] = run_time_reference

                        log_stream.info(' -----> Description: "' + run_description + '" ')

                        for run_domain_key, run_domain_fields in run_type_workspace.items():

                            log_stream.info(' ------> Domain: "' + run_domain_key + '" ... ')

                            if (run_domain_key == 'DomainAverage') or (run_domain_key in self.run_point_name):

                                if run_domain_key in self.run_point_name:
                                    section_domain, section_name = run_domain_key.split(self.str_delimiter)
                                    section_data = static_data_section.loc[
                                        (static_data_section['section_domain'] == section_domain) &
                                        (static_data_section['section_name'] == section_name)]
                                    section_dict = section_data.reset_index().to_dict('r')[0]
                                else:
                                    section_dict = {}

                                run_attrs = {**section_dict, **run_type_attrs_upd}

                                for run_var_key, run_var_array in run_domain_fields.items():

                                    run_var_type, run_var_name = run_var_key.split(self.str_delimiter)
                                    if run_var_name in list(info_var_limits.keys()):
                                        run_var_limits = info_var_limits[run_var_name]
                                    else:
                                        run_var_limits = [None, None]

                                    if run_var_limits[0] is not None:
                                        run_var_array[run_var_array < run_var_limits[0]] = np.nan
                                    if run_var_limits[1] is not None:
                                        run_var_array[run_var_array > run_var_limits[1]] = np.nan

                                    if run_var_array.shape[0] == 1:
                                        run_var_list = run_var_array.tolist()[0]
                                    elif run_var_array.shape[0] > 1:
                                        run_var_list = run_var_array.T.tolist()
                                    run_var_timeidx = pd.DatetimeIndex(run_type_time)
                                    run_dframe_var = pd.DataFrame(data=run_var_list, index=run_var_timeidx)

                                    run_dframe_filled = pd.merge(run_dframe_reference, run_dframe_var,
                                                                 how='outer', left_index=True, right_index=True)
                                    run_dframe_filled.index.name = self.coord_name_time

                                    run_datetimeidx_filled = run_dframe_filled.index
                                    run_values_filled = run_dframe_filled.values

                                    if run_domain_key not in list(run_analysis_collections.keys()):
                                        run_analysis_collections[run_domain_key] = {}
                                    if run_type_key not in list(run_analysis_collections[run_domain_key].keys()):
                                        run_analysis_collections[run_domain_key][run_type_key] = {}

                                    if self.data_attrs_ancillary not in \
                                            list(run_analysis_collections[run_domain_key][run_type_key].keys()):
                                        run_analysis_collections[run_domain_key][run_type_key][self.data_attrs_ancillary] = {}
                                        run_analysis_collections[run_domain_key][run_type_key][self.data_attrs_ancillary]['attributes_ts'] = run_attrs
                                        run_analysis_collections[run_domain_key][run_type_key][self.data_attrs_ancillary]['attributes_section'] = section_dict
                                        run_analysis_collections[run_domain_key][run_type_key][self.data_attrs_ancillary]['attributes_run'] = run_type_attrs_upd

                                    if self.data_values_ancillary not in \
                                            list(run_analysis_collections[run_domain_key][run_type_key].keys()):
                                        run_analysis_collections[run_domain_key][run_type_key][self.data_values_ancillary] = {}

                                    run_analysis_collections[run_domain_key][run_type_key][self.data_values_ancillary][run_var_key] = {}
                                    run_analysis_collections[run_domain_key][run_type_key][self.data_values_ancillary][run_var_key] = run_values_filled

                                log_stream.info(' ------> Domain: "' + run_domain_key + '" ... DONE')

                            else:
                                log_stream.info(' ------> Domain: "' + run_domain_key +
                                                '" ... SKIPPED. Domain is not available in the datasets collection.')

                        log_stream.info(' -----> Run "' + run_type_key + '"  ... DONE')

                    else:
                        log_stream.warning(' ===> Datasets are undefined and equal to None')
                        log_stream.info(' -----> Run "' + run_type_key + '"  ... FAILED')

                run_folder_name, run_file_name = os.path.split(run_file_path)
                make_folder(run_folder_name)
                write_obj(run_file_path, run_analysis_collections)

            else:
                run_analysis_collections = read_obj(run_file_path)

            log_stream.info(' ----> Analyze dynamic datasets [' + time_str + '] ... DONE')

        else:
            log_stream.info(' ----> Analyze dynamic datasets [' + time_str +
                            '] ... SKIPPED. All datasets are undefined')
            run_analysis_collections = None

        return run_analysis_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize dynamic data
    def organize_dynamic_data(self):

        time_str = self.time_str
        run_file_src = self.run_file_filter_src
        run_file_anc = self.run_file_filter_anc
        run_fields_src = self.src_dict

        run_points = self.run_point_name

        flag_dynamic_src = self.flag_cleaning_dynamic_src
        flag_dynamic_anl = self.flag_cleaning_dynamic_anl

        log_stream.info(' ---> Organize dynamic datasets [' + time_str + '] ... ')

        if flag_dynamic_anl:
            if not flag_dynamic_src:
                log_stream.warning(
                    ' ==> Due to activation of dynamic analysis flag, source flag will be activated too')
                flag_dynamic_src = True

        run_file_collections = {}
        for (run_type_key, run_series), (anc_type_key, anc_series) in zip(run_file_src.items(), run_file_anc.items()):

            run_fields = run_fields_src[run_type_key]

            run_mode = run_fields[self.run_mode_tag]
            run_description = run_fields[self.run_description_tag]
            run_variables = run_fields[self.run_variables_tag]

            log_stream.info(' ----> Run == Ref: "' + run_type_key + '" -- Description: "' +
                            run_description + '" ... ')

            run_datetime_index = run_series.index
            run_file_obj = run_series.values
            anc_datetime_index = anc_series.index
            anc_file_obj = anc_series.values

            run_file_list = run_file_obj.tolist()
            anc_file_list = anc_file_obj.tolist()

            log_stream.info(' -----> Search period of selected datasets ... ')
            if not run_datetime_index.empty:
                end_datetime_index = run_datetime_index[0]
                start_datetime_index = run_datetime_index[-1]
                end_datetime_str = end_datetime_index.strftime(time_format_algorithm)
                start_datetime_str = start_datetime_index.strftime(time_format_algorithm)

                if start_datetime_index != end_datetime_index:
                    log_stream.info(' ------> Selected steps from "' +
                                    start_datetime_str + '" to "' + end_datetime_str + '"')
                else:
                    log_stream.info(' ------> Selected step "' + start_datetime_str + '"')
                log_stream.info(' -----> Search period of selected datasets ... DONE')
            else:
                log_stream.info(' -----> Search period of selected datasets ... FAILED')
                log_stream.warning(' ===> Datasets are not found in the expected time-period')

            anc_dset = None
            for run_time_step, run_file_step, anc_file_step in zip(run_datetime_index, run_file_list, anc_file_list):

                log_stream.info(' -----> Run time "' + run_time_step.strftime(time_format_algorithm) + '" ... ')

                if flag_dynamic_src:
                    if os.path.exists(anc_file_step):
                        os.remove(anc_file_step)

                log_stream.info(' ------> Get datasets ... ')
                if anc_dset is None:
                    if not os.path.exists(anc_file_step):

                        run_file_group = run_file_step.split(self.str_delimiter)

                        if run_mode == 'deterministic':
                            run_file_header, run_file_data, run_file_attrs = read_file_collections(run_file_group)
                        elif run_mode == 'probabilistic':
                            run_file_header, run_file_data, run_file_attrs = read_file_collections(run_file_group)
                        else:
                            logging.error(' ===> Run mode "' + run_mode + ' is not allowed')
                            raise NotImplementedError('Case not implemented yet')

                        if run_file_data is not None:
                            run_file_filter = filter_file_collections(run_file_data, run_variables, run_points)
                        else:
                            run_file_filter = None
                            logging.warning(" ===> Data collections is None")

                        if self.run_description_tag not in list(run_file_attrs.keys()):
                            run_file_attrs[self.run_description_tag] = run_description

                        if run_file_filter:
                            folder_name_step, file_name_step = os.path.split(anc_file_step)
                            make_folder(folder_name_step)

                            anc_dset = {self.data_header_ancillary: run_file_header,
                                        self.data_values_ancillary: run_file_filter,
                                        self.data_attrs_ancillary: run_file_attrs}

                            write_obj(anc_file_step, anc_dset)

                            log_stream.info(' ------> Get datasets ... DONE')
                        else:

                            anc_dset = None
                            log_stream.warning(' ===> Datasets is None')
                            log_stream.info(' ------> Get datasets ... SKIPPED. Datasets is undefined')

                    else:

                        log_stream.info(' ------> Get datasets ... LOADED. Datasets is previously computed.')
                        anc_dset = read_obj(anc_file_step)

                else:
                    log_stream.info(' ------> Get datasets ... SKIPPED. Datasets is already loaded.')

                log_stream.info(' -----> Run time "' + run_time_step.strftime(time_format_algorithm) + '" ... DONE')

            if anc_dset is not None:
                log_stream.info(' ----> Run == Ref: "' + run_type_key + '" -- Description: "' +
                                run_description + '" ... DONE')
            else:
                log_stream.info(' ----> Run == Ref: "' + run_type_key + '" -- Description: "' +
                                run_description + '" ... FAILED. Datasets are not found in the selected time period ')

            run_file_collections[run_type_key] = anc_dset

        log_stream.info(' ---> Organize dynamic datasets [' + time_str + '] ... DONE')

        return run_file_collections
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
