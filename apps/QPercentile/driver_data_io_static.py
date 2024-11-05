"""
Class Features

Name:          driver_data_io_static
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210429'
Version:       '1.0.0'
"""

######################################################################################
# Library
import logging
import os
from copy import deepcopy

from lib_data_geo_ascii import read_data_grid
from lib_data_io_pickle import write_obj

from lib_utils_system import fill_tags2string, make_folder, join_path
from lib_utils_geo import search_channel_network_idx

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
                 alg_info=None, alg_template=None,
                 flag_cnet_data='channel_network', flag_idx_data='idx',
                 flag_watermark_data='watermark',
                 flag_geo_data='geo', flag_clean_static=True):

        self.flag_cnet_data = flag_cnet_data
        self.flag_idx_data = flag_idx_data
        self.flag_watermark_data = flag_watermark_data
        self.flag_geo_data = flag_geo_data

        self.alg_info = alg_info
        self.alg_template = alg_template

        self.file_name_tag, self.folder_name_tag = 'file_name', 'folder_name'
        self.dset_variable_tag, self.dset_format_tag = 'variable', 'format'

        self.obj_domain_name = self.alg_info['domains']
        self.obj_run_name = self.alg_info['run']
        self.obj_quantile = self.alg_info['quantile']
        self.obj_ensemble = self.alg_info['ensemble']
        self.ensemble_n_min, self.ensemble_n_max = self.obj_ensemble['n_min'], self.obj_ensemble['n_max']
        self.ensemble_format = self.obj_ensemble['n_format']

        folder_name_cnet_src = src_dict[self.flag_cnet_data][self.folder_name_tag]
        file_name_cnet_src = src_dict[self.flag_cnet_data][self.file_name_tag]
        self.file_path_cnet_src = join_path(folder_name_cnet_src, file_name_cnet_src)

        folder_name_watermark_src = src_dict[self.flag_watermark_data][self.folder_name_tag]
        file_name_watermark_src = src_dict[self.flag_watermark_data][self.file_name_tag]
        self.file_path_watermark_src = join_path(folder_name_watermark_src, file_name_watermark_src)

        folder_name_dst = dst_dict[self.folder_name_tag]
        file_name_dst = dst_dict[self.file_name_tag]
        self.file_path_dst = join_path(folder_name_dst, file_name_dst)

        self.flag_clean_static = flag_clean_static

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define static filename
    @staticmethod
    def define_file_name(file_name_raw, tags_template=None, tags_filled=None):
        if tags_filled is None or tags_filled is None:
            log_stream.warning(' ===> The variable(s) "tags_template" or "tags_filled" is/are defined by NoneType')
            file_name_filled = deepcopy(file_name_raw)
        else:
            file_name_filled = fill_tags2string(file_name_raw, tags_template, tags_filled)
        return file_name_filled

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize static data
    def organize_static(self):

        # info start
        log_stream.info(' ----> Organize static datasets ... ')

        # get domains list
        domain_list = self.obj_domain_name
        # get file name
        file_path_src_cnet_raw = self.file_path_cnet_src
        file_path_src_watermark_raw = self.file_path_watermark_src
        file_path_dst_raw = self.file_path_dst
        # get flags
        flag_clean_static = self.flag_clean_static

        # iterate over domain list
        static_file_collection = {}
        for domain_name in domain_list:

            # info domain start
            log_stream.info(' -----> Domain "' + domain_name + '" ... ')

            file_path_src_cnet_def = self.define_file_name(
                file_path_src_cnet_raw, tags_template=self.alg_template, tags_filled={'domain_name': domain_name})
            file_path_src_watermark_def = self.define_file_name(
                file_path_src_watermark_raw, tags_template=self.alg_template, tags_filled={'domain_name': domain_name})
            file_path_dst_def = self.define_file_name(
                file_path_dst_raw, tags_template=self.alg_template, tags_filled={'domain_name': domain_name})

            if flag_clean_static:
                if os.path.exists(file_path_dst_def):
                    os.remove(file_path_dst_def)

            # Read gridded static data source
            if not os.path.exists(file_path_dst_def):

                # get static geo datasets
                obj_cnet_data = read_data_grid(
                    file_path_src_cnet_def, var_limit_min=0, var_limit_max=None, output_format='data_array')
                # get static watermark datasets
                obj_watermark_data = read_data_grid(
                    file_path_src_watermark_def, var_limit_min=0, var_limit_max=None, output_format='data_array')

                # method to get channel network index
                obj_cnet_idx = search_channel_network_idx(obj_cnet_data, cnet_value=1)

                # organize data collections
                static_data_collections = {
                    self.flag_cnet_data: obj_cnet_data, self.flag_idx_data: obj_cnet_idx,
                    self.flag_watermark_data: obj_watermark_data}

                # write data collections
                folder_name_dst, file_name_dst = os.path.split(file_path_dst_def)
                make_folder(folder_name_dst)
                write_obj(file_path_dst_def, static_data_collections)

                # organize file collection
                static_file_collection[domain_name] = file_path_dst_def

                # info domain end
                log_stream.info(' -----> Domain "' + domain_name + '" ... DONE')

            else:
                # organize file collection
                static_file_collection[domain_name] = file_path_dst_def
                # info domain end
                log_stream.info(' -----> Domain "' + domain_name + '" ... LOADED. Datasets previously created.')

        # info end
        log_stream.info(' ----> Organize static datasets ... DONE')

        return static_file_collection
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
