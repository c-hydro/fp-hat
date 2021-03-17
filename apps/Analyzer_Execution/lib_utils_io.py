# -------------------------------------------------------------------------------------
# Libraries
import logging
import tempfile
import os
import time
import json
import pickle

import numpy as np
import pandas as pd

from distutils.util import strtobool
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read discharge file
def read_file_discharge(file_name, file_template=None, file_skiprows=4):

    file_tmp = pd.read_table(file_name)
    file_data = list(file_tmp.values)

    collections_id = 0
    obj_mod = None
    obj_observed = None
    obj_header = {}
    for row_id, row_step in enumerate(file_data):
        row_tmp = row_step[0]
        if row_id < file_skiprows:
            field_key, field_data = row_tmp.rstrip().split('=')

            if field_key in list(file_template.keys()):
                field_name = file_template[field_key]['name']
                field_type = file_template[field_key]['type']
                field_value = file_template[field_key]['value']
            else:
                field_name = field_key
                field_type = None
                field_value = None

            if field_type is not None:
                if field_type == 'time_stamp':
                    field_data = pd.Timestamp(field_data)
                elif field_type == 'time_frequency':
                    field_data = pd.Timedelta(field_data)
                elif field_type == 'int':
                    field_data = np.int(field_data)

            if field_value is not None:
                field_data = field_value

            obj_header[field_name] = field_data
        elif row_id == file_skiprows:
            columns_values = row_tmp.rstrip().split(' ')
            array_observed = np.array(columns_values, dtype=np.float)
            array_observed[array_observed < 0.0] = np.nan
            time_n = array_observed.shape[0]

            if obj_observed is None:
                obj_observed = np.zeros(shape=(time_n, 1))
                obj_observed[:, :] = np.nan
            obj_observed[:, 0] = array_observed

        elif row_id >= file_skiprows:

            columns_values = row_tmp.rstrip().split(' ')
            array_values = np.array(columns_values, dtype=np.float)
            array_values[array_values < 0.0] = np.nan
            time_n = array_values.shape[0]

            if obj_mod is None:
                obj_mod = np.zeros(shape=(time_n , obj_header['scenario_n']))
                obj_mod[:, :] = np.nan
            obj_mod[:, collections_id] = array_values

            collections_id += 1

    return obj_header, obj_mod, obj_observed
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read warning file
def read_file_warning(file_name, file_template=None, file_skiprows=4, tag_data='section_{:}'):

    file_tmp = pd.read_table(file_name)
    file_data = list(file_tmp.values)

    file_time_modified = pd.Timestamp(time.ctime(os.path.getmtime(file_name)))
    file_time_created = pd.Timestamp(time.ctime(os.path.getctime(file_name)))

    collections_id = 0
    file_header = {}
    file_collections = {}
    for row_id, row_step in enumerate(file_data):
        row_tmp = row_step[0]
        if row_id < file_skiprows:
            field_key, field_data = row_tmp.rstrip().split('=')

            if field_key in list(file_template.keys()):
                field_name = file_template[field_key]['name']
                field_type = file_template[field_key]['type']
                field_value = file_template[field_key]['value']
            else:
                field_name = field_key
                field_type = None
                field_value = None

            if field_type is not None:
                if field_type == 'time_stamp':
                    field_data = pd.Timestamp(field_data)
                elif field_type == 'time_frequency':
                    field_data = pd.Timedelta(field_data)
                elif field_type == 'int':
                    field_data = np.int(field_data)

            if field_value is not None:
                field_data = field_value

            file_header[field_name] = field_data
        elif row_id == file_skiprows:
            columns_name = row_tmp.rstrip().split(' ')
            columns_type = [str, str, float, float, bool, float, bool]
        elif row_id > file_skiprows:
            columns_values = row_tmp.rstrip().split(' ')
            file_collections[tag_data.format(collections_id)] = {}

            for column_name, column_value, column_type in zip(columns_name, columns_values, columns_type):
                file_collections[tag_data.format(collections_id)][column_name] = {}

                if column_type is float:
                    column_value = np.float(column_value)
                elif column_type is bool:
                    column_value = strtobool(column_value.lower())
                elif column_type is str:
                    column_value = column_value.strip()
                file_collections[tag_data.format(collections_id)][column_name] = column_value

            collections_id += 1

        file_header['time_file_created'] = file_time_created
        file_header['time_file_modified'] = file_time_modified

    return file_header, file_collections
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a tmp name
def create_filename_tmp(prefix='tmp_', suffix='.tiff', folder=None):

    if folder is None:
        folder = '/tmp'

    with tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, suffix=suffix, delete=False) as tmp:
        temp_file_name = tmp.name
    return temp_file_name
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data obj
def read_obj(filename):
    if os.path.exists(filename):
        data = pickle.load(open(filename, "rb"))
    else:
        data = None
    return data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write data obj
def write_obj(filename, data):
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# -------------------------------------------------------------------------------------
