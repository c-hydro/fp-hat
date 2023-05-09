"""
Class Features

Name:          driver_data_io_dynamic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210429'
Version:       '1.0.0'
"""

######################################################################################
# Library
import logging
import os
from copy import deepcopy

import rasterio
import numpy as np
import pandas as pd

from lib_data_io_tiff import write_file_tiff
from lib_data_io_nc import read_file_nc
from lib_data_io_binary import read_file_binary
from lib_data_io_pickle import read_obj, write_obj
from lib_data_io_gzip import unzip_filename

from lib_data_analysis import compute_q2t

from lib_utils_zip import remove_zip_extension
from lib_utils_system import fill_tags2string, make_folder, join_path

from lib_info_args import zip_extension, logger_name, time_format_datasets, time_format_algorithm

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
######################################################################################


# -------------------------------------------------------------------------------------
# Class DriverDynamic
class DriverDynamic:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, time_reference, src_dict, anc_dict=None, dst_dict=None, tmp_dict=None,
                 alg_static=None, alg_info=None, alg_template=None,
                 flag_geo='geo', flag_stats='statistics',
                 flag_src='Q',
                 flag_anc_q='Q', flag_anc_t='T',
                 flag_dst_q_ref='TQ', flag_dst_q_max='TQ_MAX',
                 flag_cleaning_dynamic_src=True, flag_cleaning_dynamic_anl=True, flag_cleaning_dynamic_dst=True):

        self.time_reference = time_reference

        self.flag_geo = flag_geo
        self.flag_stats = flag_stats
        self.flag_src = flag_src
        self.flag_anc_q = flag_anc_q
        self.flag_anc_t = flag_anc_t
        self.flag_dst_q_ref = flag_dst_q_ref
        self.flag_dst_q_max = flag_dst_q_max

        self.alg_static = alg_static
        self.alg_info = alg_info
        self.alg_template = alg_template

        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'
        self.dset_variable_tag = 'variable'
        self.dset_type_tag = 'type'
        self.dset_compression_tag = 'compression'
        self.dset_ratio_factor_tag = 'ratio_factor'
        self.dset_sub_path_ref_tag = 'sub_path_ref'

        self.obj_domain_name = self.alg_info['domains']
        self.obj_run_name = self.alg_info['run']
        self.obj_dim_km = self.alg_info['dim_km']
        self.obj_time_window_left = self.alg_info['time_window_left']
        self.obj_time_window_right = self.alg_info['time_window_right']

        folder_name_src = src_dict[self.folder_name_tag]
        file_name_src = src_dict[self.file_name_tag]
        self.file_path_src = join_path(folder_name_src, file_name_src)
        self.dset_variable_src = src_dict[self.dset_variable_tag]
        self.dset_type_src = src_dict[self.dset_type_tag]
        self.dset_compression_src = src_dict[self.dset_compression_tag]
        self.dset_ratio_factor_src = src_dict[self.dset_ratio_factor_tag]
        self.dset_sub_path_ref_src = src_dict[self.dset_sub_path_ref_tag]

        folder_name_anc_q = anc_dict[self.flag_anc_q][self.folder_name_tag]
        file_name_anc_q = anc_dict[self.flag_anc_q][self.file_name_tag]
        self.file_path_anc_q = join_path(folder_name_anc_q, file_name_anc_q)
        folder_name_anc_t = anc_dict[self.flag_anc_t][self.folder_name_tag]
        file_name_anc_t = anc_dict[self.flag_anc_t][self.file_name_tag]
        self.file_path_anc_t = join_path(folder_name_anc_t, file_name_anc_t)

        folder_name_dst_q_ref = dst_dict[self.flag_dst_q_ref][self.folder_name_tag]
        file_name_dst_q_ref = dst_dict[self.flag_dst_q_ref][self.file_name_tag]
        self.file_path_dst_q_ref = join_path(folder_name_dst_q_ref, file_name_dst_q_ref)
        self.dset_variable_dst_q_ref = dst_dict[self.flag_dst_q_ref][self.dset_variable_tag]
        self.dset_type_dst_q_ref = dst_dict[self.flag_dst_q_ref][self.dset_type_tag]
        self.dset_compression_dst_q_ref = dst_dict[self.flag_dst_q_ref][self.dset_compression_tag]
        self.dset_ratio_factor_dst_q_ref = dst_dict[self.flag_dst_q_ref][self.dset_ratio_factor_tag]
        self.dset_sub_path_dst_q_ref = dst_dict[self.flag_dst_q_ref][self.dset_sub_path_ref_tag]

        folder_name_dst_q_max = dst_dict[self.flag_dst_q_max][self.folder_name_tag]
        file_name_dst_q_max = dst_dict[self.flag_dst_q_max][self.file_name_tag]
        self.file_path_dst_q_max = join_path(folder_name_dst_q_max, file_name_dst_q_max)
        self.dset_variable_dst_q_max = dst_dict[self.flag_dst_q_max][self.dset_variable_tag]
        self.dset_type_dst_q_max = dst_dict[self.flag_dst_q_max][self.dset_type_tag]
        self.dset_compression_dst_q_max = dst_dict[self.flag_dst_q_max][self.dset_compression_tag]
        self.dset_ratio_factor_dst_q_max = dst_dict[self.flag_dst_q_max][self.dset_ratio_factor_tag]
        self.dset_sub_path_dst_q_max = dst_dict[self.flag_dst_q_max][self.dset_sub_path_ref_tag]

        self.folder_name_tmp = tmp_dict[self.folder_name_tag]
        self.file_name_tmp = tmp_dict[self.file_name_tag]
        self.clean_tmp = True

        self.time_window, self.time_reference, self.idx_reference = self.define_time_window(
            self.time_reference,
            time_window_left=self.obj_time_window_left, time_window_right=self.obj_time_window_right)

        self.flag_cleaning_dynamic_src = flag_cleaning_dynamic_src
        self.flag_cleaning_dynamic_anl = flag_cleaning_dynamic_anl
        self.flag_cleaning_dynamic_dst = flag_cleaning_dynamic_dst

        self.flag_debug = 0

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to define dynamic time window
    @staticmethod
    def define_time_window(time_reference,
                           time_window_left=0, time_window_right=0, time_window_frequency='H'):

        time_reference_left = deepcopy(time_reference)
        if time_window_frequency == 'H':
            time_reference_right = time_reference + pd.Timedelta(hours=1, minutes=0, seconds=0)
        else:
            log_stream.error(' ===> The frequency "' + time_window_frequency + '" is not supported')
            raise NotImplemented('Case not implemented yet')

        if time_window_left > 0:
            period_window_left = pd.date_range(end=time_reference_left,
                                               periods=time_window_left, freq=time_window_frequency)
        else:
            period_window_left = pd.DatetimeIndex([time_reference])
        if time_window_right == 1:
            period_window_right = pd.DatetimeIndex([time_reference_right])
        elif time_window_right > 1:
            period_window_right = pd.date_range(start=time_reference_right,
                                                periods=time_window_right, freq=time_window_frequency)
        else:
            period_window_right = pd.DatetimeIndex([time_reference])

        time_window = period_window_left.union(period_window_right)

        idx_reference = time_window.get_loc(time_reference)

        return time_window, time_reference, idx_reference

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to define dynamic filename
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
    # method to get obj dynamic static
    @staticmethod
    def get_obj_dynamic(file_name):

        if os.path.exists(file_name):
            file_collections = read_obj(file_name)
        else:
            log_stream.error(' ===> File  "' + file_name + '" is not found. ')
            raise RuntimeError('Static information must be defined for running the algorithm')

        return file_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to get obj static
    @staticmethod
    def get_obj_static(file_name, file_var_geo='geo', file_var_statistics='statistics'):

        if os.path.exists(file_name):
            file_obj = read_obj(file_name)

            file_data_geo = file_obj[file_var_geo]
            file_data_stats = file_obj[file_var_statistics]

            file_collections = {**file_data_geo, **file_data_stats}

        else:
            log_stream.error(' ===> File  "' + file_name + '" is not found. ')
            raise RuntimeError('Static information must be defined for running the algorithm')

        return file_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to get data dynamic
    def get_data_dynamic(self, file_path_def, dim_x=None, dim_y=None,
                         folder_name_tmp=None, clean_tmp=True):

        if os.path.exists(file_path_def):

            if self.dset_compression_src:

                if folder_name_tmp is None:
                    folder_name_tmp = '/tmp'
                if not os.path.exists(folder_name_tmp):
                    make_folder(folder_name_tmp)

                if file_path_def.endswith(zip_extension):
                    file_path_noext = remove_zip_extension(file_path_def)
                    folder_name_noext, file_name_noext = os.path.split(file_path_noext)
                    file_path_tmp = os.path.join(folder_name_tmp, file_name_noext)

                    unzip_filename(file_path_def, file_path_tmp)

                else:
                    log_stream.error(' ===> File compression "' + zip_extension + '" is not supported')
                    raise NotImplemented('Case not implemented yet')

            else:
                file_path_tmp = deepcopy(file_path_def)

            if self.dset_type_src == 'netcdf':
                file_data = read_file_nc(
                    file_path_tmp,
                    var_name=self.dset_variable_src, var_ratio_factor=self.dset_ratio_factor_src)
            elif self.dset_type_src == 'binary':
                file_data = read_file_binary(
                    file_path_tmp,
                    file_dim_x=dim_x, file_dim_y=dim_y, file_ratio_factor=self.dset_ratio_factor_src)
            else:
                log_stream.error(' ===> File type "' + self.dset_type_src + '" is not supported')
                raise NotImplemented('Case not implemented yet')

            if file_path_tmp is not None:
                if file_path_tmp != file_path_def:
                    if clean_tmp:
                        if os.path.exists(file_path_tmp):
                            os.remove(file_path_tmp)

        else:
            log_stream.warning(' ===> File  "' + file_path_def + '" is not found. ')
            file_data = None

        return file_data

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to save dynamic data
    @staticmethod
    def save_data_dynamic(file_name, file_data, file_variable, file_geo_x, file_geo_y, file_scale_factor=1,
                          file_epsg_code='EPSG:4326', file_type='tiff', file_compression=False):

        if file_compression:
            log_stream.error(' ===> File compression is not supported')
            raise NotImplemented('Case not implemented yet')
        if file_scale_factor != 1:
            log_stream.error(' ===> File scale factor must be equal to 1. Other cases are not supported')
            raise NotImplemented('Case not implemented yet')

        # check file format (tiff or tif)
        if file_type == 'tiff' or file_type == 'tif':
            file_data_height, file_data_width = file_data.shape
            file_geo_x_west = np.min(np.min(file_geo_x))
            file_geo_x_east = np.max(np.max(file_geo_x))
            file_geo_y_south = np.min(np.min(file_geo_y))
            file_geo_y_north = np.max(np.max(file_geo_y))

            file_data[file_data < -90] = -9999
            # file_data[np.isnan(file_data)] = -9999

            file_data_transform = rasterio.transform.from_bounds(
                file_geo_x_west, file_geo_y_south, file_geo_x_east, file_geo_y_north,
                file_data_width, file_data_height)

            folder_name, _ = os.path.split(file_name)
            make_folder(folder_name)

            write_file_tiff(file_name=file_name, file_data=file_data,
                            file_wide=file_data_width, file_high=file_data_height,
                            file_geotrans=file_data_transform, file_proj=file_epsg_code,
                            file_metadata=file_variable)
        else:
            # file format not supported
            log_stream.error(' ===> File type "' + file_type + '" is not supported. Only tiff format is allowed')
            raise NotImplemented('Case not implemented yet')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to save dynamic data
    def save_dynamic(self, anl_file_collection):

        # info start
        log_stream.info(' ----> Save dynamic datasets ... ')

        # get domain and time information
        domain_list = self.obj_domain_name
        time_reference = self.time_reference
        idx_reference = self.idx_reference
        time_window = self.time_window
        # get sub path reference
        sub_path_ref = self.dset_sub_path_ref_src

        # get file name
        file_path_anc_t_raw = self.file_path_anc_t
        file_path_dst_q_ref_raw = self.file_path_dst_q_ref
        file_path_dst_q_max_raw = self.file_path_dst_q_max
        # get static datasets
        alg_static = self.alg_static

        # get flags
        flag_cleaning_dynamic_dst = self.flag_cleaning_dynamic_dst

        # iterate over domain list
        for domain_name in domain_list:

            # info domain start
            log_stream.info(' -----> Domain "' + domain_name + '" ... ')

            # check static datasets
            if domain_name in list(alg_static.keys()):
                static_data = self.get_obj_static(alg_static[domain_name])
            else:
                log_stream.error(' ===> Statistics information for domain "' + domain_name + '" are not available')
                raise RuntimeError("Statistics information are mandatory for correctly running the algorithm")

            # choose sub path reference type
            if sub_path_ref == 'sub_path_run':
                time_sub_path = deepcopy(time_reference)
            elif sub_path_ref == 'sub_path_time':
                log_stream.error(' ===> Reference sub_path "' + sub_path_ref + '" is not available for dst dataset')
                raise NotImplemented('Case not implemented yet')
            else:
                log_stream.error(' ===> Reference sub_path "' + sub_path_ref + '" is not supported for dst dataset')
                raise NotImplemented('Case not implemented yet')

            # define destination filename(s)
            file_path_dst_q_ref_def = self.define_file_name(
                file_path_dst_q_ref_raw, tags_template=self.alg_template,
                tags_filled={'domain_name': domain_name,
                             'destination_datetime': time_reference, 'destination_sub_path_time': time_sub_path})

            file_path_dst_q_max_def = self.define_file_name(
                file_path_dst_q_max_raw, tags_template=self.alg_template,
                tags_filled={'domain_name': domain_name,
                             'destination_datetime': time_reference, 'destination_sub_path_time': time_sub_path})

            if flag_cleaning_dynamic_dst:
                if os.path.exists(file_path_dst_q_ref_def):
                    os.remove(file_path_dst_q_ref_def)
                if os.path.exists(file_path_dst_q_max_def):
                    os.remove(file_path_dst_q_max_def)

            # check file ancillary t
            if (not os.path.exists(file_path_dst_q_ref_def)) or (not os.path.exists(file_path_dst_q_max_def)):

                # iterate over time steps
                t_data_collection = np.zeros(shape=[static_data['dim_x'], static_data['dim_y'], time_window.shape[0]])
                t_data_collection[:, :, :] = np.nan
                for time_id, time_step in enumerate(time_window):

                    # info time start
                    log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... ')

                    # define analysis filename(s)
                    file_path_anc_t_def = self.define_file_name(
                        file_path_anc_t_raw, tags_template=self.alg_template,
                        tags_filled={'domain_name': domain_name,
                                     'ancillary_datetime': time_step, 'ancillary_sub_path_time': time_step})

                    # check file ancillary q
                    if os.path.exists(file_path_anc_t_def):

                        if domain_name in list(anl_file_collection.keys()):
                            if time_step in list(anl_file_collection[domain_name].keys()):
                                anl_data_collections = self.get_obj_dynamic(anl_file_collection[domain_name][time_step])
                                t_data_step = anl_data_collections[self.flag_anc_t]
                            else:
                                log_stream.warning(' ===> Dynamic information for time "' +
                                                   time_step.strftime(time_format_algorithm) + '" is not available')
                                t_data_step = None
                        else:
                            log_stream.warning(' ===> Dynamic information for domain "' +
                                               domain_name + '" is not available')
                            t_data_step = None

                        # compute q ref and q max
                        if t_data_step is not None:
                            # store data
                            t_data_collection[:, :, time_id] = t_data_step
                            # info time end
                            log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) +
                                            '" ... DONE')
                        else:
                            # info time end
                            log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) +
                                            '" ... SKIPPED. Datasets is defined by NoneType')

                    else:
                        # info time end
                        log_stream.warning(' ===> File "' + file_path_anc_t_def + '" not found.')
                        log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... FAILED')

                # save q ref information
                log_stream.info(' ------> Save "' + self.flag_dst_q_ref + '" ... ')
                t_data_reference = t_data_collection[:, :, idx_reference]
                if np.isnan(t_data_reference).all():
                    log_stream.info(' ------> Save "' + self.flag_dst_q_ref + '" ... SKIPPED. All values are NaNs')
                else:
                    self.save_data_dynamic(
                        file_name=file_path_dst_q_ref_def, file_data=t_data_reference,
                        file_geo_x=static_data['geo_x'], file_geo_y=static_data['geo_y'],
                        file_variable=self.dset_variable_dst_q_ref, file_type=self.dset_type_dst_q_ref,
                        file_scale_factor=self.dset_ratio_factor_dst_q_ref,
                        file_compression=self.dset_compression_dst_q_ref)
                    log_stream.info(' ------> Save "' + self.flag_dst_q_ref + '" ... DONE')

                # save q max information
                log_stream.info(' ------> Save "' + self.flag_dst_q_max + '" ... ')
                t_data_max = np.nanmax(t_data_collection, axis=2)
                if np.isnan(t_data_reference).all():
                    log_stream.info(' ------> Save "' + self.flag_dst_q_max + '" ... SKIPPED. All values are NaNs')
                else:
                    self.save_data_dynamic(
                        file_name=file_path_dst_q_max_def, file_data=t_data_max,
                        file_geo_x=static_data['geo_x'], file_geo_y=static_data['geo_y'],
                        file_variable=self.dset_variable_dst_q_max, file_type=self.dset_type_dst_q_max,
                        file_scale_factor=self.dset_ratio_factor_dst_q_max,
                        file_compression=self.dset_compression_dst_q_max)
                    log_stream.info(' ------> Save "' + self.flag_dst_q_max + '" ... DONE')

                # info domain end
                log_stream.info(' -----> Domain "' + domain_name + '" ... DONE')

            else:

                # info domain end
                log_stream.info(' -----> Domain "' + domain_name + '" ... SKIPPED. Datasets previously saved.')

        # info end
        log_stream.info(' ----> Save dynamic datasets ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to analyze dynamic data
    def analyze_dynamic(self, src_file_collection):

        # info start
        log_stream.info(' ----> Analyze dynamic datasets ... ')

        # get domain and time information
        domain_list = self.obj_domain_name
        time_reference = self.time_reference
        time_window = self.time_window

        # get file name
        file_path_anc_q_raw = self.file_path_anc_q
        file_path_anc_t_raw = self.file_path_anc_t
        # get static datasets
        alg_static = self.alg_static

        # get flags
        flag_cleaning_dynamic_anl = self.flag_cleaning_dynamic_anl

        # iterate over domain list
        anl_file_collection = {}
        for domain_name in domain_list:

            # info domain start
            log_stream.info(' -----> Domain "' + domain_name + '" ... ')

            # iterate over time steps
            anl_file_collection[domain_name] = {}
            for time_step in time_window:

                # info time start
                log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... ')

                file_path_anc_q_def = self.define_file_name(
                    file_path_anc_q_raw, tags_template=self.alg_template,
                    tags_filled={'domain_name': domain_name,
                                 'ancillary_datetime': time_step, 'ancillary_sub_path_time': time_step})

                file_path_anc_t_def = self.define_file_name(
                    file_path_anc_t_raw, tags_template=self.alg_template,
                    tags_filled={'domain_name': domain_name,
                                 'ancillary_datetime': time_step, 'ancillary_sub_path_time': time_step})

                if flag_cleaning_dynamic_anl:
                    if os.path.exists(file_path_anc_t_def):
                        os.remove(file_path_anc_t_def)

                # check file ancillary q
                if os.path.exists(file_path_anc_q_def):

                    # check file ancillary t
                    anl_file_collection[domain_name][time_step] = {}
                    if not os.path.exists(file_path_anc_t_def):

                        if domain_name in list(alg_static.keys()):
                            static_collections = self.get_obj_static(alg_static[domain_name])

                            q_index = static_collections['q_index']
                            statistics_params = static_collections['params']
                            geo_area = static_collections['geo_dataset']
                        else:
                            log_stream.error(' ===> Static information for domain "' + domain_name +
                                             '" are not available')
                            raise RuntimeError(
                                "Statistics information are mandatory for correctly running the algorithm")

                        if domain_name in list(src_file_collection.keys()):
                            if time_step in list(src_file_collection[domain_name].keys()):
                                src_data_collections = self.get_obj_dynamic(src_file_collection[domain_name][time_step])
                                q_data_step = src_data_collections[self.flag_anc_q]
                            else:
                                log_stream.warning(' ===> Dynamic information for time "' +
                                                   time_step.strftime(time_format_algorithm) + '" is not available')
                                q_data_step = None
                        else:
                            log_stream.warning(' ===> Dynamic information for domain "' +
                                               domain_name + '" is not available')
                            q_data_step = None

                        # compute t from q information
                        if q_data_step is not None:

                            # compute t as a function q
                            t_data_step = compute_q2t(q_data_step, q_index, statistics_params, geo_area,
                                                      debug_flag=self.flag_debug)

                            # organize data collections
                            anl_data_collections = {self.flag_anc_t: t_data_step}

                            # write data collections
                            folder_name_dst, file_name_dst = os.path.split(file_path_anc_t_def)
                            make_folder(folder_name_dst)
                            write_obj(file_path_anc_t_def, anl_data_collections)

                            # organize file collection
                            anl_file_collection[domain_name][time_step] = file_path_anc_t_def

                            # info domain end
                            log_stream.info(' -----> Domain "' + domain_name + '" ... DONE')

                            # info time start
                            log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) +
                                            '" ... DONE')

                    else:
                        # organize file collection
                        anl_file_collection[domain_name][time_step] = file_path_anc_t_def
                        # info time end
                        log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) +
                                        '" ... LOADED. Datasets previously created.')

                else:
                    # info domain end
                    log_stream.warning(' ===> File "' + file_path_anc_q_def + '" not found.')
                    log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... FAILED')

            # info domain end
            log_stream.info(' -----> Domain "' + domain_name + '" ... DONE')

        # info end
        log_stream.info(' ----> Analyze dynamic datasets ... DONE')

        return anl_file_collection

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to organize dynamic data
    def organize_dynamic(self):

        # info start
        log_stream.info(' ----> Organize dynamic datasets ... ')

        # get domain and time information
        domain_list = self.obj_domain_name
        time_reference = self.time_reference
        time_window = self.time_window
        # get sub path reference
        sub_path_ref = self.dset_sub_path_ref_src

        # get file name
        file_path_src_raw = self.file_path_src
        file_path_anc_q_raw = self.file_path_anc_q
        # get static datasets
        alg_static = self.alg_static

        # get flags
        flag_cleaning_dynamic_src = self.flag_cleaning_dynamic_src

        # iterate over domain list
        src_file_collection = {}
        for domain_name in domain_list:

            # info domain start
            log_stream.info(' -----> Domain "' + domain_name + '" ... ')

            # iterate over time steps
            src_file_collection[domain_name] = {}
            for time_step in time_window:

                # info time start
                log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... ')

                # choose sub path reference type
                if sub_path_ref == 'sub_path_run':
                    time_sub_path = deepcopy(time_reference)
                elif sub_path_ref == 'sub_path_time':
                    time_sub_path = deepcopy(time_step)
                else:
                    log_stream.error(' ===> Reference sub_path "' + sub_path_ref + '" is not supported for src dataset')
                    raise NotImplemented('Case not implemented yet')

                # define src and ancillary filename(s)
                file_path_src_def = self.define_file_name(
                    file_path_src_raw, tags_template=self.alg_template,
                    tags_filled={'domain_name': domain_name,
                                 'source_datetime': time_step, 'source_sub_path_time': time_sub_path})
                file_path_anc_q_def = self.define_file_name(
                    file_path_anc_q_raw, tags_template=self.alg_template,
                    tags_filled={'domain_name': domain_name,
                                 'ancillary_datetime': time_step, 'ancillary_sub_path_time': time_sub_path})

                # check static datasets
                if domain_name in list(alg_static.keys()):
                    static_data = self.get_obj_static(alg_static[domain_name])
                else:
                    log_stream.error(' ===> Statistics information for domain "' + domain_name + '" are not available')
                    raise RuntimeError("Statistics information are mandatory for correctly running the algorithm")

                if flag_cleaning_dynamic_src:
                    if os.path.exists(file_path_anc_q_def):
                        os.remove(file_path_anc_q_def)

                # check file source
                if os.path.exists(file_path_src_def):

                    # check file ancillary
                    src_file_collection[domain_name][time_step] = {}
                    if not os.path.exists(file_path_anc_q_def):

                        # get source datasets
                        src_data_step = self.get_data_dynamic(
                            file_path_src_def, dim_x=static_data['dim_x'], dim_y=static_data['dim_y'],
                            folder_name_tmp=self.folder_name_tmp, clean_tmp=self.clean_tmp)

                        # organize data collections
                        src_data_collections = {self.flag_anc_q: src_data_step}

                        # write data collections
                        folder_name_dst, file_name_dst = os.path.split(file_path_anc_q_def)
                        make_folder(folder_name_dst)
                        write_obj(file_path_anc_q_def, src_data_collections)

                        # organize file collection
                        src_file_collection[domain_name][time_step] = file_path_anc_q_def

                        # info time end
                        log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... DONE')

                    else:
                        # organize file collection
                        src_file_collection[domain_name][time_step] = file_path_anc_q_def

                        # info time end
                        log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) +
                                        '" ... LOADED. Datasets previously created.')

                else:
                    # info domain end
                    log_stream.warning(' ===> File "' + file_path_src_def + '" not found.')
                    log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... FAILED')

            # info domain end
            log_stream.info(' -----> Domain "' + domain_name + '" ... DONE')

        # info end
        log_stream.info(' ----> Organize dynamic datasets ... DONE')

        return src_file_collection
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
