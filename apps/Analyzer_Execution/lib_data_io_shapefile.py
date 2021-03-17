"""
Class Features

Name:          lib_data_io_shapefile
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""

#######################################################################################
# Libraries
import logging

import pandas as pd
import geopandas as gpd

logging.getLogger('fiona').setLevel(logging.WARNING)
logging.getLogger('geopandas').setLevel(logging.WARNING)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


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
        raise IOError('Section selection failed; section not found')
    else:
        raise NotImplementedError('Section selection failed for unknown reason.')

    return point_dict
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read shapefile section(s)
def read_file_section_data(file_name, columns_name_expected_in=None, columns_name_expected_out=None, columns_name_type=None):

    if columns_name_expected_in is None:
        columns_name_expected_in = [
            'HMC_X', 'HMC_Y', 'LAT', 'LON', 'BASIN', 'SEC_NAME', 'SEC_RS', 'AREA', 'Q_THR1', 'Q_THR2']

    if columns_name_expected_out is None:
        columns_name_expected_out = [
            'hmc_idx_x', 'hmc_idx_y', 'latitude', 'longitude', 'section_domain', 'section_name', 'section_code',
            'section_drained_area', 'section_discharge_thr_alert', 'section_discharge_thr_alarm']

    if columns_name_type is None:
        columns_name_type = ['int', 'int', 'float', 'float',
                             'str', 'str', 'str', 'float', 'float', 'float']

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
                raise NotImplementedError('Datatype not implemented yet')

        section_obj[column_name_out] = column_data

    section_df = pd.DataFrame(data=section_obj)

    return section_df
# -------------------------------------------------------------------------------------
