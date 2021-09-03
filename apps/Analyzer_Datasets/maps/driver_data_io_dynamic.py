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

from lib_analysis_fx import var_cmp_accumulated, var_cmp_average, var_cmp_instantaneous

from lib_data_io_nc import read_file_gridded, organize_file_gridded, organize_attrs_gridded, merge_file_gridded

from lib_utils_io import read_obj, write_obj
from lib_utils_system import make_folder, extract_dict_values, fill_tags2string
from lib_info_args import logger_name, time_format_algorithm

from driver_graphs_maps import DriverGraph

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
                 src_dict, anc_dict=None, anl_dict=None, dst_dict=None, tmp_dict=None,
                 static_data_collection=None,
                 registry_data_collection=None,
                 alg_info=None, alg_template=None,
                 tag_terrain_data='terrain', tag_river_network_data='river_network',
                 tag_colormap_graph_data='colormap', tag_table_graph_data='table_graph_lut',
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
        self.tmp_dict = tmp_dict

        self.tag_terrain_data = tag_terrain_data
        self.tag_river_network_data = tag_river_network_data
        self.tag_colormap_graph_data = tag_colormap_graph_data
        self.tag_table_graph_data = tag_table_graph_data

        self.tag_static_source = tag_static_source
        self.tag_static_destination = tag_static_destination
        self.tag_dynamic_source = tag_dynamic_source
        self.tag_dynamic_destination = tag_dynamic_destination

        self.alg_template_data = alg_template['data']
        self.alg_template_time = alg_template['time']
        self.alg_template_registry = alg_template['registry']
        self.alg_template_list = list({**self.alg_template_data, **self.alg_template_time}.keys())

        self.static_data_terrain = static_data_collection[self.tag_terrain_data]
        self.static_data_river_network = static_data_collection[self.tag_river_network_data]
        self.static_colormap_graph = static_data_collection[self.tag_colormap_graph_data]
        self.static_data_table_graph = static_data_collection[self.tag_table_graph_data]

        self.registry_data_collection = registry_data_collection

        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'

        # pivot tags for each group (src, analysis and graph)
        self.src_variable_tag = 'data_variables'
        self.src_time_tag = 'data_time'
        self.src_attrs_tag = 'data_attributes'
        self.anl_variable_tag = 'analysis_variables'
        self.anl_attrs_tag = 'analysis_attributes'
        self.dst_variable_tag = 'graph_variables'
        self.dst_fx_tag = 'graph_fx'
        self.dst_attrs_tag = 'graph_attributes'

        # source tags
        self.src_var_name_file_tag = 'var_name_file'
        self.src_var_name_data_tag = 'var_name_data'
        self.src_var_mode_tag = 'var_mode'
        self.src_var_description_tag = 'var_description'
        self.src_var_n_tag = 'var_n'
        self.src_time_search_period_tag = 'time_search_period'
        self.src_time_search_freq_tag = 'time_search_frequency'
        self.src_time_search_file_tag = 'time_search_file'
        self.src_time_search_reference_tag = 'time_search_reference'

        # analysis tags
        self.anl_var_name_data_tag = 'var_name_data'
        self.anl_var_name_analysis_tag = 'var_name_analysis'
        self.anl_var_level_tag = 'var_level'
        self.anl_var_mode_tag = 'var_mode'
        self.anl_var_type_tag = 'var_type'
        self.anl_var_temporal_window_tag = 'var_temporal_window'
        self.anl_var_direction_window_tag = 'var_direction_window'
        self.anl_var_description_tag = 'var_description'

        # graph tags
        self.dst_var_name_analysis_tag = 'var_name_analysis'
        self.dst_var_name_graph_tag = 'var_name_graph'
        self.dst_var_description_tag = 'var_description'
        self.dst_var_colormap_tag = 'var_colormap'
        self.dst_fx_name_tag = 'fx_name'
        self.dst_fx_attrs_tag = 'fx_attrs'
        self.dst_fx_map_tag = 'fx_map'

        self.str_delimiter = ':'

        self.anc_raw_dict = self.anc_dict['raw']
        self.anc_group_dict = self.anc_dict['group']

        self.dst_dict_plot = self.dst_dict['collections']['plot']
        self.dst_dict_info = self.dst_dict['collections']['info']
        self.dst_dict_datasets = self.dst_dict['collections']['datasets']

        self.info_domain_name = alg_info['domain_name']
        self.info_variable_limits = alg_info['variable_limits']
        self.info_variable_src = self.extract_variable_from_dict(self.src_dict, obj_tags=[self.src_variable_tag])
        self.info_time_src = self.extract_variable_from_dict(self.src_dict, obj_tags=[self.src_time_tag])
        self.info_variable_anl = self.extract_variable_from_dict(self.anl_dict, obj_tags=[self.anl_variable_tag])
        self.info_variable_dst = self.extract_variable_from_dict(self.dst_dict_plot, obj_tags=[self.dst_variable_tag])
        self.info_fx_dst = self.extract_variable_from_dict(self.dst_dict_plot, obj_tags=[self.dst_fx_tag])

        self.src_name_list = self.define_data_name(src_dict)
        self.anl_name_list = self.define_data_name(anl_dict)

        if set(self.src_name_list) != set(self.anl_name_list):
            log_stream.error(' ===> Source datasets and analysis datasets do not have the same keys, '
                             'Check your settings')
            log_stream.error(" Info keys: " + str(set(self.src_name_list)) +
                             " :: Plot keys: " + str(set(self.anl_name_list)))
            raise Exception("Keys in the datasets are not correctly defined")

        self.dst_info_list = self.define_data_name(self.dst_dict_info)
        self.dst_plot_list = self.define_data_name(self.dst_dict_plot)
        self.dst_datasets_list = self.define_data_name(self.dst_dict_datasets)
        if set(self.dst_info_list) != set(self.dst_plot_list) != set(self.dst_datasets_list):
            log_stream.error(' ===> Destination datasets "info" and "plot" do not have the same keys, '
                             'Check your settings')
            log_stream.error(" Info keys: " + str(set(self.dst_info_list)) +
                             " :: Plot keys: " + str(set(self.dst_plot_list)) +
                             " :: Datasets keys: " + str(set(self.dst_datasets_list))
                             )
            raise Exception("Keys in the datasets are not correctly defined")

        self.src_time_search_period = self.define_data_common_field(
            self.info_time_src, field_select=self.src_time_search_period_tag, field_cmp='max')
        self.src_var_n = self.define_data_common_field(
            self.info_variable_src, field_select=self.src_var_n_tag, field_cmp='max')
        self.src_time_search_freq = self.define_data_common_field(
            self.info_time_src, field_select=self.src_time_search_freq_tag, field_cmp='unique')
        self.src_time_range = self.define_data_time_range(
            time_reference, time_period=self.src_time_search_period, time_frequency=self.src_time_search_freq)

        self.anl_var_level = self.define_map_attributes(self.anl_dict, key_pivot=self.anl_variable_tag,
                                                        key_name=self.anl_var_level_tag)
        self.anl_var_temporal_window = self.define_map_attributes(self.anl_dict, key_pivot=self.anl_variable_tag,
                                                                  key_name=self.anl_var_temporal_window_tag)
        self.anl_var_name = self.define_map_attributes(self.anl_dict, key_pivot=self.anl_variable_tag,
                                                       key_name=self.anl_var_name_analysis_tag)
        self.anl_var_mode = self.define_map_attributes(self.anl_dict, key_pivot=self.anl_variable_tag,
                                                       key_name=self.anl_var_mode_tag)

        self.dst_var_name = self.define_map_attributes(self.dst_dict_plot, key_pivot=self.dst_variable_tag,
                                                       key_name=self.dst_var_name_graph_tag)

        # collections of source file path(s)
        self.src_file_collections = self.define_data_file_name_struct(
            self.src_dict, data_args={'data_key': self.src_name_list},
            data_time_period=self.src_time_range, date_time_run=self.time_reference)

        # collections of ancillary file path(s)
        self.anc_file_collections_raw = self.define_data_file_name_struct(
            self.anc_raw_dict, data_args={'data_key': self.src_name_list},
            data_time_period=self.src_time_range, date_time_run=self.time_reference)
        self.anc_file_collections_group = self.define_data_file_name_struct(
            self.anc_group_dict, data_args={'data_key': self.src_name_list},
            data_time_period=pd.DatetimeIndex([self.time_reference]), date_time_run=self.time_reference)

        # collections of analysis file path(s)
        self.anl_file_collections = self.define_data_file_name_struct(
            self.anl_dict, data_args={'data_key': self.anl_name_list},
            data_time_period=pd.DatetimeIndex([self.time_reference]), date_time_run=self.time_reference)

        # collections of destination file path(s)
        self.dst_file_collections_plot = self.define_data_file_name_struct(
            self.dst_dict_plot,
            data_args={'domain_name': self.info_domain_name,
                       'data_key': self.dst_plot_list,
                       'var_name': self.dst_var_name,
                       'var_level': self.anl_var_level,
                       'var_temporal_window': self.anl_var_temporal_window,
                       'var_mode': self.anl_var_mode},
            data_time_period=pd.DatetimeIndex([self.time_reference]))
        self.dst_file_collections_info = self.define_data_file_name_struct(
            self.dst_dict_info,
            data_args={'domain_name': self.info_domain_name,
                       'data_key': self.dst_plot_list,
                       'var_name': self.dst_var_name,
                       'var_level': self.anl_var_level,
                       'var_temporal_window': self.anl_var_temporal_window,
                       'var_mode': self.anl_var_mode},
            data_time_period=pd.DatetimeIndex([self.time_reference]))
        self.dst_file_collections_datasets = self.define_data_file_name_struct(
            self.dst_dict_datasets,
            data_args={'domain_name': self.info_domain_name,
                       'data_key': self.dst_plot_list,
                       'var_name': self.dst_var_name,
                       'var_level': self.anl_var_level,
                       'var_temporal_window': self.anl_var_temporal_window,
                       'var_mode': self.anl_var_mode},
            data_time_period=pd.DatetimeIndex([self.time_reference]))

        self.src_file_filter, self.anc_file_filter_raw = self.filter_data_file_name_struct(
            self.src_file_collections, self.anc_file_collections_raw)

        self.anc_file_filter_group = self.convert_data_file_name_struct(self.anc_file_collections_group)

        self.flag_cleaning_dynamic_src = flag_cleaning_dynamic_src
        self.flag_cleaning_dynamic_anl = flag_cleaning_dynamic_anl
        self.flag_cleaning_dynamic_dst = flag_cleaning_dynamic_dst
        self.flag_cleaning_dynamic_tmp = flag_cleaning_dynamic_tmp

        self.coord_name_geo_x = 'longitude'
        self.coord_name_geo_y = 'latitude'
        self.coord_name_time = 'time'
        self.dim_name_geo_x = 'longitude'
        self.dim_name_geo_y = 'latitude'
        self.dim_name_time = 'time'

        self.dims_order_2d = [self.dim_name_geo_y, self.dim_name_geo_x]
        self.dims_order_3d = [self.dim_name_geo_y, self.dim_name_geo_x, self.dim_name_time]

        self.folder_tmp = self.define_tmp_folder()

        self.workspace_values = 'datasets'
        self.workspace_attrs = 'attributes'

        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to extract analysis variables
    @staticmethod
    def extract_variable_from_dict(obj_dict, obj_tags=None):

        if obj_tags is None:
            obj_tags = ['variables']

        variable_dict = {}
        for obj_key, obj_fields in obj_dict.items():
            variable_dict[obj_key] = {}

            if isinstance(obj_fields, dict):
                for field_key, field_values in obj_fields.items():
                    if field_key in obj_tags:
                        variable_dict[obj_key] = field_values
            else:
                log_stream.error(' ===> Dictionary field format is not allowed')
                raise IOError('Dictionary field format must be Dict')

        return variable_dict

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define temporary folder
    def define_tmp_folder(self):
        folder_name = self.tmp_dict[self.folder_name_tag]
        make_folder(folder_name)
        return folder_name
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define map attributes
    @staticmethod
    def define_map_attributes(dict_obj, key_pivot='analysis_variables', key_name='var_level'):
        dict_attribute = {}
        for dict_key, dict_fields in dict_obj.items():

            if key_pivot in list(dict_fields.keys()):
                dict_variables = dict_fields[key_pivot]
                dict_attribute[dict_key] = {}
                for var_key, var_fields in dict_variables.items():
                    var_value = extract_dict_values(var_fields, key_name)
                    if isinstance(var_value, list) and var_value.__len__() == 1:
                        var_value = var_value[0]
                    else:
                        log_stream.error(' ===> Variable value obj is not allowed')
                        raise NotImplemented('Case not implemented yet')

                    dict_attribute[dict_key][var_key] = var_value
            else:
                log_stream.warning(' ===> Dictionary "key_pivot" is not available in the selected dictionary')
                dict_attribute[dict_key] = None

        return dict_attribute
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to convert data file name struct
    @staticmethod
    def convert_data_file_name_struct(anc_file_collections):

        anc_file_filter = {}
        for data_key, data_fields in anc_file_collections.items():
            anc_file_filter[data_key] = {}

            data_values = list(data_fields.values())[0]
            data_keys = list(data_fields.keys())

            data_series = pd.Series(data=data_values, index=data_keys)

            anc_file_filter[data_key] = data_series

        return anc_file_filter

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to filter filename(s) struct
    @staticmethod
    def filter_data_file_name_struct(data_file_collections, anc_file_collections, str_delimiter=':'):

        file_dframe = None
        anc_dframe = None
        for (data_name, data_fields), (anc_name, anc_fields) in zip(
                data_file_collections.items(), anc_file_collections.items()):

            file_ws = []
            anc_ws = []
            for (data_time, data_file), (anc_time, anc_file) in zip(data_fields.items(), anc_fields.items()):
                file_list = []
                id_list = []
                for file_id, file_name in enumerate(data_file):
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
            file_series = pd.Series(data=file_array, index=list(data_fields.keys()))
            anc_series = pd.Series(data=anc_array, index=list(anc_fields.keys()))

            if file_dframe is None:
                file_dframe = file_series.to_frame(name=data_name)
            else:
                file_dframe[data_name] = file_series
            if anc_dframe is None:
                anc_dframe = anc_series.to_frame(name=data_name)
            else:
                anc_dframe[data_name] = anc_series

        data_file_filter = {}
        anc_file_filter = {}
        for file_column, anc_column in zip(list(file_dframe.columns), list(anc_dframe.columns)):
            file_series_raw = file_dframe[file_column]
            anc_series_raw = anc_dframe[anc_column]
            file_series_filter = file_series_raw[file_series_raw.notnull()]
            anc_series_filter = anc_series_raw[file_series_raw.notnull()]

            data_file_filter[file_column] = file_series_filter
            anc_file_filter[file_column] = anc_series_filter

        return data_file_filter, anc_file_filter

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define filename(s) struct
    def define_data_file_name_struct(self, data_dict,
                                     data_args=None, data_time_period=None, date_time_run=None):

        alg_template_data = self.alg_template_data
        alg_template_time = self.alg_template_time

        alg_template_raw = {**alg_template_data, **alg_template_time}

        if 'data_key' in list(data_args.keys()):
            data_list = data_args['data_key']
        else:
            log_stream.error(' ===> Bad definition or "data_key" in the datada arguments dictionary')
            raise Exception("Key not defined")

        if data_list.__len__() == 0:
            data_list = [None]

        ancillary_args = deepcopy(data_args)
        ancillary_args.pop('data_key', None)

        if not isinstance(data_list, list):
            data_list = [data_list]

        data_file_collections = {}
        for data_key in data_list:

            if data_key is not None:
                data_fields = data_dict[data_key]
                data_folder_step = data_fields[self.folder_name_tag]
                data_file_step = data_fields[self.file_name_tag]
                if self.src_time_search_reference_tag in list(data_fields.keys()):
                    data_time_reference_step = data_fields[self.src_time_search_reference_tag]
                else:
                    data_time_reference_step = None
            else:
                data_fields = deepcopy(data_dict)
                data_folder_step = data_fields[self.folder_name_tag]
                data_file_step = data_fields[self.file_name_tag]
                if self.src_time_search_reference_tag in list(data_fields.keys()):
                    data_time_reference_step = data_fields[self.src_time_search_reference_tag]
                else:
                    data_time_reference_step = None

            if self.src_var_n_tag in list(data_fields.keys()):
                data_n = data_fields[self.src_var_n_tag]
            else:
                data_n = 1
            data_tag = self.define_data_n_range(n_max=data_n)

            data_path_step = os.path.join(data_folder_step, data_file_step)

            if data_key is not None:
                data_file_collections[data_key] = {}
            for data_time_step in data_time_period:

                data_file_obj = []
                if data_key is not None:
                    data_file_collections[data_key][data_time_step] = {}
                else:
                    data_file_collections[data_time_step] = {}
                for data_tag_step in data_tag:

                    alg_template_filled = {}
                    for alg_template_key, alg_template_value in alg_template_time.items():
                        alg_template_filled[alg_template_key] = data_time_step
                    alg_template_filled['ensemble_name'] = data_tag_step

                    for tmpl_key, tmpl_value in alg_template_filled.items():
                        if data_time_reference_step is not None:
                            if tmpl_key in list(data_time_reference_step.keys()):
                                time_reference_flag = data_time_reference_step[tmpl_key]
                                if time_reference_flag == 'time_run':
                                    alg_template_filled[tmpl_key] = date_time_run
                                elif time_reference_flag == 'time_period':
                                    pass
                                else:
                                    log_stream.error(' ===> Time folder reference value is not allowed')
                                    raise RuntimeError('Time folder reference value must pe "time_run" or "time_period"')

                    ancillary_name = None
                    if ancillary_args:

                        ancillary_template = {}
                        for ancillary_key, ancillary_fields in ancillary_args.items():
                            if isinstance(ancillary_fields, dict):
                                if data_key in list(ancillary_fields.keys()):
                                    var_args = ancillary_fields[data_key]
                                    if ancillary_name is None:
                                        ancillary_name = list(var_args.keys())

                                    ancillary_template[ancillary_key] = list(var_args.values())
                            elif isinstance(ancillary_fields, str):
                                ancillary_template[ancillary_key] = ancillary_fields
                            else:
                                log_stream.error(' ===> Ancillary fields format is not allowed')
                                raise NotImplemented('Case not implemented yet')

                    if ancillary_name is None:
                        data_path_filled = fill_tags2string(data_path_step, alg_template_raw, alg_template_filled)
                        data_file_obj.append(data_path_filled)
                    else:
                        data_file_dict = {}

                        for variable_id, variable_name in enumerate(ancillary_name):
                            ancillary_template_filled = {}
                            for template_key, template_value in ancillary_template.items():
                                if isinstance(template_value, list):
                                    template_value_selected = template_value[variable_id]
                                else:
                                    template_value_selected = template_value
                                ancillary_template_filled[template_key] = template_value_selected

                            alg_template_not_equal = {**alg_template_filled, **ancillary_template_filled}
                            alg_template_equal, alg_template_len = self.adjust_dict_deep(alg_template_not_equal)

                            data_file_step = []
                            for alg_template_step in range(0, alg_template_len):
                                alg_template_filled = {}
                                for alg_template_key, alg_template_value in alg_template_equal.items():
                                    alg_template_filled[alg_template_key] = alg_template_value[alg_template_step]

                                data_path_filled = fill_tags2string(data_path_step, alg_template_raw, alg_template_filled)
                                data_file_step.append(data_path_filled)

                            data_file_dict[variable_name] = data_file_step
                        data_file_obj = deepcopy(data_file_dict)

                if data_key is not None:
                    data_file_collections[data_key][data_time_step] = data_file_obj
                else:
                    data_file_collections[data_time_step] = data_file_obj

        return data_file_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to adjust dictionary deep
    @staticmethod
    def adjust_dict_deep(template_dict):

        template_len_max = 0
        for template_key, template_values in template_dict.items():

            if isinstance(template_values, pd.Timestamp):
                template_len_step = 1
            elif isinstance(template_values, str):
                template_len_step = 1
            elif isinstance(template_values, list):
                template_len_step = template_values.__len__()

            if template_len_step > template_len_max:
                template_len_max = template_len_step

        template_dict_upd = {}
        for template_key, template_values in template_dict.items():

            if isinstance(template_values, pd.Timestamp):
                template_values_upd = [template_values] * template_len_max
            elif isinstance(template_values, str):
                template_values_upd = [template_values] * template_len_max
            elif isinstance(template_values, list):
                template_values_upd = template_values
            template_dict_upd[template_key] = template_values_upd

        return template_dict_upd, template_len_max

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define data time range
    @staticmethod
    def define_data_time_range(time_reference, time_period=1, time_frequency='H', time_reverse=True):

        if time_period < 1:
            log_stream.warning(' ===> Data time period less than 1, Set to 1 by the algorithm')
            time_period = 1
        time_range = pd.date_range(end=time_reference, periods=time_period, freq=time_frequency)

        if time_reverse:
            time_range = time_range[::-1]

        return time_range

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define data n
    @staticmethod
    def define_data_n_range(n_min=1, n_max=1, n_step=1, n_format="{:03d}"):

        n_name = np.arange(n_min, n_max + 1, n_step).tolist()
        n_range = np.arange(1, n_name.__len__() + 1, 1).tolist()

        n_list = []
        for i_name, i_range in zip(n_name, n_range):
            n_list.append(n_format.format(i_range))

        return n_list

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define data common field
    @staticmethod
    def define_data_common_field(data_dict, field_select=None, field_cmp=None):

        fields_common_values = []
        for data_key, data_fields in data_dict.items():
            for field_key, field_value in data_fields.items():
                if not isinstance(field_value, dict):
                    if field_key == field_select:
                        fields_common_values.append(field_value)
                elif isinstance(field_value, dict):
                    for value_key, value_step in field_value.items():
                        if value_key == field_select:
                            fields_common_values.append(value_step)
                else:
                    log_stream.error(' ===> Object type for multiple values is not allowed')
                    raise NotImplementedError('Case not implemented yet')

        if fields_common_values.__len__() >= 1:
            if field_cmp == 'max':
                fields_common_value = max(fields_common_values)
            elif field_cmp == 'min':
                fields_common_value = min(fields_common_values)
            elif field_cmp == 'unique':
                fields_common_value = list(set(fields_common_values))
                if fields_common_value.__len__() == 1:
                    fields_common_value = fields_common_value[0]
                elif fields_common_value.__len__() > 1:
                    fields_tmp_value = []
                    for field_value in fields_common_value:
                        if isinstance(field_value, str):
                            if field_value.isalpha():
                                field_value = '1' + field_value
                            field_td_seconds = pd.to_timedelta(field_value).total_seconds()
                            fields_tmp_value.append(field_td_seconds)
                        else:
                            log_stream.error(' ===> Run common fields type for multiple values is not allowed')
                            raise NotImplementedError('Case not implemented yet')
                    field_min_idx = np.argmin(fields_tmp_value)
                    fields_common_value = fields_common_value[field_min_idx]
                else:
                    log_stream.error(' ===> Run common fields not defined')
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
    # Method to define data name
    @staticmethod
    def define_data_name(data_dict, data_fields_exclude=None):

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
        file_collections_anc = self.anc_file_collections_group

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
    # Method to map variables between two info dictionaries
    @staticmethod
    def define_variable_map(info_variable_src, info_variable_dst, reference_key='var_name_analysis'):

        map_tmp_src = {}
        for info_key_src, info_vars_src in info_variable_src.items():
            map_tmp_src[info_key_src] = {}
            for var_key_src, var_fields_src in info_vars_src.items():
                for field_key_src, field_name_src in var_fields_src.items():
                    if field_key_src == reference_key:
                        map_tmp_src[info_key_src][var_key_src] = {}
                        map_tmp_src[info_key_src][var_key_src] = field_name_src
        map_tmp_dst = {}
        for info_key_dst, info_vars_dst in info_variable_dst.items():
            map_tmp_dst[info_key_dst] = {}
            for var_key_dst, var_fields_dst in info_vars_dst.items():
                for field_key_dst, field_name_dst in var_fields_dst.items():
                    if field_key_dst == reference_key:
                        map_tmp_dst[info_key_dst][var_key_dst] = {}
                        map_tmp_dst[info_key_dst][var_key_dst] = field_name_dst

        map_variable = {}
        for (map_key_src, map_db_src), (map_key_dst, map_db_dst) in zip(map_tmp_src.items(), map_tmp_dst.items()):
            if map_key_src == map_key_dst:
                map_variable[map_key_dst] = {}
                for db_key_src, db_name_src in map_db_src.items():
                    for db_key_dst, db_name_dst in map_db_dst.items():
                        if db_name_src == db_name_dst:
                            map_variable[map_key_dst][db_key_src] = {}
                            map_variable[map_key_dst][db_key_src][db_key_dst] = {}
                            map_variable[map_key_dst][db_key_src][db_key_dst] = db_name_dst

        return map_variable
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to dump dynamic data
    def dump_dynamic_data(self, anl_file_collections):

        time_str = self.time_str

        anl_info_variable = self.info_variable_anl
        dst_info_variable = self.info_variable_dst
        dst_info_fx = self.info_fx_dst

        map_info_variable = self.define_variable_map(anl_info_variable, dst_info_variable,
                                                     reference_key='var_name_analysis')

        anl_dict = self.anl_dict
        dst_dict_plot = self.dst_dict_plot
        dst_dict_info = self.dst_dict_info
        dst_dict_datasets = self.dst_dict_datasets

        static_colormap_graph = self.static_colormap_graph
        static_data_table_graph = self.static_data_table_graph

        dst_file_collections_plot = self.dst_file_collections_plot
        dst_file_collections_info = self.dst_file_collections_info
        dst_file_collections_datasets = self.dst_file_collections_datasets

        flag_dynamic_dst = self.flag_cleaning_dynamic_dst

        log_stream.info(' ----> Dump dynamic datasets [' + time_str + '] ... ')

        for (dst_type_key, dst_type_plot), dst_type_info, dst_type_datasets in zip(
                dst_file_collections_plot.items(), dst_file_collections_info.values(),
                dst_file_collections_datasets.values()):

            log_stream.info(' -----> Dataset == Ref: "' + dst_type_key + '" ... ')

            dst_time_stamp_plot = list(dst_type_plot.keys())[0]
            dst_file_collections_plot = list(dst_type_plot.values())[0]
            dst_file_collections_info = list(dst_type_info.values())[0]
            dst_file_collections_datasets = list(dst_type_datasets.values())[0]

            dst_collections_map = map_info_variable[dst_type_key]
            dst_collections_attrs = dst_info_variable[dst_type_key]
            dst_collections_fx = dst_info_fx[dst_type_key]

            if dst_type_key in list(anl_file_collections.keys()):
                anl_file_path = anl_file_collections[dst_type_key]
            else:
                anl_file_path = None
            
            if anl_file_path is not None:

                anl_file_obj = read_obj(anl_file_path)
                anl_file_dset = anl_file_obj[self.workspace_values]
                anl_file_attrs = anl_file_obj[self.workspace_attrs]

                for anl_var_key, anl_var_dst in anl_file_dset.items():

                    if anl_var_key in list(dst_collections_map.keys()):

                        dst_var_key = list(dst_collections_map[anl_var_key].keys())[0]
                        anl_var_name = list(dst_collections_map[anl_var_key].values())[0]

                        if dst_var_key in list(dst_file_collections_plot.keys()):

                            log_stream.info(' ------> Variable "' + dst_var_key + '"  ... ')

                            dst_info_attrs = dst_collections_attrs[dst_var_key]
                            anl_info_attrs = anl_file_attrs[anl_var_key]

                            dst_file_list_plot = dst_file_collections_plot[dst_var_key]
                            dst_file_list_info = dst_file_collections_info[dst_var_key]
                            dst_file_list_datasets = dst_file_collections_datasets[dst_var_key]

                            if flag_dynamic_dst:
                                for dst_file_plot, dst_file_info, dst_file_datasets in zip(
                                        dst_file_list_plot, dst_file_list_info, dst_file_list_datasets):
                                    if os.path.exists(dst_file_plot):
                                        os.remove(dst_file_plot)
                                    if os.path.exists(dst_file_info):
                                        os.remove(dst_file_info)
                                    if os.path.exists(dst_file_datasets):
                                        os.remove(dst_file_datasets)

                            for (anl_var_t_period, anl_var_darray), \
                                dst_file_path_plot, dst_file_path_info, dst_file_path_datasets in zip(
                                anl_var_dst.items(), dst_file_list_plot, dst_file_list_info, dst_file_list_datasets):

                                log_stream.info(' -------> Period "' + anl_var_t_period + '"  ... ')

                                if (not os.path.exists(dst_file_path_plot)) or \
                                        (not os.path.exists(dst_file_path_plot)) or \
                                        (not os.path.exists(dst_file_path_plot)):

                                    dst_fx_info = deepcopy(dst_collections_fx)

                                    dst_attrs_info = self.merge_attrs_obj(
                                        dict_attr_base=anl_info_attrs,
                                        dict_attr_list=[dst_info_attrs], dict_name_list=[self.dst_attrs_tag])

                                    if 'var_temporal_window' in list(anl_info_attrs[self.anl_attrs_tag].keys()):
                                        dst_attrs_info[self.anl_attrs_tag]['var_temporal_window'] = anl_var_t_period
                                    else:
                                        dst_attrs_info[self.anl_attrs_tag]['var_temporal_window'] = {}
                                        dst_attrs_info[self.anl_attrs_tag]['var_temporal_window'] = anl_var_t_period

                                    if 'var_colormap' in list(anl_info_attrs[self.dst_attrs_tag].keys()):
                                        dst_colormap_name = dst_attrs_info[self.dst_attrs_tag]['var_colormap']
                                        if dst_colormap_name is not None:
                                            if dst_colormap_name in list(static_colormap_graph.keys()):
                                                dst_colormap_obj = static_colormap_graph[dst_colormap_name]
                                            else:
                                                dst_colormap_obj = dst_colormap_name
                                        else:
                                            dst_colormap_obj = None
                                    else:
                                        dst_colormap_obj = None

                                    driver_graph = DriverGraph(
                                        file_name_graph=dst_file_path_plot,
                                        file_name_info=dst_file_path_info,
                                        file_name_datasets=dst_file_path_datasets,
                                        map_time_stamp=dst_time_stamp_plot, map_time_description=anl_var_t_period,
                                        map_obj=anl_var_darray, map_attrs=dst_attrs_info, map_colormap=dst_colormap_obj,
                                        map_var_name_geo_x=self.dim_name_geo_x, map_var_name_geo_y=self.dim_name_geo_y,
                                        fx_name=dst_fx_info[self.dst_fx_name_tag],
                                        fx_map=dst_fx_info[self.dst_fx_map_tag],
                                        fx_table=static_data_table_graph,
                                        tag_src_attributes=self.src_attrs_tag,
                                        tag_anl_attributes=self.anl_attrs_tag,
                                        tag_dst_attributes=self.dst_attrs_tag
                                    )

                                    driver_graph.compute_data()

                                    log_stream.info(' -------> Period "' +
                                                    anl_var_t_period + '"  ... DONE')

                                else:
                                    log_stream.info(' -------> Period "' +
                                                    anl_var_t_period + '"  ... SKIPPED. Graph is already saved')

                            log_stream.info(' ------> Variable "' + dst_var_key + '"  ... DONE')

                        else:
                            log_stream.warning(' ===> File paths for map destination key "' + dst_var_key +
                                               '" are not defined')
                    else:
                        log_stream.warning(' ===> Variable map for analysis key "' + anl_var_key + '" is not defined')

                log_stream.info(' -----> Dataset == Ref: "' + dst_type_key +
                                '" ... DONE')

            else:
                log_stream.info(' -----> Dataset == Ref: "' + dst_type_key +
                                '" ... SKIPPED. Datasets are not available')

        log_stream.info(' ----> Dump dynamic datasets [' + time_str + '] ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to merge attributes objects
    @staticmethod
    def merge_attrs_obj(dict_attr_base=None, dict_attr_list=None, dict_name_list=None):

        if (dict_attr_list is not None) and (dict_name_list is not None):

            if dict_attr_base is None:
                dict_attr_base = {}

            for dict_attr_step, dict_name_step in zip(dict_attr_list, dict_name_list):
                if dict_name_step not in list(dict_attr_base.keys()):
                    dict_attr_base[dict_name_step] = dict_attr_step
                else:
                    log_stream.warning(' ===> Merge datasets "' + dict_name_step +
                                       '" is not allowed; dict key is already set in the base dictionary.')

        dict_attr_merged = deepcopy(dict_attr_base)

        return dict_attr_merged

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to select attributes of different dict(s)
    @staticmethod
    def select_attrs_obj(dict_attr_base, dict_attr_file, reference_key='var_name_data'):

        for attr_base_key, attr_base_field in dict_attr_base.items():
            if attr_base_key == reference_key:
                for attr_file_key, attr_file_obj in dict_attr_file.items():
                    if isinstance(attr_file_obj, dict):
                        for attr_field_key, attr_field_value in attr_file_obj.items():
                            if attr_field_key == reference_key:
                                if attr_field_value == attr_base_field:
                                    dict_attr_select = deepcopy(attr_file_obj)
                                    break
        return dict_attr_select

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize dynamic data
    def analyze_dynamic_data(self, anc_file_collections):

        time_str = self.time_str
        time_reference = self.time_reference

        static_terrain_darray = self.static_data_terrain

        anl_info_variable = self.info_variable_anl
        anl_file_collections = self.anl_file_collections

        flag_dynamic_src = self.flag_cleaning_dynamic_src
        flag_dynamic_anl = self.flag_cleaning_dynamic_anl

        log_stream.info(' ----> Analyze dynamic datasets [' + time_str + '] ... ')

        if flag_dynamic_src:
            if not flag_dynamic_anl:
                log_stream.warning(
                    ' ===> Due to activation of dynamic source flag, analysis flag will be activated too')
                flag_dynamic_anl = True

        anl_file_database = {}
        for anl_type_key in self.anl_name_list:

            log_stream.info(' -----> Dataset == Ref: "' + anl_type_key + '" ... ')

            if anl_type_key in list(anc_file_collections.keys()):
                anc_file_path = anc_file_collections[anl_type_key]
            else:
                logging.error(' ===> Data source file path is not defined')
                raise IOError('File source for "' + anl_type_key + '" datasets is not defined')

            if anl_type_key in list(anl_file_collections.keys()):
                if anc_file_path is not None:
                    anl_file_obj = anl_file_collections[anl_type_key]
                    anl_file_path = list(anl_file_obj.values())[0][0]
                else:
                    anl_file_path = None
            else:
                logging.error(' ===> Data analysis file path is not defined')
                raise IOError('File analysis for "' + anl_type_key + '" datasets is not defined')

            if anl_type_key in list(anl_info_variable.keys()):
                anl_var_info = anl_info_variable[anl_type_key]
            else:
                logging.warning(' ===> Info analysis are not defined')
                anl_var_info = None

            if anc_file_path is not None:

                anc_file_obj = read_obj(anc_file_path)
                anc_file_dset = anc_file_obj[self.workspace_values]
                anc_file_attrs = anc_file_obj[self.workspace_attrs]

                if flag_dynamic_anl:
                    if os.path.exists(anl_file_path):
                        os.remove(anl_file_path)

                if not os.path.exists(anl_file_path):
                    var_workspace_darray = {}
                    var_workspace_attrs = {}
                    for var_info_key, var_info_attrs in anl_var_info.items():

                        log_stream.info(' ------> Analyze variable "' + var_info_key + '" ... ')

                        var_name_data = var_info_attrs[self.anl_var_name_data_tag]
                        var_name_analysis = var_info_attrs[self.anl_var_name_analysis_tag]

                        var_level = var_info_attrs[self.anl_var_level_tag]
                        var_mode = var_info_attrs[self.anl_var_mode_tag]
                        var_description = var_info_attrs[self.anl_var_description_tag]
                        var_temporal_window = var_info_attrs[self.anl_var_temporal_window_tag]
                        var_direction_window = var_info_attrs[self.anl_var_direction_window_tag]

                        if var_name_data in list(anc_file_dset.variables):

                            log_stream.info(' -------> Source: "' + var_name_data +
                                            '" - Analysis: "' + var_name_analysis +
                                            '" - Description: "' + var_description + '"... ')

                            var_darray_data = anc_file_dset[var_name_data]

                            log_stream.info(' --------> Apply method "' + var_mode + '" ... ')
                            if var_mode == 'accumulated':

                                # Call fx for computing accumulated values
                                var_collections_darray = var_cmp_accumulated(
                                    time_reference, var_darray_data, static_terrain_darray,
                                    var_temporal_window=var_temporal_window,
                                    var_temporal_direction=var_direction_window)

                            elif var_mode == 'average':

                                # Call fx for computing average values
                                var_collections_darray = var_cmp_average(
                                    time_reference, var_darray_data, static_terrain_darray,
                                    var_temporal_window=var_temporal_window,
                                    var_temporal_direction=var_direction_window)

                            elif var_mode == 'instantaneous':

                                var_collections_darray = var_cmp_instantaneous(
                                    time_reference, var_darray_data, static_terrain_darray,
                                    var_temporal_window=var_temporal_window,
                                    var_temporal_direction=var_direction_window)

                            else:
                                log_stream.error(' --------> Apply method "' + var_mode + '" ... FAILED')
                                log_stream.error(' ===> Analysis mode "' + var_mode + '" is not allowed')
                                raise NotImplemented('Case not implemented yet')

                            tmp_file_attrs = self.select_attrs_obj(
                                var_info_attrs, anc_file_attrs, reference_key='var_name_data')

                            var_collections_attrs = self.merge_attrs_obj(
                                dict_attr_list=[tmp_file_attrs, var_info_attrs],
                                dict_name_list=[self.src_attrs_tag, self.anl_attrs_tag])

                            var_workspace_darray[var_info_key] = var_collections_darray
                            var_workspace_attrs[var_info_key] = var_collections_attrs

                            log_stream.info(' --------> Apply method "' + var_mode + '" ... DONE')

                            log_stream.info(' -------> Source: "' + var_name_data +
                                            '" - Analysis: "' + var_name_analysis +
                                            '" - Description: "' + var_description + '" ... DONE')

                            log_stream.info(' ------> Analyze variable "' + var_info_key + '" ... DONE')
                        else:
                            log_stream.info(' ------> Analyze variable "' + var_info_key +
                                            '" ... SKIPPED. Datasets are not available')

                    folder_name_anl, file_name_anl = os.path.split(anl_file_path)
                    make_folder(folder_name_anl)

                    anl_ws = {
                        self.workspace_values: var_workspace_darray,
                        self.workspace_attrs: var_workspace_attrs}

                    write_obj(anl_file_path, anl_ws)

                    log_stream.info(' -----> Analyze datasets "' + anl_type_key + '" ... DONE')

                else:

                    log_stream.info(' -----> Analyze datasets "' + anl_type_key +
                                    '" ... SKIPPED. Datasets are already available')

            else:
                log_stream.info(' -----> Analyze datasets "' + anl_type_key +
                                '" ... SKIPPED. Datasets are not available')

            anl_file_database[anl_type_key] = anl_file_path

        log_stream.info(' ----> Analyze dynamic datasets [' + time_str + '] ... DONE')

        return anl_file_database

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize dynamic data
    def organize_dynamic_data(self):

        time_str = self.time_str

        var_terrain_data = self.tag_terrain_data

        src_file = self.src_file_filter
        anc_file_raw = self.anc_file_filter_raw
        anc_file_group = self.anc_file_filter_group

        limits_info_variable = self.info_variable_limits
        src_info_variable = self.info_variable_src
        src_info_time = self.info_time_src
        anl_info_variable = self.info_variable_anl

        static_terrain_darray = self.static_data_terrain

        folder_name_tmp = self.folder_tmp

        flag_dynamic_src = self.flag_cleaning_dynamic_src
        flag_dynamic_anl = self.flag_cleaning_dynamic_anl

        log_stream.info(' ----> Organize dynamic datasets [' + time_str + '] ... ')

        if flag_dynamic_anl:
            if not flag_dynamic_src:
                log_stream.warning(
                    ' ===> Due to activation of dynamic analysis flag, source flag will be activated too')
                flag_dynamic_src = True

        anc_file_database = {}
        for (src_type_key, src_series), (anc_type_key_raw, anc_series_raw),\
            (anc_type_key_group, anc_series_group) in zip(src_file.items(), anc_file_raw.items(),
                                                          anc_file_group.items()):

            src_data = src_info_variable[src_type_key]
            src_time = src_info_time[src_type_key]

            log_stream.info(' -----> Dataset == Ref: "' + src_type_key + '"  ... ')

            src_datetime_index = src_series.index
            src_file_obj = src_series.values
            anc_datetime_index_raw = anc_series_raw.index
            anc_file_obj_raw = anc_series_raw.values
            anc_datetime_index_group = anc_series_group.index
            anc_file_obj_group = anc_series_group.values

            src_time_search = src_time[self.src_time_search_file_tag]

            src_file_list = src_file_obj.tolist()
            anc_file_list_raw = anc_file_obj_raw.tolist()
            anc_file_name_group = anc_file_obj_group.tolist()[0]

            log_stream.info(' ------> Search period of selected datasets ... ')
            if not src_datetime_index.empty:
                end_datetime_index = src_datetime_index[0]
                start_datetime_index = src_datetime_index[-1]
                end_datetime_str = end_datetime_index.strftime(time_format_algorithm)
                start_datetime_str = start_datetime_index.strftime(time_format_algorithm)

                if start_datetime_index != end_datetime_index:
                    log_stream.info(' -------> Selected steps from "' +
                                    start_datetime_str + '" to "' + end_datetime_str + '"')
                else:
                    log_stream.info(' -------> Selected step "' + start_datetime_str + '"')
                log_stream.info(' ------> Search period of selected datasets ... DONE')
            else:
                log_stream.info(' ------> Search period of selected datasets ... FAILED')
                log_stream.warning(' ===> Datasets are not found in the expected time-period')

            if flag_dynamic_src:
                if os.path.exists(anc_file_name_group):
                    os.remove(anc_file_name_group)

            if not os.path.exists(anc_file_name_group):

                anc_file_collections_raw = []
                for src_time_step, src_file_step, anc_file_step_raw in zip(src_datetime_index, src_file_list, anc_file_list_raw):

                    log_stream.info(' ------> Get time "' + src_time_step.strftime(time_format_algorithm) + '" ... ')

                    if os.path.exists(anc_file_step_raw):
                        os.remove(anc_file_step_raw)

                    log_stream.info(' -------> Get datasets ... ')
                    if not os.path.exists(anc_file_step_raw):

                        src_var_map = {}
                        src_var_mode_list = []
                        for src_var_name, src_var_fields in src_data.items():
                            tmp_var_mode = src_var_fields[self.src_var_mode_tag]
                            tmp_file_name_step = src_var_fields[self.src_var_name_file_tag]
                            tmp_file_data_step = src_var_fields[self.src_var_name_data_tag]

                            src_var_map[tmp_file_data_step] = tmp_file_name_step
                            src_var_mode_list.append(tmp_var_mode)

                        src_var_mode = list(set(src_var_mode_list))
                        if isinstance(src_var_mode, list) and (src_var_mode.__len__() == 1):
                            src_var_mode = src_var_mode[0]
                        else:
                            log_stream.error(' ===> Dataset mode must be unique')
                            raise IOError('Dataset mode flag can be "deterministic" or "probabilistic"')

                        if src_var_mode == 'deterministic':
                            src_file_obj = read_file_gridded(src_file_step, folder_name_tmp=folder_name_tmp)
                        elif src_var_mode == 'probabilistic':
                            log_stream.error(' ===> Dataset mode "' + src_var_mode + ' is not included in the mode choice')
                            raise NotImplementedError('Case not implemented yet')
                        else:
                            log_stream.error(' ===> Dataset mode "' + src_var_mode + ' is not allowed')
                            raise NotImplementedError('Case not implemented yet')

                        if src_file_obj is not None:
                            src_file_dset = organize_file_gridded(
                                src_time_step, src_file_obj, src_var_map, static_terrain_darray,
                                data_limits_variables=limits_info_variable,
                                var_name_terrain=var_terrain_data,
                                var_dim_x=self.dim_name_geo_x , var_dim_y=self.dim_name_geo_y,
                                var_dim_time=self.dim_name_time,
                                var_coord_x=self.coord_name_geo_x, var_coord_y=self.coord_name_geo_y,
                                var_coord_time=self.coord_name_time,
                                var_dim_order_2d=self.dims_order_2d, var_dim_order_3d=self.dims_order_3d)

                            src_file_attrs = organize_attrs_gridded(src_file_dset, src_data, src_var_map)

                        else:
                            src_file_dset = None
                            src_file_attrs = None
                            logging.warning(" ===> Data collections is None")

                        if src_file_dset:
                            folder_name_step, file_name_step = os.path.split(anc_file_step_raw)
                            make_folder(folder_name_step)

                            anc_ws_raw = {self.workspace_values: src_file_dset, self.workspace_attrs: src_file_attrs}

                            write_obj(anc_file_step_raw, anc_ws_raw)

                            anc_file_collections_raw.append(anc_file_step_raw)
                            log_stream.info(' -------> Get datasets ... DONE')
                        else:

                            anc_file_collections_raw.append(None)
                            log_stream.warning(' ===> Datasets is None')
                            log_stream.info(' -------> Get datasets ... SKIPPED. Datasets is undefined')

                    else:

                        log_stream.info(' -------> Get datasets ... LOADED. Datasets is previously computed.')
                        anc_file_collections_raw.append(anc_file_step_raw)

                    log_stream.info(' ------> Get time "' + src_time_step.strftime(time_format_algorithm) + '" ... DONE')

                log_stream.info(' -------> Merge datasets ... ')
                if anc_file_collections_raw:

                    if src_time_search == 'first':
                        anc_file_collections_filter = anc_file_collections_raw[0]
                    elif src_time_search == 'all':
                        anc_file_collections_filter = anc_file_collections_raw
                    else:
                        log_stream.error(' ===> Data searching parameters "' + src_time_search + '" is not allowed')
                        raise NotImplementedError('Case not implemented yet')

                    anc_dset_collections, anc_attr_collections = merge_file_gridded(
                        anc_file_collections_filter,
                        var_name_terrain=var_terrain_data,
                        var_dim_x=self.dim_name_geo_x, var_dim_y=self.dim_name_geo_y,
                        var_dim_time=self.dim_name_time,
                        var_coord_x=self.coord_name_geo_x, var_coord_y=self.coord_name_geo_y,
                        var_coord_time=self.coord_name_time,
                        var_dim_order_2d=self.dims_order_2d, var_dim_order_3d=self.dims_order_3d
                    )

                    anc_ws_group = {
                        self.workspace_values: anc_dset_collections,
                        self.workspace_attrs: anc_attr_collections}

                    folder_name_group, file_name_group = os.path.split(anc_file_name_group)
                    make_folder(folder_name_group)

                    write_obj(anc_file_name_group, anc_ws_group)

                    for file_name_step in anc_file_collections_raw:
                        if os.path.exists(file_name_step):
                            os.remove(file_name_step)

                    log_stream.info(' -------> Merge datasets ... DONE')
                else:
                    anc_file_name_group = None
                    log_stream.info(' -------> Merge datasets ... FAILED. File collections is not defined')

                if anc_file_name_group is not None:
                    log_stream.info(' -----> Dataset == Ref: "' + src_type_key +
                                    '"  ... DONE')
                else:
                    log_stream.info(' -----> Dataset == Ref: "' + src_type_key +
                                    '"  ... FAILED. Datasets are not found in the time period ')

            else:

                log_stream.info(' -----> Dataset == Ref: "' + src_type_key +
                                '" ... SKIPPED. Datasets ara previously computed')

            anc_file_database[src_type_key] = anc_file_name_group

        log_stream.info(' ----> Organize dynamic datasets [' + time_str + '] ... DONE')

        return anc_file_database
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
