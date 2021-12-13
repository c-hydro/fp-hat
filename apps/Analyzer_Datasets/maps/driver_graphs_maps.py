"""
Library Features:

Name:          driver_graphs_maps
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180918'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import os
import inspect
import collections
import ast

from copy import deepcopy

from lib_utils_system import map_dict_by_list
from lib_graph_map_utils import read_map_table
import lib_graph_map_base as fx_collections_method

from lib_graph_map_ancillary import write_file_info_map, write_file_datasets_map
from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
#################################################################################


# -------------------------------------------------------------------------------------
# Class to graph time-series
class DriverGraph:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, file_name_graph=None,  file_name_info=None, file_name_datasets=None,
                 map_time_stamp=None, map_time_description=None,
                 map_obj=None, map_attrs=None,
                 map_color_map=None, map_color_label=None,
                 map_var_name_geo_x='longitude', map_var_name_geo_y='latitude',
                 fx_name=None, fx_attrs=None, fx_map=None, fx_table='table_graph_lut.json',
                 tag_src_attributes='data_attributes', tag_anl_attributes='analysis_attributes',
                 tag_dst_attributes='graph_attributes'):

        self.file_name_graph = file_name_graph
        self.file_name_info = file_name_info
        self.file_name_datasets = file_name_datasets

        self.map_obj = map_obj
        self.map_time_stamp = map_time_stamp
        self.map_time_description = map_time_description
        self.map_attrs = map_attrs
        self.map_color_map = map_color_map
        self.map_color_label = map_color_label
        self.fx_name = fx_name
        self.fx_attrs = fx_attrs
        self.fx_map = fx_map
        self.fx_table = fx_table

        self.fx_obj = self.get_fx_method()
        self.fx_map = self.get_fx_lut()

        self.tag_src_attributes = tag_src_attributes
        self.tag_anl_attributes = tag_anl_attributes
        self.tag_dst_attributes = tag_dst_attributes

        self.fx_map_common = 'common'
        self.fx_map_extra = 'args'
        self.fx_map_delimiter = ':'

        self.var_name_geo_x = map_var_name_geo_x
        self.var_name_geo_y = map_var_name_geo_y

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get fx object
    def get_fx_method(self):

        fx_collections_methods = [fx_collections_method]

        fx_obj = None
        for fx_collections_step in fx_collections_methods:
            if hasattr(fx_collections_step, self.fx_name):
                fx_obj = getattr(fx_collections_step, self.fx_name)
                break

        if fx_obj is None:
            log_stream.error(' ===> Fx method is not available in the fx collection methods')
            raise RuntimeError('Method not defined in the selected fx collection methods')

        return fx_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get fx lut
    def get_fx_lut(self):

        fx_table = self.fx_table

        if isinstance(fx_table, str):
            if os.path.exists(fx_table):
                fx_collections_methods = read_map_table(fx_table)
            else:
                log_stream.error(' ===> Fx table "' + fx_table + '" does not exist.')
                raise IOError('Fx table is not available in the selected location')
        elif isinstance(fx_table, dict):
            fx_collections_methods = deepcopy(fx_table)
        else:
            log_stream.error(' ===> Fx table object is not allowed.')
            raise NotImplemented('Case not implemented yet')

        if self.fx_map in list(fx_collections_methods.keys()):
            fx_lut = fx_collections_methods[self.fx_map]
        else:
            log_stream.error(' ===> Fx lut is not available in the fx collection lut')
            raise RuntimeError('Lut not defined in the selected fx collection lut')

        return fx_lut

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to merge fx attributes
    @staticmethod
    def merge_fx_attributes(fx_collections, extra_attributes_collections=None,
                            tag_ts_file_attributes='file_attributes'):

        fx_collections_upd = deepcopy(fx_collections)
        fx_attributes_collection = fx_collections_upd[tag_ts_file_attributes]

        if extra_attributes_collections is not None:
            for attr_key, attr_value in extra_attributes_collections.items():
                if attr_key not in list(fx_attributes_collection.keys()):
                    fx_attributes_collection[attr_key] = attr_value
                else:
                    log_stream.warning(' ===> Attributes "' + attr_key +
                                       '" is already saved in fx attributes collections')

        fx_attributes_collection_ordered = collections.OrderedDict(sorted(fx_attributes_collection.items()))

        fx_collections_upd[tag_ts_file_attributes] = fx_attributes_collection_ordered

        return fx_collections_upd

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to write fx info
    @staticmethod
    def write_fx_info(file_name_info, file_data_info):
        if file_name_info is not None:
            write_file_info_map(file_name_info, file_data_info)
        else:
            log_stream.warning(' ===> File info is not defined')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to write fx datasets
    @staticmethod
    def write_fx_datasets(file_name_datasets, file_data_datasets):
        if file_name_datasets is not None:
            write_file_datasets_map(file_name_datasets, file_data_datasets)
        else:
            log_stream.warning(' ===> File datasets is not defined')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to fill fx args included in fx signature
    @staticmethod
    def fill_fx_args(fx_signature, fx_data, fx_sep=','):

        fx_parameters_list_no_def = []
        fx_parameters_list_no_value = []
        for fx_parameter in fx_signature.parameters.values():
            fx_parameter_name = fx_parameter.name
            fx_parameter_default = fx_parameter.default

            if fx_parameter_name not in list(fx_data.keys()):
                if fx_parameter_default is not inspect._empty:
                    fx_data[fx_parameter_name] = fx_parameter_default

                    fx_parameters_list_no_def.append(fx_parameter_name)
                else:
                    fx_data[fx_parameter_name] = None
                    fx_parameters_list_no_value.append(fx_parameter_name)

        if fx_parameters_list_no_def.__len__() > 0:
            fx_parameters_str_no_def = fx_sep.join(fx_parameters_list_no_def)
            log_stream.warning(' ===> Fx parameters "' + fx_parameters_str_no_def +
                               '" not defined; fx will use a default value')

        if fx_parameters_list_no_value.__len__() > 0:
            fx_parameters_str_no_value = fx_sep.join(fx_parameters_list_no_value)
            log_stream.warning(' ===> Fx parameters "' + fx_parameters_str_no_value +
                               '" not defined; fx will use a null value')

        return fx_data

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to remove fx args not included in fx signature
    @staticmethod
    def pop_fx_args(fx_signature, fx_data):

        fx_data_tmp = deepcopy(fx_data)
        for fx_key_tmp in fx_data_tmp.keys():
            if fx_key_tmp not in list(fx_signature.parameters.keys()):
                fx_data.pop(fx_key_tmp, None)

        return fx_data
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set fx argument(s)
    def set_fx_args(self, fx_attrs_common=None, fx_attrs_extra=None):

        fx_map_extra = self.fx_map[self.fx_map_extra]
        fx_map_common = self.fx_map[self.fx_map_common]

        fx_map_filled = {}
        for map_key, map_path in fx_map_extra.items():

            map_list = map_path.split(self.fx_map_delimiter)
            map_value_raw = map_dict_by_list(fx_attrs_extra, map_list)

            if map_value_raw is not None:
                if "var_limit_min" == map_key:
                    tmp_value = map_value_raw.split(',')[0]
                    if ast.literal_eval(tmp_value) is None:
                        map_value_raw = None
                    else:
                        map_value_raw = float(tmp_value)
                if "var_limit_max" == map_key:
                    tmp_value = map_value_raw.split(',')[1]
                    if ast.literal_eval(tmp_value) is None:
                        map_value_raw = None
                    else:
                        map_value_raw = float(tmp_value)

                map_value_def = map_value_raw
            else:
                map_value_def = None

            fx_map_filled[map_key] = map_value_def

        for map_key, map_path in fx_map_common.items():

            if map_path in list(fx_attrs_common.keys()):
                map_value = fx_attrs_common[map_path]
            else:
                map_value = None

            fx_map_filled[map_key] = map_value

        return fx_map_filled

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable data
    def compute_data(self):

        # Get the time-series filename
        file_name_graph = self.file_name_graph
        file_name_info = self.file_name_info
        file_name_datasets = self.file_name_datasets

        # Get map obj and attributes
        fx_map_time_stamp = self.map_time_stamp
        fx_map_time_description = self.map_time_description
        fx_map_obj = self.map_obj
        fx_map_attrs = self.map_attrs
        fx_map_color_map = self.map_color_map
        fx_map_color_label = self.map_color_label

        # Check the function availability
        if self.fx_obj:

            # Get fx signature
            fx_signature = inspect.signature(self.fx_obj)

            # Set fx attributes
            fx_map_attrs_common = {
                'file_name': file_name_graph,
                'fx_map_obj': fx_map_obj, 'fx_map_time': fx_map_time_stamp,
                'fx_geo_x': self.var_name_geo_x, 'fx_geo_y': self.var_name_geo_y,
                'fx_map_color_map': fx_map_color_map, 'fx_map_color_label': fx_map_color_label}
            fx_map_attrs_extra = deepcopy(fx_map_attrs)

            # Create fx data
            fx_map_collections = self.set_fx_args(
                fx_attrs_common=fx_map_attrs_common,
                fx_attrs_extra=fx_map_attrs_extra
            )

            # Write fx info
            self.write_fx_info(file_name_info, fx_map_attrs_extra)
            # Write fx datasets
            self.write_fx_datasets(file_name_datasets, fx_map_obj)

            # Fill and pop fx data
            fx_map_collections = self.fill_fx_args(fx_signature, fx_map_collections)
            fx_map_collections = self.pop_fx_args(fx_signature, fx_map_collections)

            # Execute fx method
            self.fx_obj(**fx_map_collections)

        else:
            log_stream.error(' ===> Fx method is not defined. Fx results will be null')
            raise RuntimeError('Method is not defined. Exit.')

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
