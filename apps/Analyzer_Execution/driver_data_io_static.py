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
import pandas as pd

from copy import deepcopy

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
        self.filter_tag = 'filter'

        # get domain name information
        self.domain_name_list = self.alg_ancillary['domain_name']
        if not isinstance(self.domain_name_list, list):
            self.domain_name_list = [self.domain_name_list]

        self.section_data_file, self.section_data_filter = self.define_section_data()

        self.execution_data = self.src_dict[self.flag_execution_data]

        self.flag_cleaning_static = flag_cleaning_static

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to define section data
    def define_section_data(self):

        domain_name_list = self.domain_name_list
        src_dict = self.src_dict

        if domain_name_list.__len__() > 1:
            for domain_name_step in domain_name_list:
                if domain_name_step not in list(src_dict[self.flag_section_data].keys()):
                    log_stream.error(' ===> Domain "' + domain_name_step + '" is not defined in the source data obj')
                    raise RuntimeError('All the domains must be defined in the source data obj')

        # case for domain or multi-domains declared in the source dictionary
        section_data_dict, filter_data_dict = None, None
        for domain_name_step in domain_name_list:
            if domain_name_step in list(src_dict[self.flag_section_data].keys()):

                if section_data_dict is None:
                    section_data_dict = {}
                if filter_data_dict is None:
                    filter_data_dict = {}

                folder_name_step = src_dict[self.flag_section_data][domain_name_step][self.folder_name_tag]
                file_name_step = src_dict[self.flag_section_data][domain_name_step][self.file_name_tag]
                file_path_step = os.path.join(folder_name_step, file_name_step)

                if self.filter_tag in list(src_dict[self.flag_section_data][domain_name_step].keys()):
                    filter_data_step = src_dict[self.flag_section_data][domain_name_step][self.filter_tag]
                else:
                    filter_data_step = None

                section_data_dict[domain_name_step] = file_path_step
                filter_data_dict[domain_name_step] = filter_data_step

        # case for single domain not declared in the source dictionary
        if (section_data_dict is None) and (domain_name_list.__len__() == 1):

            domain_name_step = domain_name_list[0]

            folder_name_step = src_dict[self.flag_section_data][self.folder_name_tag]
            file_name_step = src_dict[self.flag_section_data][self.file_name_tag]
            file_path_step = os.path.join(folder_name_step, file_name_step)

            filter_data_step = src_dict[self.flag_section_data][domain_name_step][self.filter_tag]

            if section_data_dict is None:
                section_data_dict = {}
            section_data_dict[domain_name_step] = {}
            section_data_dict[domain_name_step] = file_path_step
            if filter_data_dict is None:
                filter_data_dict = {}
            filter_data_dict[domain_name_step] = {}
            filter_data_dict[domain_name_step] = filter_data_step
        elif section_data_dict is not None:
            pass
        else:
            log_stream.error(' ===> Section data is not defined and the size of the domain list is not supported')
            raise NotImplemented('Case not implemented yet')

        for domain_name_step in domain_name_list:
            if domain_name_step not in list(section_data_dict.keys()):
                log_stream.error(' ===> Domain "' + domain_name_step + '" is not defined in the section data obj')
                raise RuntimeError('All the domains must be defined in the section data obj')

        return section_data_dict, filter_data_dict

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to organize section data
    def organize_section_data(self, tag_db='reference_db'):

        # iterate over domain(s)
        dframe_section_merged = None
        for (section_dset_name_file, section_dset_file_path), (section_dset_name_filter, section_dset_filter) \
                in zip(self.section_data_file.items(), self.section_data_filter.items()):

            log_stream.info(' -----> Domain reference "' + section_dset_name_file + '" ... ')

            assert section_dset_name_file == section_dset_name_filter, ' key of file and filter fields must be the same'

            dframe_section_step = read_file_section_data(section_dset_file_path)
            dframe_section_step[tag_db] = section_dset_name_file

            update_section_tag = False
            if 'section_tag' in list(dframe_section_step.columns):
                section_tag_check = dframe_section_step['section_tag'][0]
                if ':' not in section_tag_check:
                    update_section_tag = True
            else:
                update_section_tag = True
            if update_section_tag:
                log_stream.warning(' ===> The column "section_tag" is not in the correct format. '
                                   'The column will be updated by the expected fields format.')
                section_catch_list = dframe_section_step['section_catchment'].values
                section_name_list = dframe_section_step['section_name'].values

                section_tag_list = ["{}:{}".format(elem_a, elem_b)
                                    for elem_a, elem_b in zip(section_catch_list, section_name_list)]

                dframe_section_step['section_tag'] = section_tag_list

            if section_dset_filter is not None:
                section_column_filter = list(section_dset_filter.keys())[0]
                section_value_filter = list(section_dset_filter.values())[0]

                if section_column_filter in list(dframe_section_step.columns):
                    dframe_section_step = dframe_section_step.loc[
                        dframe_section_step[section_column_filter] == section_value_filter]
                else:
                    log_stream.warning(' ===> The filter key "' + section_column_filter +
                                       '" is not available in the section dataframe. Filter is not activated')

                if dframe_section_step.empty:
                    log_stream.warning(' ===> The filter key "' + section_column_filter +
                                       '" and the value key "' + str(section_value_filter) +
                                       '" returned an empty dataframe')

            if dframe_section_merged is None:
                dframe_section_merged = deepcopy(dframe_section_step)
            else:
                dframe_section_merged = pd.concat([dframe_section_merged, dframe_section_step])

            log_stream.info(' -----> Domain reference "' + section_dset_name_file + '" ... DONE')

        return dframe_section_merged

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize geographical data
    def organize_static(self):

        # Info start
        log_stream.info(' ---> Organize static datasets ... ')

        # Data collection object
        dframe_collections = {}

        # Organize sections datasets
        log_stream.info(' ----> Sections datasets ... ')
        # Organize section datasets
        dframe_section = self.organize_section_data()
        # Filter section datasets
        dframe_section = filter_file_section_data(
            dframe_section, field_value_list=self.domain_name_list, field_tag='reference_db')
        log_stream.info(' ----> Sections datasets ... DONE')

        # Read execution dataset
        log_stream.info(' ----> Executions datasets ... ')
        dframe_execution = read_file_execution_data(self.execution_data)
        log_stream.info(' ----> Executions datasets ... DONE')

        # Collect datasets in a common object
        dframe_collections[self.flag_section_data] = dframe_section
        dframe_collections[self.flag_execution_data] = dframe_execution

        # Info end
        log_stream.info(' ---> Organize static datasets ... DONE')

        return dframe_collections
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
