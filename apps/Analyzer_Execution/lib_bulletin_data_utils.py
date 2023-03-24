"""
Library Features:

Name:          lib_data_io_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201202'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging

import numpy as np
import pandas as pd

from statistics import mean
from copy import deepcopy

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to init bulletin attrs
def init_bulletin_attrs(summary_attrs_in):
    summary_attrs_out = None
    if summary_attrs_in is not None:
        summary_attrs_out = {}
        for summary_key, summary_value in summary_attrs_in.items():
            if not isinstance(summary_value, list):
                summary_value = [summary_value]
            summary_attrs_out[summary_key] = summary_value
    return summary_attrs_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to merge bulletin attrs
def merge_bulletin_attrs(summary_attrs_new, summary_attrs_tmp):

    summary_attrs_n, summary_attrs_merged = None, {}
    if summary_attrs_new is not None:

        # organize merged attributes
        for summary_key, summary_value in summary_attrs_new.items():
            tmp_value = summary_attrs_tmp[summary_key]
            if isinstance(summary_value, list):
                tmp_value.extend(summary_value)
            else:
                log_stream.error(' ===> The bulletin attrs values format is not supported')
                raise NotImplemented('Case not implemented yet')

            if summary_attrs_n is None:
                summary_attrs_n = tmp_value.__len__()

            summary_attrs_merged[summary_key] = {}
            summary_attrs_merged[summary_key] = tmp_value

        # fill merged attributes (if needed because some fields are missing)
        for tmp_key, tmp_value in summary_attrs_tmp.items():
            if tmp_key not in list(summary_attrs_merged.keys()):
                tmp_attrs_n = tmp_value.__len__()
                diff_attrs_n = summary_attrs_n - tmp_attrs_n

                if diff_attrs_n < 0:
                    log_stream.error(' ===> Difference between element length of new and tmp summary must be positive')
                    raise RuntimeError('Check the algorithm; this is an unexpected error')

                fill_attrs_value = [None] * diff_attrs_n

                tmp_value.extend(fill_attrs_value)

                summary_attrs_merged[tmp_key] = tmp_value

    else:
        log_stream.warning(' ===> The bulletin attrs values is defined by NoneType')
        summary_attrs_merged = deepcopy(summary_attrs_tmp)

    return summary_attrs_merged

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get bool value
def get_bool_value(values, method='unique', separator=';'):
    values_filtered = [i for i in values if i is not None]
    if not values_filtered:
        values_filtered = None

    if values_filtered is not None:
        if method == 'unique':
            values_filtered = list(set(values_filtered))
            if values_filtered.__len__() == 1:
                value = np.bool(values_filtered[0])
            else:
                log_stream.error(' ===> Obj type is not expected')
                raise RuntimeError('Value must be defined by list of one element')
        else:
            log_stream.error(' ===> Get unique value method "' + method + '" is not supported')
            raise NotImplemented('Case not implemented yet')
    else:
        log_stream.error(' ===> All the values are defined by NoneType')
        value = None

    return value
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute unique list
def get_unique_value(values, method='unique', separator=';'):
    values_filtered = [i for i in values if i is not None]
    if not values_filtered:
        values_filtered = None

    if values_filtered is not None:
        if method == 'unique':
            values_filtered = list(set(values_filtered))
            if values_filtered.__len__() == 1:
                value = values_filtered[0]
            else:
                log_stream.error(' ===> Obj type is not expected')
                raise RuntimeError('Value must be defined by list of one element')
        elif method == 'concatenate':
            value = separator.join(values_filtered)
        else:
            log_stream.error(' ===> Get unique value method "' + method + '" is not supported')
            raise NotImplemented('Case not implemented yet')
    else:
        log_stream.error(' ===> All the values are defined by NoneType')
        value = None

    return value
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute unique date
def compute_unique_date(values, method='min'):

    values_filtered = [i for i in values if i is not None]
    if not values_filtered:
        values_filtered = None

    if values_filtered is not None:
        if method == 'min':
            value = min(values_filtered)
        elif method == 'max':
            value = max(values_filtered)
        elif method == 'null':
            value = deepcopy(values)
        else:
            log_stream.error(' ===> Compute unique date method "' + method + '" is not supported')
            raise NotImplemented('Case not implemented yet')
    else:
        log_stream.error(' ===> All the dates are defined by NoneType')
        value = None

    return value
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute sum value
def compute_unique_value(values, method='sum', precision=1):

    values_filtered = [i for i in values if i is not None]
    if not values_filtered:
        values_filtered = None

    if values_filtered is not None:
        if method == 'sum':
            value = sum(values_filtered)
        elif method == 'average':

            if isinstance(values_filtered[0], pd.Timedelta):
                value = pd.to_timedelta(pd.Series(values_filtered)).mean()
            else:
                value = mean(values_filtered)
        else:
            log_stream.error(' ===> Compute unique value method "' + method + '" is not supported')
            raise NotImplemented('Case not implemented yet')

        if not isinstance(value, pd.Timedelta):
            if precision is not None:
                value = round(value, precision)
    else:
        log_stream.error(' ===> All the values are defined by NoneType')
        value = None

    return value
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to shrink bulletin attrs
def shrink_bulletin_attrs(summary_attrs_all, op_element_list=None):

    if op_element_list is None:
        op_element_list = [
            'run_n:get_unique_value:unique',
            'run_expected:get_unique_value:unique',
            'section_n:compute_unique_value:sum',
            'run_type:get_unique_value:unique',
            'run_name:get_unique_value:unique',
            'run_sub_path_execution:get_unique_value:unique',
            'run_description:get_unique_value:unique',
            'time_period:get_unique_value:unique',
            'time_frequency:get_unique_value:unique',
            'time_rounding:get_unique_value:unique',
            'run_start:compute_unique_date:min',
            'run_end:compute_unique_date:max',
            'run_elapsed:compute_unique_value:average',
            'run_sub_path_datasets:get_unique_value:concatenate',
            'run_variable_sim:get_unique_value:concatenate',
            'run_variable_obs:get_unique_value:concatenate',
            'run_domain_reference:get_unique_value:unique',
            'domain_name:get_unique_value:concatenate',
            'run_domain_warnings:get_unique_value:unique',
            'view_warnings:get_bool_value:unique',
            'view_execution:get_bool_value:unique',
            'run_time_last:compute_unique_date:max',
            'run_time_period:compute_unique_date:null',
        ]

    summary_attrs_unique = {}
    for summary_key, summary_obj in summary_attrs_all.items():

        op_var, op_fx, op_method = None, None, None
        for op_element_step in op_element_list:
            op_element_key = op_element_step.split(':')[0]
            if op_element_key == summary_key:
                op_var, op_fx, op_method = op_element_step.split(':')
                break

        if op_var is not None:
            if op_fx == 'get_unique_value':
                summary_value = get_unique_value(summary_obj, method=op_method)
            elif op_fx == 'get_bool_value':
                summary_value = get_bool_value(summary_obj, method=op_method)
            elif op_fx == 'compute_unique_date':
                summary_value = compute_unique_date(summary_obj, method=op_method)
            elif op_fx == 'compute_unique_value':
                summary_value = compute_unique_value(summary_obj, method=op_method, precision=1)
            else:
                log_stream.error(' ===> Obj fx "' + op_fx + '" is not expected')
                raise NotImplemented('Case not implemented yet')
            summary_attrs_unique[summary_key] = summary_value

        else:
            log_stream.error(' ===> The variable "' + summary_key + '" is not defined in the expected list')
            raise RuntimeError('Check the variables and insert the "' + summary_key + '" is needed by the algorithm')

    return summary_attrs_unique

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to merge bulletin datasets
def merge_bulletin_datasets(summary_datasets_new, summary_datasets_tmp):
    summary_datasets_merged = {}
    if summary_datasets_new is not None:
        for summary_key, summary_data in summary_datasets_new.items():
            tmp_data = summary_datasets_tmp[summary_key]

            summary_datasets_merged[summary_key] = {}
            for summary_subkey, summary_values in summary_data.items():

                tmp_values = tmp_data[summary_subkey]
                if isinstance(tmp_values, list):
                    tmp_values.extend(summary_values)
                else:
                    log_stream.error(' ===> The bulletin datasets values format is not supported')
                    raise NotImplemented('Case not implemented yet')

                summary_datasets_merged[summary_key][summary_subkey] = {}
                summary_datasets_merged[summary_key][summary_subkey] = tmp_values
    else:
        log_stream.warning(' ===> The bulletin datasets values is defined by NoneType')
        summary_datasets_merged = deepcopy(summary_datasets_tmp)

    return summary_datasets_merged
# -------------------------------------------------------------------------------------


