"""
Library Features:

Name:          cpl_data_variables_ws
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
import pandas as pd

from copy import deepcopy

from lib_graph_ts_utils import read_ts_table
import lib_graph_ts_obs as fx_collections_method_obs
import lib_graph_ts_nwp as fx_collections_method_nwp

from lib_graph_ts_ancillary import write_file_info_ts, write_file_datasets_ts
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
                 ts_obj=None, ts_deps=None,
                 fx_name=None, fx_attrs=None, fx_map=None, fx_table='table_graph_lut.json'):

        self.file_name_graph = file_name_graph
        self.file_name_info = file_name_info
        self.file_name_datasets = file_name_datasets

        self.ts_obj = ts_obj
        self.ts_deps = ts_deps
        self.fx_name = fx_name
        self.fx_attrs = fx_attrs
        self.fx_map = fx_map
        self.fx_table = fx_table

        self.fx_obj = self.get_fx_method()
        self.fx_map = self.get_fx_lut()

        self.tag_filename = 'filename'
        self.tag_datasets = 'datasets'
        self.tag_attributes = 'attributes'

        self.fx_mode_tags = ['reference', 'other']

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get fx object
    def get_fx_method(self):

        fx_collections_methods = [fx_collections_method_obs, fx_collections_method_nwp]

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
                fx_collections_methods = read_ts_table(fx_table)
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
            log_stream.error(' ===> Fx lut "' + self.fx_map + '" is not available in the fx collection lut')
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
            write_file_info_ts(file_name_info, file_data_info)
        else:
            log_stream.warning(' ===> File info is not defined')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to write fx datasets
    @staticmethod
    def write_fx_datasets(file_name_datasets, file_data_datasets):
        if file_name_datasets is not None:
            write_file_datasets_ts(file_name_datasets, file_data_datasets)
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
    def set_fx_args(self, ts_obj, ts_signature=None, ts_attrs_extra=None,
                    ts_extra_options=None):

        fx_args_datasets = {}
        fx_args_attributes = {}
        fx_args_ancillary = {}

        ts_mode_list = []
        for ts_key, ts_fields in self.ts_deps.items():

            ts_type = ts_fields['type']
            ts_mode = ts_fields['mode']

            if (ts_mode == 'reference') and (ts_mode not in ts_mode_list):
                ts_mode_list.append(ts_mode)
            elif ts_mode == 'other':
                pass
            elif (ts_mode == 'reference') and (ts_mode in ts_mode_list):
                log_stream(' ===> Mode "reference" is defined for multiple datasets.')
                raise NotImplementedError('Case not implemented yet')
            else:
                log_stream(' ===> Unexpected error in time-series mode definition.')
                raise RuntimeError('Check your time-series mode definitions')

            if ts_mode not in self.fx_mode_tags:
                log_stream.error(' ===> Mode "' + ts_mode +
                                 '" not included in allowed mode tags [' + ','.join(self.fx_mode_tags) + ']')
                raise NotImplementedError('Case not implemented yet')

            if ts_type in list(self.fx_map.keys()):

                if ts_type in list(self.fx_map.keys()):
                    ts_var_mapping = self.fx_map[ts_type]
                else:
                    log_stream.error(' ===> Mapping "' + ts_type + '" part is not defined')
                    raise NotImplementedError('Case not implemented yet')

            else:
                log_stream.error(' ===> Mapping type is not defined')
                raise RuntimeError('Method arguments are not defined')

            ts_attributes = ts_obj[ts_key][self.tag_attributes]
            ts_datasets = ts_obj[ts_key][self.tag_datasets]

            ts_time_period = None
            for var_out, var_in in ts_var_mapping.items():
                if var_in in list(ts_attributes.keys()):
                    ts_attrs = ts_attributes[var_in]

                    # Add extra attributes (defined by fx)
                    if ts_attrs_extra is not None:
                        for attr_key, attr_value in ts_attrs_extra.items():
                            if attr_key not in list(ts_attrs.keys()):
                                ts_attrs[attr_key] = attr_value
                            else:
                                log_stream.warning(' ===> Attributes "' + attr_key +
                                                   '" is already saved in fx attributes collections')
                    if ts_time_period is None:
                        ts_time_period = ts_attrs['time_period']

                    fx_args_attributes[var_out] = collections.OrderedDict(sorted(ts_attrs.items()))

            for var_out, var_in in ts_var_mapping.items():

                if var_in in list(ts_datasets.keys()):
                    ts_var = ts_datasets[var_in]

                    if ts_time_period is not None:
                        ts_dframe = pd.DataFrame(data=ts_var, index=ts_time_period)
                    else:
                        log_stream.error(' ===> TimePeriod is not defined to create dataframe TimeSeries')
                        raise RuntimeError('TimePeriod must be defined in the dataframe')

                    if var_out not in list(fx_args_datasets.keys()):
                        fx_args_datasets[var_out] = ts_dframe

                    if var_out in list(fx_args_datasets.keys()) and ts_mode == 'reference':
                        log_stream.warning(
                            ' ===> Variable "' + var_out + '" is already saved in fx datasets but derived from '
                                                           '"other" datasets. \n For this reason variable will be '
                                                           'updated using the "reference" datasets \n')
                        fx_args_datasets[var_out] = ts_dframe

        if 'common' in self.fx_map.keys():
            fx_common = self.fx_map['common']
            for fx_key, fx_value in fx_common.items():
                if ts_signature is not None:
                    if fx_key in list(ts_signature.parameters.keys()):
                        if fx_key in list(ts_extra_options.keys()):
                            fx_value_select = ts_extra_options[fx_key]
                        else:
                            fx_value_select = fx_value
                        fx_args_datasets[fx_key] = fx_value_select
        else:
            log_stream.warning(' ===> Mapping "common" part is not defined')

        fx_args_datasets_collections = {**fx_args_datasets, **fx_args_ancillary, **fx_args_attributes}
        fx_args_attributes_collections = {**fx_args_attributes}

        return fx_args_datasets_collections, fx_args_attributes_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable data
    def compute_data(self):

        # Get the time-series filename
        file_name_graph = self.file_name_graph
        file_name_info = self.file_name_info
        file_name_datasets = self.file_name_datasets

        # Get time-series datasets
        ts_obj = self.ts_obj

        # Check the function availability
        if self.fx_obj:

            # Get fx signature
            fx_signature = inspect.signature(self.fx_obj)

            # Create fx data
            fx_ts_collections, fx_ts_attributes = self.set_fx_args(
                ts_obj, ts_signature=fx_signature, ts_attrs_extra=self.fx_attrs,
                ts_extra_options={'file_name': file_name_graph}
            )

            # Write fx info
            self.write_fx_info(file_name_info, fx_ts_attributes)
            # Write fx datasets
            self.write_fx_datasets(file_name_datasets, fx_ts_collections)

            # Fill and pop fx data
            fx_ts_collections = self.fill_fx_args(fx_signature, fx_ts_collections)
            fx_ts_collections = self.pop_fx_args(fx_signature, fx_ts_collections)

            # Execute fx method
            self.fx_obj(**fx_ts_collections)

        else:
            log_stream.error(' ===> Fx method is not defined. Fx results will be null')
            raise RuntimeError('Method is not defined. Exit.')

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
