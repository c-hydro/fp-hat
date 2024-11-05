"""
Library Features:

Name:          lib_data_analysis
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20241104'
Version:       '1.0.0'
"""
# ----------------------------------------------------------------------------------------------------------------------
# Library
import logging
import warnings

from lib_utils_io import create_dframe
from lib_info_args import logger_name

# Logging
warnings.filterwarnings("ignore")
logging.getLogger('numpy').setLevel(logging.WARNING)
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute quantile(s)
def compute_quantile(ensemble_data, ensemble_list=None, geo_idx=None, quantile_list=0.8):

    if isinstance(quantile_list, (int, float)):
        quantile_list = [quantile_list]

    # create data frame data
    ensemble_dframe_raw = create_dframe(
        data_values=ensemble_data, data_index=geo_idx,
        column_name=ensemble_list, index_name='index')

    # create data frame quantiles
    ensemble_dframe_quantile = ensemble_dframe_raw.quantile(quantile_list, axis=1, numeric_only=True).T
    # join data frames
    ensemble_dframe_quantile = ensemble_dframe_quantile.join(ensemble_dframe_raw)

    return ensemble_dframe_quantile

# ----------------------------------------------------------------------------------------------------------------------
