"""
Class Features

Name:          lib_data_io_shapefile
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import os.path

import pandas as pd
import geopandas as gpd

from copy import deepcopy

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

logging.getLogger('fiona').setLevel(logging.WARNING)
logging.getLogger('geopandas').setLevel(logging.WARNING)

# Debug
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to find data section
def find_file_section_data(section_df, section_name=None, basin_name=None,
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
        log_stream.error(' ===> Section are not available')
        raise IOError('Algorithm needs defined section to properly work')
    else:
        log_stream.error(' ===> Section are not correctly read for unknown reason')
        raise NotImplemented('Case not implemented yet')

    return point_dict
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to filter file section data based on column tag and values
def filter_file_section_data(dframe_in, field_value_list=None, field_tag='domain_name'):

    if field_value_list is not None:
        if not isinstance(field_value_list, list):
            field_value_list = [field_value_list]
        dframe_out = None
        for field_value_step in field_value_list:
            dframe_tmp = dframe_in.loc[dframe_in[field_tag].str.lower() == field_value_step.lower()]
            if dframe_out is None:
                dframe_out = deepcopy(dframe_tmp)
            else:
                dframe_out = pd.concat([dframe_out, dframe_tmp])
    else:
        dframe_out = deepcopy(dframe_in)

    if dframe_out.empty:
        log_stream.error(' ===> Section dataframe is empty. Sections are not available')
        raise RuntimeError('Sections must be available to properly run the algorithm')

    return dframe_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read shapefile section(s)
def read_file_section_data(file_name, columns_name_expected_in=None, columns_name_expected_out=None, columns_name_type=None):

    if columns_name_expected_in is None:
        columns_name_expected_in = [
            'HMC_X', 'HMC_Y', 'LAT', 'LON', 'BASIN', 'SEC_TAG', 'SEC_NAME', 'SEC_RS', 'AREA', 'Q_THR1', 'Q_THR2',
            'DOMAIN', 'SEC_DES', 'DOMAIN_DES']

    if columns_name_expected_out is None:
        columns_name_expected_out = [
            'hmc_idx_x', 'hmc_idx_y', 'latitude', 'longitude',
            'section_catchment', 'section_tag', 'section_name', 'section_code',
            'section_drained_area', 'section_discharge_thr_alert', 'section_discharge_thr_alarm',
            'domain_name', 'section_description', 'domain_description']

    if columns_name_type is None:
        columns_name_type = ['int', 'int', 'float', 'float',
                             'str', 'str', 'str', 'str',
                             'float', 'float', 'float',
                             'str', 'str', 'str']

    if os.path.exists(file_name):

        file_dframe_raw = gpd.read_file(file_name)
        file_rows = file_dframe_raw.shape[0]

        section_obj = {}
        for column_name_in, column_name_out, column_type in zip(columns_name_expected_in,
                                                                columns_name_expected_out, columns_name_type):
            if column_name_in in file_dframe_raw.columns:
                column_data = file_dframe_raw[column_name_in].values.tolist()
            else:
                if column_type == 'int':
                    column_data = [-9999] * file_rows
                elif column_type == 'str':
                    column_data = [''] * file_rows
                elif column_type == 'float':
                    column_data = [-9999.0] * file_rows
                else:
                    log_stream.error(' ===> DataType format is not supported')
                    raise NotImplemented('Case not implemented yet')

            section_obj[column_name_out] = column_data

        section_df = pd.DataFrame(data=section_obj)

    else:
        log_stream.error(' ===> File "' + file_name + '" does not exist')
        raise FileNotFoundError('Algorithm needs the file to properly work')

    if 'section_description' in list(section_df.columns):
        section_df['section_description'] = section_df['section_description'].str.replace('', 'NA')
    if 'domain_description' in list(section_df.columns):
        section_df['domain_description'] = section_df['domain_description'].str.replace('', 'NA')

    return section_df
# -------------------------------------------------------------------------------------
