"""
Class Features

Name:          lib_data_geo_shapefile
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""

#######################################################################################
# Libraries
import logging

import re

import numpy as np
import pandas as pd
import geopandas as gpd

from copy import deepcopy

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to find data section
def find_data_section(section_df, section_name=None, basin_name=None,
                      tag_column_section_in='section_name', tag_column_basin_in='section_domain',
                      tag_column_section_out='section_name', tag_column_basin_out='basin_name'):

    section_name_ref = section_name.lower()
    basin_name_ref = basin_name.lower()

    section_name_list = section_df[tag_column_section_in].values
    basin_name_list = section_df[tag_column_basin_in].values

    section_dict_tmp = {tag_column_section_in: section_name_list, tag_column_basin_in: basin_name_list}
    section_df_tmp = pd.DataFrame(data=section_dict_tmp)
    section_df_tmp = section_df_tmp.astype(str).apply(lambda x: x.str.lower())

    point_idx = section_df_tmp[(section_df_tmp[tag_column_section_in] == section_name_ref) &
                                 (section_df_tmp[tag_column_basin_in] == basin_name_ref)].index

    if point_idx.shape[0] == 1:
        point_idx = point_idx[0]
        point_dict = section_df.iloc[point_idx, :].to_dict()

        point_dict[tag_column_section_out] = point_dict.pop(tag_column_section_in)
        point_dict[tag_column_basin_out] = point_dict.pop(tag_column_basin_in)

    elif point_idx.shape[0] == 0:
        log_stream.error(' ===> Section idx not found in the section dictionary.')
        raise IOError('Section selection failed; section not found')
    else:
        log_stream.error(' ===> Section idx not found. Procedure will be exit for unexpected error.')
        raise NotImplementedError('Section selection failed for unknown reason.')

    return point_dict
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read shapefile section(s)
def read_data_section(file_name, file_filter=None,
                      columns_name_expected_in=None, columns_name_expected_out=None, columns_name_type=None):

    if columns_name_expected_in is None:
        columns_name_expected_in = [
            'HMC_X', 'HMC_Y', 'LAT', 'LON', 'BASIN', 'SEC_NAME', 'SEC_RS', 'AREA', 'Q_THR1', 'Q_THR2', 'TYPE']

    if columns_name_expected_out is None:
        columns_name_expected_out = [
            'hmc_idx_x', 'hmc_idx_y', 'latitude', 'longitude', 'section_domain', 'section_name', 'section_code',
            'section_drained_area', 'section_discharge_thr_alert', 'section_discharge_thr_alarm', 'section_type']

    if columns_name_type is None:
        columns_name_type = ['int', 'int', 'float', 'float',
                             'str', 'str', 'float', 'float', 'float', 'float',
                             'str']

    file_dframe_raw = gpd.read_file(file_name)
    file_rows = file_dframe_raw.shape[0]

    if file_filter is not None:
        file_dframe_step = deepcopy(file_dframe_raw)
        for filter_key, filter_value in file_filter.items():
            file_columns_check = [x.lower() for x in list(file_dframe_raw.columns)]
            if filter_key.lower() in file_columns_check:
                if isinstance(filter_value, str):
                    id_key = file_columns_check.index(filter_key)
                    filter_column = list(file_dframe_raw.columns)[id_key]

                    file_dframe_step = file_dframe_step.loc[
                        file_dframe_step[filter_column].str.lower() == filter_value.lower()]
                else:
                    log_stream.error(' ===> Filter datatype is not allowed.')
                    raise NotImplementedError('Datatype not implemented yet')

        file_dframe_raw = deepcopy(file_dframe_step)

    section_obj = {}
    for column_name_in, column_name_out, column_type in zip(columns_name_expected_in,
                                                            columns_name_expected_out, columns_name_type):
        if column_name_in in file_dframe_raw.columns:

            column_data = file_dframe_raw[column_name_in].values

            if isinstance(column_data[0], str):
                tmp_type = 'str'
                test_type = re.sub('[^a-zA-Z0-9 \n\.]', '', column_data[0])
                test_type = test_type.replace('.', '')
            elif isinstance(column_data[0], (int, np.int64)):
                tmp_type = 'int'
                test_type = int(column_data[0])
            elif isinstance(column_data[0], float):
                tmp_type = 'float'
                test_type = float(column_data[0])
            else:
                log_stream.error(' ===> Column datatype is not allowed.')
                raise NotImplementedError('Datatype not implemented yet')

            if tmp_type != column_type:
                log_stream.warning(' ===> Column "' + column_name_in + '" datatype "' + tmp_type +
                                   '" is not consistent with expected datatype. Keep datatype "' + column_type+ '"')

            if column_type == 'int':
                # check if columns expected are string of integer number
                if not isinstance(test_type, (int, float)):
                    if column_data[0].isdigit():
                        column_data = np.array(column_data, dtype=int).tolist()
                    else:
                        log_stream.warning(' ===> Column datatype is not allowed. Type expected: ' + str(column_type))
                        column_data = np.array(column_data, dtype=str).tolist()
            elif column_type == 'str':

                column_data = np.array(column_data, dtype=str).tolist()

            elif column_type == 'float':

                # check if columns expected are string of integer number
                if not isinstance(test_type, (int, float)):
                    if column_data[0].isdigit():
                        column_data = np.array(column_data, dtype=float).tolist()
                    else:
                        log_stream.warning(' ===> Column datatype is not allowed. Type expected: ' + str(column_type))
                        column_data = np.array(column_data, dtype=str).tolist()
            else:
                log_stream.error(' ===> Column datatype is not allowed.')
                raise NotImplementedError('Datatype not implemented yet')

        else:
            if column_type == 'int':
                column_data = [-9999] * file_rows
            elif column_type == 'str':
                column_data = [''] * file_rows
            elif column_type == 'float':
                column_data = [-9999.0] * file_rows
            else:
                log_stream.error(' ===> Column datatype is not allowed.')
                raise NotImplementedError('Datatype not implemented yet')

        section_obj[column_name_out] = column_data

    section_df = pd.DataFrame(data=section_obj)

    if file_filter is not None:
        section_df.attrs = file_filter

    if section_df.empty:
        list_filter = list(file_filter.keys())
        log_stream.error(' ===> Section Dataframe is empty. Check the filtering settings in "' + str(list_filter) + '"')
        raise IOError('Section dataframe must be not empty')

    return section_df
# -------------------------------------------------------------------------------------
