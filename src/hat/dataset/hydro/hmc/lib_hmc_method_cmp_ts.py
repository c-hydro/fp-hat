"""
Library Features:

Name:          lib_hmc_method_cmp_ts
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190206'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import warnings
import pandas as pd
import xarray as xr
import numpy as np

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to create an empty dataframe with datetime index
def combineVarDataArray(oDataArray, sDataName, oDataTime):
    oVarDSet_DATA = oDataArray.to_dataset(name=sDataName)
    oVarDSet_GENERIC = xr.Dataset(coords={'time': (['time'], pd.to_datetime(oDataTime))})
    oVarDSet_FILLED = oVarDSet_GENERIC.combine_first(oVarDSet_DATA)

    oVarDArray_FILLED = oVarDSet_FILLED[sDataName]
    oVarDArray = oVarDArray_FILLED.loc[sDataName]

    return oVarDArray
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create an empty dataframe with datetime index
def createVarDataFrame(oDataTime):
    oDataFrame = pd.DataFrame({'time': oDataTime})
    oDataFrame = oDataFrame.set_index('time')
    return oDataFrame
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to find finite gridded data steps along time
def findVarFinite(oVarData, sVarName='air_temperature', sVarMask='Terrain', sVarTime='time'):

    oVarData_CHECK = oVarData.where(oVarData[sVarMask] > 0).mean(dim=['south_north', 'west_east'])[sVarName]
    oVarTime_CHECK = oVarData[sVarTime]

    oVarData_BOOL = xr.ufuncs.isfinite(oVarData_CHECK)

    oVarTime_FINITE = pd.DatetimeIndex(oVarTime_CHECK.where(oVarData_BOOL).dropna(dim='time').values)
    oVarData_FINITE = oVarData_CHECK.sel(time=oVarTime_FINITE)

    return oVarData_FINITE, oVarTime_FINITE
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to mean gridded data steps along time
def cmpVarMean(oVarData, oVarTime_FROM=None, oVarTime_TO=None):

    if (oVarTime_FROM is not None) and (oVarTime_TO is not None):
        oVarData_SEL = oVarData.where(
            (oVarData['time'] >= oVarTime_FROM.to_datetime64()) & (oVarData['time'] <= oVarTime_TO.to_datetime64()),
            np.nan)
    elif (oVarTime_FROM is not None) and (oVarTime_TO is None):
        oVarData_SEL = oVarData.where(
            (oVarData['time'] >= oVarTime_FROM.to_datetime64()), np.nan)
    elif (oVarTime_FROM is None) and (oVarTime_TO is not None):
        oVarData_SEL = oVarData.where(
            (oVarData['time'] <= oVarTime_TO.to_datetime64()), np.nan)
    else:
        oVarData_SEL = oVarData

    # Apply mean function (and suppress runtime warnings)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        # oVarData_CMP_TEST = oVarData.mean(dim=['south_north', 'west_east'])
        oVarData_CMP = oVarData_SEL.mean(dim=['south_north', 'west_east'])
        oVarTS_CMP = oVarData_CMP.to_pandas()

    return oVarTS_CMP
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to sum gridded data steps along time in a cumulative mode
def cmpVarCumSum(oVarData, oVarTime_FROM=None, oVarTime_TO=None, dVarData_MIN=0, dVarData_MAX=None):

    if (oVarTime_FROM is not None) and (oVarTime_TO is not None):
        oVarData_SEL = oVarData.where(
            (oVarData['time'] >= oVarTime_FROM.to_datetime64()) & (oVarData['time'] <= oVarTime_TO.to_datetime64()),
            np.nan)
    elif (oVarTime_FROM is not None) and (oVarTime_TO is None):
        oVarData_SEL = oVarData.where(
            (oVarData['time'] >= oVarTime_FROM.to_datetime64()), np.nan)
    elif (oVarTime_FROM is None) and (oVarTime_TO is not None):
        oVarData_SEL = oVarData.where(
            (oVarData['time'] <= oVarTime_TO.to_datetime64()), np.nan)
    else:
        oVarData_SEL = oVarData

    # Apply sum function (and suppress runtime warnings)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        if 'Mask' in list(oVarData.coords):
            oVarData_CMP = oVarData_SEL.where(oVarData.Mask > 0)
        else:
            oVarData_CMP = oVarData_SEL

        if dVarData_MIN is not None:
            oVarData_CMP = oVarData_CMP.where(oVarData_CMP > dVarData_MIN)
        if dVarData_MAX is not None:
            oVarData_CMP = oVarData_CMP.where(oVarData_CMP < dVarData_MAX)

        oVarData_CMP = oVarData_CMP.mean(dim=['south_north', 'west_east'])
        oVarData_CMP = oVarData_CMP.cumsum(dim=['time'])

        if (oVarTime_FROM is not None) and (oVarTime_TO is not None):
            oVarData_FILTER = oVarData_CMP.where(
                (oVarData_CMP['time'] >= oVarTime_FROM.to_datetime64()) & (oVarData_CMP['time'] <= oVarTime_TO.to_datetime64()),
                np.nan)
        elif (oVarTime_FROM is not None) and (oVarTime_TO is None):
            oVarData_FILTER = oVarData_CMP.where(
                (oVarData_CMP['time'] >= oVarTime_FROM.to_datetime64()), np.nan)
        elif (oVarTime_FROM is None) and (oVarTime_TO is not None):
            oVarData_FILTER = oVarData.where(
                (oVarData_CMP['time'] <= oVarTime_TO.to_datetime64()), np.nan)
        else:
            oVarData_FILTER = oVarData_CMP

        oVarTS_CMP = oVarData_FILTER.to_pandas()

    return oVarTS_CMP
# -------------------------------------------------------------------------------------
