"""
Library Features:

Name:          lib_data_analysis
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import math
import numpy as np
import matplotlib.pylab as plt
import warnings

from scipy.stats import genextreme

from lib_info_args import logger_name

# Logging
warnings.filterwarnings("ignore")
logging.getLogger('numpy').setLevel(logging.WARNING)
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# method to compute T(Q)
def compute_q2t(q_data, q_index, statistics_params, geo_area,
                no_data_t=-9999, max_value_t=500, debug_flag=0):

    shape, scale, location = statistics_params[0, 0], statistics_params[0, 1], statistics_params[0, 2]

    kt = np.zeros(shape=[q_index.shape[0], q_index.shape[1]])
    kt[:, :] = q_data/q_index
    kt[kt < 0.0] = 0.0
    P = genextreme.cdf(kt, -shape, location, scale)

    T = np.zeros(shape=[kt.shape[0], kt.shape[1]])
    T[:, :] = 1.0 / (1.0 - P)
    T[geo_area < 1.0] = np.nan
    T[T == np.nan] = no_data_t
    T[T > max_value_t] = max_value_t

    if debug_flag == 1:
        plt.figure(1)
        plt.imshow(T, vmin=-2, vmax=20)
        plt.colorbar()
        plt.show()
        plt.title(['Time: '])
        plt.close()

        plt.figure(2)
        plt.imshow(q_index, vmin=-2, vmax=20)
        plt.colorbar()
        plt.show()
        plt.close()

    return T
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to organize geo parameters
def organize_geo_parameters(obj_geo, obj_watermark=None, dim_km=0.1705, no_data=-9999):

    geo_dataset = obj_geo.values
    geo_x = obj_geo['west_east'].values
    geo_y = obj_geo['south_north'].values

    geo_dataset = geo_dataset * math.pow(dim_km, 2.0)

    if obj_watermark is not None:
        wt_values = obj_watermark.values
        geo_dataset[wt_values < 0] = no_data

    dim_x, dim_y = geo_dataset.shape

    obj_data = {'geo_dataset': geo_dataset, 'geo_x': geo_x, 'geo_y': geo_y,
                'dim_x': dim_x, 'dim_y': dim_y}

    return obj_data

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to organize statistics parameters
def organize_statistic_parameters(obj_statistics_data, params_tag='domain_params_gev', q_index_flag='q_index'):

    obj_params = obj_statistics_data[params_tag]
    obj_q_index = obj_statistics_data[q_index_flag]

    t = np.array([1.1, 1.2, 3.0, 4.0])
    shape, scale, location = obj_params[0, 0], obj_params[0, 1], obj_params[0, 2]

    cdf = genextreme.cdf(t, -shape, location, scale)
    T = cdf * 0.0
    T = 1 / (1 - cdf)

    obj_data = {'params': obj_params, 'q_index': obj_q_index, 'cdf': cdf, 'T': T}

    return obj_data
# -------------------------------------------------------------------------------------
