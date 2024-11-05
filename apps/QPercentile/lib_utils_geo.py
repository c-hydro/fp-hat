"""
Library Features:

Name:          lib_utils_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20241104'
Version:       '3.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import os
import numpy as np

from lib_info_args import logger_name, zip_extension

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to search channel network index
def search_channel_network_idx(cnet_data, cnet_value=10):

    cnet_1d = cnet_data.values.flatten()
    cnet_idx = np.argwhere(cnet_1d == cnet_value)[:, 0]

    return cnet_idx
# ----------------------------------------------------------------------------------------------------------------------
