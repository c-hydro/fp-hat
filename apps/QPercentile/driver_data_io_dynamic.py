"""
Class Features

Name:          driver_data_io_dynamic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20241104'
Version:       '1.1.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import os
from copy import deepcopy

import rasterio
import numpy as np
import xarray as xr

from lib_data_io_tiff import write_file_tiff
from lib_data_io_nc import read_file_nc
from lib_data_io_binary import read_file_binary
from lib_data_io_pickle import read_obj, write_obj
from lib_data_io_gzip import unzip_filename

from lib_data_analysis import compute_quantile

from lib_utils_io import define_ensemble_list, create_darray
from lib_utils_zip import remove_zip_extension, add_zip_extension
from lib_utils_system import fill_tags2string, make_folder, join_path

from lib_info_args import zip_extension, logger_name, time_format_datasets, time_format_algorithm

# logging
log_stream = logging.getLogger(logger_name)

# debugging
import matplotlib.pylab as plt
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class DriverDynamic
class DriverDynamic:

    # ------------------------------------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, time_reference, time_range,
                 src_dict, anc_dict=None, dst_dict=None, tmp_dict=None,
                 alg_static=None, alg_info=None, alg_template=None,
                 flag_cnet_data='channel_network', flag_idx_data='idx',
                 flag_src='Q', flag_anc='Q', flag_dst='Q',
                 flag_clean_dynamic_src=True, flag_clean_dynamic_dst=True):

        # time info
        self.time_reference = time_reference
        self.time_range = time_range
        # flags info
        self.flag_cnet_data = flag_cnet_data
        self.flag_idx_data = flag_idx_data
        self.flag_src = flag_src
        self.flag_anc = flag_anc
        self.flag_dst = flag_dst

        # objects info
        self.alg_static = alg_static
        self.alg_info = alg_info
        self.alg_template = alg_template

        # tags info
        self.file_name_tag, self.folder_name_tag = 'file_name', 'folder_name'
        self.dset_variable_tag, self.dset_format_tag, self.dset_decimals_tag = 'variable', 'format', 'decimals'
        self.dset_compression_tag, self.dset_ratio_factor_tag = 'compression', 'ratio_factor'
        self.dset_sub_path_ref_tag = 'sub_path_ref'

        # parameters info
        self.obj_domain_name = self.alg_info['domains']
        self.obj_run_name = self.alg_info['run']
        self.obj_quantile = self.alg_info['quantile']
        self.obj_ensemble = self.alg_info['ensemble']
        self.ensemble_n_min, self.ensemble_n_max = self.obj_ensemble['n_min'], self.obj_ensemble['n_max']
        self.ensemble_format = self.obj_ensemble['n_format']

        # define ensemble and quantile list
        self.ensemble_list = define_ensemble_list(self.ensemble_n_min, self.ensemble_n_max, self.ensemble_format)
        if isinstance(self.obj_quantile, (int, float)):
            self.quantile_list = [self.obj_quantile]
        else:
            self.quantile_list = self.obj_quantile

        # src info
        folder_name_src = src_dict[self.folder_name_tag]
        file_name_src = src_dict[self.file_name_tag]
        self.file_path_src = join_path(folder_name_src, file_name_src)
        self.dset_variable_src = src_dict[self.dset_variable_tag]
        self.dset_format_src = src_dict[self.dset_format_tag]
        self.dset_decimals_src = src_dict[self.dset_decimals_tag]
        self.dset_compression_src = src_dict[self.dset_compression_tag]
        self.dset_ratio_factor_src = src_dict[self.dset_ratio_factor_tag]
        self.dset_sub_path_src = src_dict[self.dset_sub_path_ref_tag]

        # ancillary info
        folder_name_anc = anc_dict[self.folder_name_tag]
        file_name_anc = anc_dict[self.file_name_tag]
        self.file_path_anc = join_path(folder_name_anc, file_name_anc)

        # destination info
        folder_name_dst = dst_dict[self.folder_name_tag]
        file_name_dst = dst_dict[self.file_name_tag]
        self.file_path_dst = join_path(folder_name_dst, file_name_dst)
        self.dset_variable_dst = dst_dict[self.dset_variable_tag]
        self.dset_format_dst = dst_dict[self.dset_format_tag]
        self.dset_decimals_dst = dst_dict[self.dset_decimals_tag]
        self.dset_compression_dst = dst_dict[self.dset_compression_tag]
        self.dset_ratio_factor_dst = dst_dict[self.dset_ratio_factor_tag]
        self.dset_sub_path_dst = dst_dict[self.dset_sub_path_ref_tag]

        # tmp info
        self.folder_name_tmp = tmp_dict[self.folder_name_tag]
        self.file_name_tmp = tmp_dict[self.file_name_tag]
        self.clean_tmp = True

        # flags info
        self.flag_clean_dynamic_src = flag_clean_dynamic_src
        self.flag_clean_dynamic_dst = flag_clean_dynamic_dst

        self.flag_debug = 0

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to define dynamic filename
    @staticmethod
    def define_file_name(file_name_raw, tags_template=None, tags_filled=None):
        if tags_filled is None or tags_filled is None:
            log_stream.warning(' ===> The variable(s) "tags_template" or "tags_filled" is/are defined by NoneType')
            file_name_filled = deepcopy(file_name_raw)
        else:
            file_name_filled = fill_tags2string(file_name_raw, tags_template, tags_filled)
        return file_name_filled

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to get obj dynamic static
    @staticmethod
    def get_obj_dynamic(file_name):
        if os.path.exists(file_name):
            file_collections = read_obj(file_name)
        else:
            log_stream.error(' ===> File  "' + file_name + '" is not found. ')
            raise RuntimeError('Static information must be defined for running the algorithm')

        return file_collections

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to get obj static
    @staticmethod
    def get_obj_static(file_name, file_var_data='channel_network'):
        if os.path.exists(file_name):
            file_obj = read_obj(file_name)
            file_data = file_obj[file_var_data]
        else:
            log_stream.error(' ===> File  "' + file_name + '" is not found. ')
            raise RuntimeError('Static information must be defined for running the algorithm')

        return file_data

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
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

            if self.dset_format_src == 'netcdf':
                file_data = read_file_nc(
                    file_path_tmp,
                    var_name=self.dset_variable_src, var_ratio_factor=self.dset_ratio_factor_src)
            elif self.dset_format_src == 'binary':
                file_data = read_file_binary(
                    file_path_tmp,
                    file_dim_x=dim_x, file_dim_y=dim_y, file_ratio_factor=self.dset_ratio_factor_src)
            else:
                log_stream.error(' ===> File type "' + self.dset_format_src + '" is not supported')
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

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to save dynamic data
    @staticmethod
    def save_data_dynamic(file_name, file_data, file_variable, file_geo_x, file_geo_y, file_scale_factor=1,
                          file_epsg_code='EPSG:4326', file_type='tiff', file_compression=False):

        # check flags
        if file_compression:
            log_stream.error(' ===> File compression is not supported')
            raise NotImplemented('Case not implemented yet')
        if file_scale_factor != 1:
            log_stream.error(' ===> File scale factor must be equal to 1. Other cases are not supported')
            raise NotImplemented('Case not implemented yet')

        # organize data and variable(s)
        list_data, list_variable = [], []
        for var_name, var_data in file_data.items():

            var_data[var_data < 0] = np.nan
            list_data.append(var_data)

            tmp_name = file_variable.format(var_name)
            list_variable.append(tmp_name)

        # check file format (tiff or tif)
        if file_type == 'tiff' or file_type == 'tif':
            file_data_height, file_data_width = file_geo_y.shape[0], file_geo_x.shape[0]
            file_geo_x_west = np.min(np.min(file_geo_x))
            file_geo_x_east = np.max(np.max(file_geo_x))
            file_geo_y_south = np.min(np.min(file_geo_y))
            file_geo_y_north = np.max(np.max(file_geo_y))

            file_data_transform = rasterio.transform.from_bounds(
                file_geo_x_west, file_geo_y_south, file_geo_x_east, file_geo_y_north,
                file_data_width, file_data_height)

            folder_name, _ = os.path.split(file_name)
            make_folder(folder_name)

            write_file_tiff(file_name=file_name, file_data=list_data,
                            file_wide=file_data_width, file_high=file_data_height,
                            file_geotrans=file_data_transform, file_proj=file_epsg_code,
                            file_metadata=list_variable, file_description=list_variable)
        else:
            # file format not supported
            log_stream.error(' ===> File type "' + file_type + '" is not supported. Only tiff format is allowed')
            raise NotImplemented('Case not implemented yet')

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to dump dynamic data
    def dump_dynamic(self, file_collection):

        # info start
        log_stream.info(' ----> Dump dynamic datasets ['
                        + self.time_reference.strftime(time_format_algorithm) + '] ... ')

        # get time info
        time_reference = self.time_reference
        time_range = self.time_range
        # get domain
        domain_list = self.obj_domain_name
        # get quantile and ensemble list
        quantile_list = self.quantile_list
        ensemble_list = self.ensemble_list

        # get sub path reference
        sub_path_ref = self.dset_sub_path_dst

        # get file name
        file_path_anc_raw = self.file_path_anc
        file_path_dst_raw = self.file_path_dst
        # get static datasets
        alg_static = self.alg_static

        # get flags
        flag_clean_dynamic_dst = self.flag_clean_dynamic_dst

        # iterate over domain list
        for domain_name in domain_list:

            # info domain start
            log_stream.info(' -----> Domain "' + domain_name + '" ... ')

            # iterate over time steps
            for time_step in time_range:

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

                # define ancillary filename(s)
                file_path_anc_def = self.define_file_name(
                    file_path_anc_raw, tags_template=self.alg_template,
                    tags_filled={'domain_name': domain_name,
                                 'ancillary_datetime': time_step, 'ancillary_sub_path_time': time_sub_path})
                # define destination filename(s)
                file_path_dst_def = self.define_file_name(
                    file_path_dst_raw, tags_template=self.alg_template,
                    tags_filled={'domain_name': domain_name,
                                 'destination_datetime': time_step, 'destination_sub_path_time': time_sub_path})

                # remove destination file if required
                if flag_clean_dynamic_dst:
                    if os.path.exists(file_path_dst_def):
                        os.remove(file_path_dst_def)

                # check file ancillary availability
                if not os.path.exists(file_path_dst_def):

                    # info get data start
                    log_stream.info(' -------> Get data ... ')

                    # check static datasets
                    if domain_name in list(alg_static.keys()):
                        geo_da = self.get_obj_static(alg_static[domain_name], file_var_data=self.flag_cnet_data)
                        geo_data = geo_da.values
                        geo_x, geo_y = geo_da['longitude'].values, geo_da['latitude'].values
                        geo_idx = self.get_obj_static(alg_static[domain_name], file_var_data=self.flag_idx_data)
                    else:
                        log_stream.error(
                            ' ===> Statistics information for domain "' + domain_name + '" are not available')
                        raise RuntimeError("Statistics information are mandatory for correctly running the algorithm")

                    # check domain availability
                    if domain_name in list(file_collection.keys()):
                        # check time step availability
                        if time_step in list(file_collection[domain_name].keys()):
                            # get data
                            quantile_dframe = self.get_obj_dynamic(file_collection[domain_name][time_step])
                            # info get data end
                            log_stream.info(' -------> Get data ... DONE')

                        else:
                            # info get data end
                            log_stream.warning(' ===> Time step "' + time_step.strftime(time_format_algorithm) +
                                               '" is not available in the file collections')
                            log_stream.info(' -------> Get data ... SKIPPED.')
                            quantile_dframe = None
                    else:
                        log_stream.warning(' ===> Domain "' + domain_name +
                                           '" is not available in the file collections')
                        log_stream.info(' -------> Get data ... SKIPPED.')
                        quantile_dframe = None

                    # info transform data start
                    log_stream.info(' -------> Transform data ... ')
                    quantile_collections = None
                    if quantile_dframe is not None:

                        # iterate over datasets
                        for quantile_name, quantile_obj in quantile_dframe.items():

                            quantile_array = np.zeros_like(geo_data.flatten())
                            quantile_array[:] = np.nan

                            if quantile_name in quantile_list:

                                quantile_index = quantile_obj.index
                                quantile_values = quantile_obj.values
                                quantile_array[quantile_index] = quantile_values
                                quantile_data = np.reshape(quantile_array, [geo_data.shape[0], geo_data.shape[1]])

                                if not isinstance(quantile_name, str):
                                    quantile_name = str(quantile_name)

                                # quantile_da = create_darray(quantile_data, geo_x, geo_y, name=quantile_name)

                                if quantile_collections is None:
                                    quantile_collections = {}
                                quantile_collections[quantile_name] = quantile_data

                        # info transform data end
                        log_stream.info(' -------> Transform data ... DONE')

                    else:
                        # info transform data end
                        log_stream.info(' -------> Transform data ... SKIPPED. Datasets are not available.')

                    # info save data start
                    log_stream.info(' -------> Save data ... ')
                    if quantile_collections is not None:

                        # save data
                        self.save_data_dynamic(
                            file_name=file_path_dst_def, file_data=quantile_collections,
                            file_geo_x=geo_x, file_geo_y=geo_y,
                            file_variable=self.dset_variable_dst, file_type=self.dset_format_dst,
                            file_scale_factor=self.dset_ratio_factor_dst,
                            file_compression=self.dset_compression_dst)

                        # info save data end
                        log_stream.info(' -------> Save data ... DONE')
                    else:
                        # info save data end
                        log_stream.info(' -------> Save data ... SKIPPED. Datasets are not available.')

                    # info time end
                    log_stream.info(
                        ' ------> Time "' + time_step.strftime(time_format_algorithm) +
                        '" ... DONE.')

                else:

                    # info time end
                    log_stream.info(
                        ' ------> Time "' + time_step.strftime(time_format_algorithm) +
                        '" ... SKIPPED. Datasets are not available.')

            # info domain start
            log_stream.info(' -----> Domain "' + domain_name + '" ... DONE')

        # info end
        log_stream.info(' ----> Dump dynamic datasets ['
                        + self.time_reference.strftime(time_format_algorithm) + '] ... DONE')
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to organize dynamic data
    def organize_dynamic(self):

        # info start
        log_stream.info(' ----> Organize dynamic datasets ['
                        + self.time_reference.strftime(time_format_algorithm) + '] ... ')

        # get time info
        time_reference = self.time_reference
        time_range = self.time_range
        # get domain
        domain_list = self.obj_domain_name
        # get quantile and ensemble list
        quantile_list = self.quantile_list
        ensemble_list = self.ensemble_list

        # get sub path reference
        sub_path_ref = self.dset_sub_path_src

        # get file name
        file_path_src_raw = self.file_path_src
        file_path_anc_raw = self.file_path_anc
        file_path_dst_raw = self.file_path_dst
        # get static datasets
        alg_static = self.alg_static

        # get flags
        flag_clean_dynamic_src = self.flag_clean_dynamic_src

        # iterate over domain list
        file_collection = {}
        for domain_name in domain_list:

            # info domain start
            log_stream.info(' -----> Domain "' + domain_name + '" ... ')

            # iterate over time steps
            file_collection[domain_name] = {}
            for time_step in time_range:

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

                # define ancillary filename(s)
                file_path_anc_def = self.define_file_name(
                    file_path_anc_raw, tags_template=self.alg_template,
                    tags_filled={'domain_name': domain_name,
                                 'ancillary_datetime': time_step, 'ancillary_sub_path_time': time_sub_path})
                # define destination filename(s)
                file_path_dst_def = self.define_file_name(
                    file_path_dst_raw, tags_template=self.alg_template,
                    tags_filled={'domain_name': domain_name,
                                 'ancillary_datetime': time_step, 'ancillary_sub_path_time': time_sub_path})

                if flag_clean_dynamic_src:
                    if os.path.exists(file_path_anc_def):
                        os.remove(file_path_anc_def)
                    if os.path.exists(file_path_dst_def):
                        os.remove(file_path_dst_def)

                # check file ancillary availability
                if not os.path.exists(file_path_anc_def):

                    # check static datasets
                    if domain_name in list(alg_static.keys()):
                        geo_da = self.get_obj_static(alg_static[domain_name], file_var_data=self.flag_cnet_data)
                        geo_data = geo_da.values
                        geo_x, geo_y = geo_da['longitude'].values, geo_da['latitude'].values
                        geo_idx = self.get_obj_static(alg_static[domain_name], file_var_data=self.flag_idx_data)
                    else:
                        log_stream.error(
                            ' ===> Statistics information for domain "' + domain_name + '" are not available')
                        raise RuntimeError("Statistics information are mandatory for correctly running the algorithm")

                    # iterate over ensemble list
                    ensemble_data = np.zeros(shape=[geo_idx.shape[0], len(ensemble_list)])
                    ensemble_data[:, :] = np.nan
                    for ensemble_id, ensemble_name in enumerate(ensemble_list):

                        # info ensemble start
                        log_stream.info(' -------> Ensemble "' + ensemble_name + '" ... ')

                        # define src filename(s)
                        file_path_src_def = self.define_file_name(
                            file_path_src_raw, tags_template=self.alg_template,
                            tags_filled={'domain_name': domain_name, 'ensemble_name': ensemble_name,
                                         'source_datetime': time_step, 'source_sub_path_time': time_sub_path})

                        # check file source
                        if os.path.exists(file_path_src_def):

                            # get source datasets
                            src_data_2d = self.get_data_dynamic(
                                file_path_src_def, dim_x=geo_data.shape[0], dim_y=geo_data.shape[1],
                                folder_name_tmp=self.folder_name_tmp, clean_tmp=self.clean_tmp)

                            # organize source datasets
                            src_data_1d = src_data_2d.flatten()
                            src_data_select = src_data_1d[geo_idx]
                            src_data_select = np.round(src_data_select, decimals=1)

                        else:
                            # info domain end
                            log_stream.warning(' ===> File "' + file_path_src_def + '" not found.')
                            # no data available
                            src_data_select = np.zeros(shape=[geo_idx.shape[0]])
                            src_data_select[:] = np.nan

                        # store data in the ensemble collection
                        ensemble_data[:, ensemble_id] = src_data_select

                        # info ensemble end
                        log_stream.info(' -------> Ensemble "' + ensemble_name + '" ... DONE')

                    # compute quantile(s)
                    ensemble_quantiles = compute_quantile(
                        ensemble_data, ensemble_list=ensemble_list, geo_idx=geo_idx, quantile_list=quantile_list)

                    # filter nan values (all values are nans)
                    ensemble_quantiles = ensemble_quantiles.dropna(how='all')

                    # check quantile availability
                    if not ensemble_quantiles.empty:

                        # write data collections
                        folder_name_anc, file_name_anc = os.path.split(file_path_anc_def)
                        make_folder(folder_name_anc)
                        write_obj(file_path_anc_def, ensemble_quantiles)

                        # organize file collection
                        file_collection[domain_name][time_step] = {}
                        file_collection[domain_name][time_step] = file_path_anc_def

                        # info time end
                        log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) +
                                        '" ... DONE')

                    else:
                        # info time end
                        log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) +
                                        '" ... SKIPPED. '
                                        'Datasets are defined by nan values for all ensembles and quantiles.')

                else:
                    # organize file collection
                    file_collection[domain_name][time_step] = file_path_anc_def

                    # info time end
                    log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) +
                                    '" ... LOADED. Datasets previously created.')

            # info domain end
            log_stream.info(' -----> Domain "' + domain_name + '" ... DONE')

        # info end
        log_stream.info(' ----> Organize dynamic datasets ['
                        + self.time_reference.strftime(time_format_algorithm) + '] ... DONE')

        return file_collection
    # ------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
