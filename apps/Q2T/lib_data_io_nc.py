"""
Library Features:

Name:          lib_data_io_nc
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os
import numpy as np
import xarray as xr

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to read file settings
def read_file_nc(file_name, var_name='Discharge', var_ratio_factor=1):
    if os.path.exists(file_name):
        file_dset = xr.open_mfdataset(file_name, decode_times=False)
        data_var = np.flipud(file_dset[var_name].values)
        data_var = data_var / var_ratio_factor
    else:
        log_stream.warning(' ===> File "' + file_name + '" not found')
        data_var = None
    return data_var
# -------------------------------------------------------------------------------------
