"""
Library Features:

Name:          lib_data_io_binary
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os
import numpy as np

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to read file settings
def read_file_binary(file_name, file_dim_x=None, file_dim_y=None, file_ratio_factor=1, file_type=np.int32):
    if os.path.exists(file_name):
        data_tmp = np.fromfile(file_name, dtype=file_type)
        data_map = np.reshape(data_tmp, (int(file_dim_x), int(file_dim_y)))
        data_var = np.transpose(data_map.astype(float) / file_ratio_factor)
    else:
        log_stream.error(' ===> Error in reading settings file "' + file_name + '"')
        raise IOError('File not found')
    return data_var
# -------------------------------------------------------------------------------------
