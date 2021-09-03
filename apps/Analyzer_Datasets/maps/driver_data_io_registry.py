"""
Class Features

Name:          driver_data_io_registry
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210429'
Version:       '1.0.0'
"""

######################################################################################
# Library
import logging
import os
import numpy as np

from copy import deepcopy

from lib_data_io_csv import write_file_registry, read_file_registry
from lib_utils_system import make_folder, extract_dict_values, fill_tags2string

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
######################################################################################


# -------------------------------------------------------------------------------------
# Class DriverRegistry
class DriverRegistry:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, time_reference,
                 src_dict, anl_dict=None, dst_dict=None,
                 static_data_collection=None,
                 alg_ancillary=None, alg_template=None,
                 tag_static_source='source', tag_static_destination='destination',
                 flag_cleaning_registry=True):

        self.time_reference = time_reference

        self.tag_static_source = tag_static_source
        self.tag_static_destination = tag_static_destination

        self.alg_ancillary = alg_ancillary
        self.alg_template_run = alg_template['data']
        self.alg_template_time = alg_template['time']
        self.alg_template_registry = alg_template['registry']

        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'

        dst_registry_dict = dst_dict['registry']
        dst_plot_dict = dst_dict['collections']['plot']
        dst_analysis_dict = anl_dict

        folder_name_registry = dst_registry_dict[self.folder_name_tag]
        file_name_registry = dst_registry_dict[self.file_name_tag]

        self.file_path_registry = self.define_file_name(folder_name_registry, file_name_registry)

        self.flag_cleaning_registry = flag_cleaning_registry

        self.tag_var_name = "var_name_graph"
        self.tag_var_level = 'var_level'
        self.str_delimiter_order = ';'

        self.map_registry_tag = self.define_registry_tag(
            ref_dict=dst_plot_dict, ref_fields=self.tag_var_name,
            other_dict=dst_analysis_dict, other_fields=self.tag_var_level)

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect ancillary file
    def define_file_name(self, folder_name_raw, file_name_raw):

        time_reference = self.time_reference

        alg_template_registry = {
            'registry_sub_path': time_reference, 'registry_datetime': time_reference}

        folder_name_def = fill_tags2string(folder_name_raw, self.alg_template_time, alg_template_registry)
        file_name_def = fill_tags2string(file_name_raw, self.alg_template_time, alg_template_registry)

        file_path_def = os.path.join(folder_name_def, file_name_def)

        return file_path_def

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define registry tags
    def define_registry_tag(self, ref_dict=None, ref_fields=None, other_dict=None, other_fields=None):

        if ref_fields is None:
            ref_fields = ['level']
        if other_fields is None:
            other_fields = None

        if ref_fields is not None:
            if not isinstance(ref_fields, list):
                ref_fields = [ref_fields]
        if other_fields is not None:
            if not isinstance(other_fields, list):
                other_fields = [other_fields]

        ref_values = []
        for id_field, name_field in enumerate(ref_fields):
            values_field = extract_dict_values(ref_dict, name_field)
            ref_values.append(values_field)
        ref_id = deepcopy(id_field)

        other_values = []
        if other_fields is not None:
            for id_field, name_field in enumerate(other_fields):
                values_field = extract_dict_values(other_dict, name_field)
                other_values.append(values_field)
        else:
            id_field = None
        other_id = deepcopy(id_field)

        dict_values = {}
        for id_step in np.arange(0, other_id + 1):
            for ref_value, other_value in zip(ref_values[0], other_values[id_step]):

                if ref_value not in list(dict_values.keys()):
                    dict_values[ref_value] = {}
                    dict_values[ref_value] = self.str_delimiter_order.join([ref_value, other_value])
                else:
                    tmp_values = dict_values[ref_value]
                    update_values = self.str_delimiter_order.join([tmp_values, other_value])
                    dict_values[ref_value] = update_values

        return dict_values

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize registry data
    def organize_registry(self):

        # Info start
        log_stream.info(' ----> Organize registry datasets ... ')

        flag_cleaning_registry = self.flag_cleaning_registry
        file_path_registry = self.file_path_registry
        if flag_cleaning_registry:
            if os.path.exists(file_path_registry):
                os.remove(file_path_registry)

        # Read gridded static data source
        if not os.path.exists(file_path_registry):

            map_registry_tag = self.map_registry_tag

            registry_data_collections = []
            for map_registry_row in map_registry_tag.values():
                registry_data_collections.append(map_registry_row)

            # Write info datasets
            folder_name_info, file_name_info = os.path.split(file_path_registry)
            make_folder(folder_name_info)

            write_file_registry(file_path_registry, registry_data_collections)

            # Info end
            log_stream.info(' ----> Organize registry datasets ... DONE')

        else:
            # Read registry datasets
            registry_data_collections = read_file_registry(file_path_registry)
            # Info end
            log_stream.info(' ----> Organize registry datasets ... LOADED. Registry datasets created previously')

        return registry_data_collections
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


