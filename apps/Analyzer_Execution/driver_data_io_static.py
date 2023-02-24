"""
Class Features

Name:          driver_data_io_static
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""

######################################################################################
# Library
import logging
import os

from lib_data_io_shapefile import read_file_section_data, filter_file_section_data
from lib_utils_exec import read_file_execution_data

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
######################################################################################


# -------------------------------------------------------------------------------------
# Class DriverStatic
class DriverStatic:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, src_dict, dst_dict=None,
                 alg_ancillary=None, alg_template_tags=None,
                 flag_section_data='section_data', flag_execution_data='execution_data',
                 flag_domain_collections='domain_collection',
                 flag_cleaning_static=True):

        self.src_dict = src_dict

        self.flag_section_data = flag_section_data
        self.flag_execution_data = flag_execution_data

        self.flag_domain_collections = flag_domain_collections

        self.alg_ancillary = alg_ancillary

        self.alg_template_tags = alg_template_tags
        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'

        # get domain name information
        self.domain_name_list = self.alg_ancillary['domain_name']
        if not isinstance(self.domain_name_list, list):
            self.domain_name_list = [self.domain_name_list]

        self.folder_name_section = self.src_dict[self.flag_section_data][self.folder_name_tag]
        self.file_name_section = self.src_dict[self.flag_section_data][self.file_name_tag]
        self.file_path_section = os.path.join(self.folder_name_section, self.file_name_section)

        self.execution_data = self.src_dict[self.flag_execution_data]

        self.flag_cleaning_static = flag_cleaning_static

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize geographical data
    def organize_static(self):

        # Info start
        log_stream.info(' ---> Organize static datasets ... ')

        # Data collection object
        dframe_collections = {}

        # Read section dataset
        dframe_section = read_file_section_data(self.file_path_section)
        dframe_section = filter_file_section_data(
            dframe_section, field_value_list=self.domain_name_list, field_tag='domain_name')
        # Read execution dataset
        dframe_execution = read_file_execution_data(self.execution_data)

        # Collect datasets in a common object
        dframe_collections[self.flag_section_data] = dframe_section
        dframe_collections[self.flag_execution_data] = dframe_execution

        # Info end
        log_stream.info(' ---> Organize static datasets ... DONE')

        return dframe_collections
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
