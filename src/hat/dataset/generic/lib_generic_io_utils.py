"""
Library Features:

Name:          lib_generic_io_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190527'
Version:       '1.0.2'
"""
#######################################################################################
# Library
import logging
import warnings

import numpy as np
import xarray as xr
import pandas as pd

from copy import deepcopy

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to add attribute dictionary to object
def addVarAttrs(oVarObj, oVarAttrs):
    for sAttrKey, oAttrValue in oVarAttrs.items():

        if isinstance(oVarObj, xr.DataArray):
            oVarObj.attrs[sAttrKey] = oAttrValue
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                setattr(oVarObj, sAttrKey, oAttrValue)
                try:
                    oVarObj._metadata.append(sAttrKey)
                except BaseException:
                    Exc.getExc(' =====> ERROR: add attribute(s) to dataframe obj in _metadata list FAILED! ', 1, 1)
    return oVarObj
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to merge a list of attribute dictionary
def mergeVarAttrs(oVarAttrs):
    if not isinstance(oVarAttrs, list):
        oVarAttrs = [oVarAttrs]

    oVarAttrs_MERGE = {}
    for oVarAttr in oVarAttrs:
        if oVarAttr is not None:
            for sVarKey, oVarValue in oVarAttr.items():
                oVarAttrs_MERGE[sVarKey] = oVarValue
    return oVarAttrs_MERGE
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a attribute(s) dictionary
def createVarAttrs(oVarInfo):
    oVarAttrs = {}
    for sVarKey, oVarValue in oVarInfo.items():
        oVarAttrs[sVarKey] = oVarValue
    return oVarAttrs
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to clip probabilistic outlier(s)
def clipVar1D(oVarData_WS, sVarData_CHECK='first'):

    if sVarData_CHECK == 'first':
        iVarData_CHECK = 0

    oVarName_LIST = list(oVarData_WS)
    a1dVarData_VALUE = np.zeros([oVarName_LIST.__len__()])
    for iVarID, sVarName in enumerate(oVarName_LIST):

        if np.all(np.isnan(oVarData_WS[sVarName].values)):
            Exc.getExc(' =====> WARNING: time-series of probabilistic ensemble ' + sVarName + ' is null!', 2, 1)

        dVarData = oVarData_WS[sVarName].values[iVarData_CHECK]
        a1oVarData_CHECK = list(oVarData_WS[sVarName].values)
        if np.isnan(dVarData):

            Exc.getExc(' =====> WARNING: time-series of probabilistic ensemble ' + sVarName +
                       ' start with nan! First finite value will be searched in time-series!', 2, 1)

            for iN in range(0, a1oVarData_CHECK.__len__()):
                dVarData_CHECK = oVarData_WS[sVarName].values[iN]

                if not np.isnan(dVarData_CHECK):
                    dVarData = oVarData_WS[sVarName].values[iN]
                    a1dVarData_VALUE[iVarID] = dVarData
                    Exc.getExc(' =====> WARNING: time-series of probabilistic ensemble ' + sVarName +
                               ' has first finite value ' + str(dVarData) + ' at ' + str(iN) + ' position!', 2, 1)
                    break
                else:
                    a1dVarData_VALUE[iVarID] = np.nan
        else:
            a1dVarData_VALUE[iVarID] = dVarData

    # Count occurrences of time-series first values and set to NaNs outlier(s)
    a1dVarData_UNIQUE, a1iVarData_COUNT = np.unique(a1dVarData_VALUE, return_counts=True)

    if not np.all(np.isnan(a1dVarData_VALUE)):

        if a1dVarData_UNIQUE.shape[0] > 1:

            a1iVarData_COUNT_SORT = np.sort(a1iVarData_COUNT)
            a1iVarData_INDEX_SORT = np.argsort(a1iVarData_COUNT)

            a1dVarData_UNIQUE_SORT = a1dVarData_UNIQUE[a1iVarData_INDEX_SORT]

            a1iVarData_COUNT_SORT = a1iVarData_COUNT_SORT[::-1]
            a1dVarData_UNIQUE_SORT = a1dVarData_UNIQUE_SORT[::-1]

            a1sVarData_CHECK = ', '.join(str(dVarData_CHECK) for dVarData_CHECK in a1dVarData_UNIQUE_SORT)
            a1sVarCount_CHECK = ', '.join(str(dVarCount_CHECK) for dVarCount_CHECK in a1iVarData_COUNT_SORT)
            Exc.getExc(' =====> WARNING: probabilistic ensembles start with different values [ ' +
                       a1sVarData_CHECK + '] with occurrences [' +
                       a1sVarCount_CHECK + '] . Outliers will be removed.', 2, 1)

            for iVarData_INDEX, (iVarData_COUNT, dVarData_OUTLIER) in enumerate(
                    zip(a1iVarData_COUNT_SORT[1:], a1dVarData_UNIQUE_SORT[1:])):

                iVarData_OUTLIER = np.where(a1dVarData_VALUE == dVarData_OUTLIER)[0][0]
                sVarName_OUTLIER = oVarName_LIST[iVarData_OUTLIER]

                oVarData_DA = oVarData_WS[sVarName_OUTLIER].values
                oVarTime_DA = oVarData_WS['time'].values

                a1dVarNAN_DA = np.zeros([oVarData_DA.size])
                a1dVarNAN_DA[:] = np.nan
                oVarData_NAN = xr.DataArray(a1dVarNAN_DA, coords={'time': oVarTime_DA}, dims=['time'])
                oVarData_WS[sVarName_OUTLIER] = oVarData_NAN

                Exc.getExc(' =====> WARNING: the probabilistic ensemble ' + sVarName_OUTLIER
                           + ' starts with outlier value ' + str(dVarData_OUTLIER) + ' ! Set all values to NA', 2, 1)
    else:
        Exc.getExc(' =====> WARNING: all probabilistic ensembles have starting NA value for all time-series!', 2, 1)

    return oVarData_WS

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to merge multiple 1D data array
def mergeVar1D(oVarData):
    oVarData_WS = xr.merge(oVarData)
    return oVarData_WS
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to reduce data array 3D to data array 2D
def reduceDArray3D(oVarDArray, sVarIndex='last'):

    if 'time' in list(oVarDArray.dims) and oVarDArray.time.__len__() > 1:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            oVarDArray_AVG = oVarDArray.mean(dim=['south_north', 'west_east'])
            a1oVarIDX_FINITE = list(np.where(np.isfinite(oVarDArray_AVG))[0])

            if not a1oVarIDX_FINITE:
                a1oVarIDX_FINITE = None

    else:
        a1oVarIDX_FINITE = None

    if a1oVarIDX_FINITE is not None:
        oVarDArray_SEL = oVarDArray.isel(time=a1oVarIDX_FINITE)
    else:
        oVarDArray_SEL = oVarDArray

    if 'time' in list(oVarDArray_SEL.dims) and oVarDArray_SEL.time.__len__() > 1:
        if sVarIndex == 'first':
            oVarDArray_SEL = oVarDArray_SEL.isel(time=[0])
        elif sVarIndex == 'last':
            oVarDArray_SEL = oVarDArray_SEL.isel(time=[-1])
        else:
            if isinstance(sVarIndex, str):
                sVarIndex = list(sVarIndex)
            oVarDArray_SEL = oVarDArray_SEL.isel(time=sVarIndex)

    if 'time' in list(oVarDArray_SEL.dims):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            oVarDArray_AVG = oVarDArray_SEL.mean(dim=['south_north', 'west_east'])
            a1oVarIDX_NAN = list(np.where(np.isnan(oVarDArray_AVG))[0])
            if not a1oVarIDX_NAN:
                a1oVarIDX_NAN = None
    else:
        a1oVarIDX_NAN = None
    if a1oVarIDX_NAN is not None:
        if a1oVarIDX_NAN.__len__() == 1 and oVarDArray_SEL.time.__len__() == 1:
            oVarDArray_SEL = None

    return oVarDArray_SEL
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create 2D variable in data array format
def createDArray2D(oVarDArray, sVarName_IN='rain', sVarName_OUT=None, oVarCoords=None, oVarDims=None):

    # Initialize coord(s) and dim(s)
    if oVarCoords is None:
        oVarCoords = ['time']
    if oVarDims is None:
        oVarDims = ['time']
    if sVarName_OUT is None:
        sVarName_OUT = sVarName_IN

    oVarDArray_SEL = deepcopy(oVarDArray)
    if oVarDArray_SEL['time'].__len__() > 1:
        oVarDArray_SEL = reduceDArray3D(oVarDArray_SEL)

    if sVarName_IN != sVarName_OUT:
        oVarDArray_SEL.name = sVarName_OUT

    return oVarDArray_SEL

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create 2D variable statistics
def createStats2D(oVarStats, oVarData, sVarNameGroup):

    if oVarStats is None:
        oVarStats = {}

    if sVarNameGroup not in list(oVarStats.keys()):
        oVarStats[sVarNameGroup] = {}
        oVarStats[sVarNameGroup]['min'] = []
        oVarStats[sVarNameGroup]['max'] = []
        oVarStats[sVarNameGroup]['average'] = []

    dVarMax = np.nanmax(oVarData.values)
    dVarMin = np.nanmin(oVarData.values)
    dVarAvg = np.nanmean(oVarData.values)

    if not oVarStats[sVarNameGroup]['min']:
        oVarStats[sVarNameGroup]['min'] = [dVarMin]
    else:
        oVarStats[sVarNameGroup]['min'].append(dVarMin)

    if not oVarStats[sVarNameGroup]['max']:
        oVarStats[sVarNameGroup]['max'] = [dVarMax]
    else:
        oVarStats[sVarNameGroup]['max'].append(dVarMax)

    if not oVarStats[sVarNameGroup]['average']:
        oVarStats[sVarNameGroup]['average'] = [dVarAvg]
    else:
        oVarStats[sVarNameGroup]['average'].append(dVarAvg)

    return oVarStats
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create 1D variable statistics
def createStats1D(oVarStats, oVarData, sVarNameGroup):

    if oVarStats is None:
        oVarStats = {}

    if sVarNameGroup not in list(oVarStats.keys()):
        oVarStats[sVarNameGroup] = {}
        oVarStats[sVarNameGroup]['min'] = []
        oVarStats[sVarNameGroup]['max'] = []
        oVarStats[sVarNameGroup]['average'] = []

    if np.isnan(oVarData.values).all():
        dVarMax = np.nan
        dVarMin = np.nan
        dVarAvg = np.nan
        Exc.getExc(' =====> WARNING: in calculating 1D stats for type ' + oVarData.name
                   + ' all values in time series are null!', 2, 1)
    else:
        dVarMax = np.nanmax(oVarData.values)
        dVarMin = np.nanmin(oVarData.values)
        dVarAvg = np.nanmean(oVarData.values)

    if isinstance(dVarMax, np.float64):
        dVarMax = dVarMax.astype(np.float32)
    if isinstance(dVarMin, np.float64):
        dVarMin = dVarMin.astype(np.float32)
    if isinstance(dVarAvg, np.float64):
        dVarAvg = dVarAvg.astype(np.float32)

    if not oVarStats[sVarNameGroup]['min']:
        oVarStats[sVarNameGroup]['min'] = [dVarMin]
    else:
        oVarStats[sVarNameGroup]['min'].append(dVarMin)

    if not oVarStats[sVarNameGroup]['max']:
        oVarStats[sVarNameGroup]['max'] = [dVarMax]
    else:
        oVarStats[sVarNameGroup]['max'].append(dVarMax)

    if not oVarStats[sVarNameGroup]['average']:
        oVarStats[sVarNameGroup]['average'] = [dVarAvg]
    else:
        oVarStats[sVarNameGroup]['average'].append(dVarAvg)

    return oVarStats
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create 1D variable in data array format
def createDArray1D(oVarDArray, oVarPeriod, sVarName_IN='rain', sVarName_OUT=None, oVarCoords=None, oVarDims=None):

    # Initialize coord(s) and dim(s)
    if oVarCoords is None:
        oVarCoords = ['time']
    if oVarDims is None:
        oVarDims = ['time']
    if sVarName_OUT is None:
        sVarName_OUT = sVarName_IN

    # Define data period
    oVarPeriod_DATA = pd.DatetimeIndex(oVarDArray.time.to_pandas().values)
    oVarPeriod_SEL = oVarPeriod.intersection(oVarPeriod_DATA)

    # Get data, attribute(s) and encoding(s) for selected data array
    oVarDArray_SEL = oVarDArray.loc[dict(time=oVarPeriod_SEL)]
    oAttributeDArray_SEL = oVarDArray_SEL.attrs
    try:
        oEncodingDArray_SEL = {'_FillValue': float(oVarDArray_SEL.encoding['_FillValue']),
                               'scale_factor': int(oVarDArray_SEL.encoding['scale_factor'])}
    except BaseException:
        Exc.getExc(' =====> WARNING: in creating data array 1D _FillValue and scale_factor are not defined! Try'
                   'to correct with default values (_FillValue=-9999.0; scale_factor=1) ', 2, 1)
        oEncodingDArray_SEL = {'_FillValue': -9999.0,
                               'scale_factor': 1}

    # Initialize empty data array
    a1dVarArray_EMPTY = np.zeros([oVarPeriod.__len__()])
    a1dVarArray_EMPTY[:] = np.nan
    oVarDArray_EMPTY = xr.DataArray(a1dVarArray_EMPTY, name=sVarName_IN,
                                    attrs=oAttributeDArray_SEL, # encoding=oEncodingDArray_SEL,
                                    dims=oVarDims[0], coords={oVarCoords[0]: (oVarDims[0], oVarPeriod)})
    # Combine empty data array with selected data array
    oVarDSet_FILLED = oVarDArray_EMPTY.combine_first(oVarDArray_SEL)

    if sVarName_IN != sVarName_OUT:
        oVarDSet_FILLED.name = sVarName_OUT

    return oVarDSet_FILLED
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to merge multiple 2D data array
def mergeVar2D(oVarData):
    oVarData_WS = xr.merge(oVarData)
    return oVarData_WS
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create 2D variable in data array format
def createVar2D(a2dVarData, a2dVarGeoX, a2dVarGeoY, sVarName=None, oVarDims=None, oVarCoords=None,
                oVarAttributes=None, oVarEncoding=None):

    if oVarCoords is None:
        oVarCoords = ['Latitude', 'Longitude']
    if oVarDims is None:
        oVarDims = ['south_north', 'west_east']

    if sVarName is not None:
        oVarData = xr.DataArray(a2dVarData, name=sVarName, dims=oVarDims,
                                attrs=oVarAttributes, # encoding=oVarEncoding,
                                coords={oVarCoords[0]: (oVarDims, a2dVarGeoX),
                                        oVarCoords[1]: (oVarDims, a2dVarGeoY)})
    else:
        oVarData = xr.DataArray(a2dVarData, dims=oVarDims,
                                attrs=oVarAttributes, # encoding=oVarEncoding,
                                coords={oVarCoords[0]: (oVarDims, a2dVarGeoX),
                                        oVarCoords[1]: (oVarDims, a2dVarGeoY)})
    return oVarData
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to clip data 2D/3D using a min/max threshold(s) and assign a missing value
def clipVarMD(oVarData, oVarValidRange=[None, None], dVarMissingValue=None):

    # Set variable valid range
    if oVarValidRange[0] is not None:
        dVarValidRange_MIN = float(oVarValidRange[0])
    else:
        dVarValidRange_MIN = None
    if oVarValidRange[1] is not None:
        dVarValidRange_MAX = float(oVarValidRange[1])
    else:
        dVarValidRange_MAX = None
    # Set variable missing value
    if dVarMissingValue is None:
        dVarMissingValue_MIN = dVarValidRange_MIN
        dVarMissingValue_MAX = dVarValidRange_MAX
    else:
        dVarMissingValue_MIN = dVarMissingValue
        dVarMissingValue_MAX = dVarMissingValue

    # Apply min and max condition(s)
    if dVarValidRange_MIN is not None:
        oVarData = oVarData.where(oVarData >= dVarValidRange_MIN, dVarMissingValue_MIN)
    if dVarValidRange_MAX is not None:
        oVarData = oVarData.where(oVarData <= dVarValidRange_MAX, dVarMissingValue_MAX)

    return oVarData
# -------------------------------------------------------------------------------------
