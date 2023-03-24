"""
Library Features:

Name:          lib_utils_exec
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import os
import time
import pandas as pd

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read file execution information
def read_file_execution_info(file_name,
                             tag_time_access='time_access', tag_time_modified='time_modified',
                             tag_time_create='time_create', tag_file_size='file_size'):

    file_time_access = pd.Timestamp(time.ctime(os.path.getatime(file_name)))
    file_time_modified = pd.Timestamp(time.ctime(os.path.getmtime(file_name)))
    file_time_create = pd.Timestamp(time.ctime(os.path.getctime(file_name)))
    file_size = os.path.getsize(file_name)

    file_obj = {tag_time_access: file_time_access, tag_time_modified: file_time_modified,
                tag_time_create: file_time_create, tag_file_size: file_size}

    return file_obj
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read file execution data
def read_file_execution_data(execution_data, tag_name='run_name'):

    collections_data, collections_columns = {}, None
    for exec_id, exec_step in execution_data.items():
        exec_key = exec_step['features'][tag_name]
        collections_data[exec_key] = {}

        log_stream.info(' -----> Run reference "' + exec_key + '" ... ')

        data_list, columns_list = [], []
        for exec_subkey in exec_step.keys():
            for exec_type, exec_value in exec_step[exec_subkey].items():
                columns_list.append(exec_type)
                data_list.append(exec_value)

            if 'run_domain_reference' not in columns_list:
                log_stream.error(' ===> The field "run_domain_reference" must be defined in the execution "' +
                                 exec_key + '" datasets')
                raise RuntimeError('Insert the key "run_domain_reference" in the execution datasets to skip the error.')

            if 'view_warnings' not in columns_list:
                log_stream.warning(' ===> The field "view_warnings" is not found in the execution "' +
                                   exec_key + '" datasets. The default value will be set to "true"')
                columns_list.append('view_warnings')
                data_list.append(True)
            if 'view_execution' not in columns_list:
                log_stream.warning(' ===> The field "view_execution" is not found in the execution "' +
                                   exec_key + '" datasets. The default value will be set to "true"')
                columns_list.append('view_execution')
                data_list.append(True)

        collections_data[exec_key] = data_list
        if collections_columns is None:
            collections_columns = columns_list

        log_stream.info(' -----> Run reference "' + exec_key + '" ... DONE')

    execution_df = pd.DataFrame.from_dict(collections_data, orient='index', columns=collections_columns)

    return execution_df

# -------------------------------------------------------------------------------------
