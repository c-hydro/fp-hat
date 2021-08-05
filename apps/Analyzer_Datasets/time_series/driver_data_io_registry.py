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

from lib_data_io_csv import write_file_registry_ts, read_file_registry_ts
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
                 src_dict, dst_dict=None,
                 static_data_collection=None,
                 alg_ancillary=None, alg_template=None,
                 tag_section_data='sections',
                 tag_static_source='source', tag_static_destination='destination',
                 flag_cleaning_registry=True):

        self.time_reference = time_reference

        self.tag_section_data = tag_section_data
        self.tag_static_source = tag_static_source
        self.tag_static_destination = tag_static_destination

        self.alg_ancillary = alg_ancillary
        self.alg_template_run = alg_template['run']
        self.alg_template_time = alg_template['time']
        self.alg_template_registry = alg_template['registry']

        self.section_name_type = ['River']

        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'

        self.static_data_section = static_data_collection[self.tag_section_data]

        dst_registry_dict = dst_dict['registry']
        dst_plot_dict = dst_dict['collections']['plot']

        folder_name_registry = dst_registry_dict[self.folder_name_tag]
        file_name_registry = dst_registry_dict[self.file_name_tag]

        self.file_path_registry = self.define_file_name(folder_name_registry, file_name_registry)

        self.flag_cleaning_registry = flag_cleaning_registry

        self.plot_name_tag = "graph_tag_name"
        self.str_delimiter_first_order = ';'
        self.str_delimiter_second_order = ','

        self.point_tag_registry = self.define_registry_tag(name_type=self.section_name_type)
        self.point_tag_plot = self.define_plot_tag(dst_plot_dict, dst_field=self.plot_name_tag)

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
    # Method to define plot tags
    @staticmethod
    def define_plot_tag(dst_dict, dst_field=None):
        if dst_field is None:
            dst_field = 'tag_name'
        dst_values = extract_dict_values(dst_dict, dst_field)
        return dst_values

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define registry tags
    def define_registry_tag(self, name_lower=True, name_type=None, name_capitalize=True):

        if name_lower:
            section_domain = self.static_data_section['section_domain'].str.lower()
        else:
            section_domain = self.static_data_section['section_domain']
        section_type = self.static_data_section['section_type']

        if name_type is None:
            name_type = ['River']

        run_point_domain_list = section_domain.values.tolist()
        run_point_type_list = section_type.values.tolist()

        point_tag_registry = []
        for run_point_domain_step, run_point_type_step in zip(run_point_domain_list, run_point_type_list):
            if name_capitalize:
                run_point_domain_step = run_point_domain_step.capitalize()
            if run_point_type_step in name_type:
                point_tag_registry.append(run_point_domain_step)
        point_tag_registry = sorted(list(set(point_tag_registry)))

        return point_tag_registry

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

            pnt_tag_registry = self.point_tag_registry
            pnt_tag_plot = self.point_tag_plot

            str_delimiter_first_order = self.str_delimiter_first_order
            str_delimiter_second_order = self.str_delimiter_second_order

            plot_list = str_delimiter_second_order.join(pnt_tag_plot)

            registry_data_collections = []
            for tag_registry_step in pnt_tag_registry:
                registry_row = str_delimiter_first_order.join([tag_registry_step, plot_list])
                registry_data_collections.append(registry_row)

            # Write info datasets
            folder_name_info, file_name_info = os.path.split(file_path_registry)
            make_folder(folder_name_info)

            write_file_registry_ts(file_path_registry, registry_data_collections)

            # Info end
            log_stream.info(' ----> Organize registry datasets ... DONE')

        else:
            # Read registry datasets
            registry_data_collections = read_file_registry_ts(file_path_registry)
            # Info end
            log_stream.info(' ----> Organize registry datasets ... LOADED. Registry datasets created previously')

        return registry_data_collections
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


