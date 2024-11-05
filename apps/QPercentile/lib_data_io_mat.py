"""
Library Features:

Name:          lib_data_io_mat
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os
from scipy.io import loadmat

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to read file statistics
def read_file_stats(file_name, fields_mapping=None, fields_excluded=None):

    if fields_excluded is None:
        fields_excluded = ['__header__', '__version__', '__globals__']
    if fields_mapping is None:
        fields_mapping = {
            'a1dT': 'T', 'a1dtA': 'TA', 'a2dAS': 'AS',
            'a2dKtDom': 'domain_kt', 'a2dParGevDom': 'domain_params_gev',
            'a2dQindex': 'q_index', 'a3dParGev': 'params_gev'
        }

    if os.path.exists(file_name):
        file_data = loadmat(file_name)
    else:
        log_stream.error(' ===> Error in reading statistics file "' + file_name + '"')
        raise IOError('File not found')

    fields_data = {}
    for fields_name_in in list(file_data.keys()):
        if fields_name_in not in fields_excluded:
            if fields_name_in in list(fields_mapping.keys()):
                fields_name_out = fields_mapping[fields_name_in]
                fields_data[fields_name_out] = file_data[fields_name_in]
            else:
                log_stream.error(' ===> Field name "' + fields_name_in + '" is expected but not included')
                raise RuntimeError('Set the field name in the statistics file')

    return fields_data
# -------------------------------------------------------------------------------------
