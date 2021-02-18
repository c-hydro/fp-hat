"""
Library Features:

Name:          lib_hmc_data_gridded
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20191023'
Version:       '1.0.1'
"""

#######################################################################################
# Library
import logging
import warnings
import xarray as xr
import pandas as pd
import numpy as np
import datetime
import dask.array as da
import tempfile
import shutil
import gzip
import os

from copy import deepcopy

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to add variable to datasets
def addVar3D(oFileData, a3dVarData, a2dVarGeoX, a2dVarGeoY, iTimeStep=0, sVarName='Terrain', sTimeName='time'):

    # Check if variable is in file list (considering the upper and lower cases)
    oFileVars = list(oFileData.variables)
    if sVarName.lower() in oFileVars:
        sVarFile = oFileVars.index(sVarName.lower())
        oFileData = oFileData.rename({sVarFile: sVarName})
    elif sVarName.upper() in oFileVars:
        sVarFile = oFileVars.index(sVarName.upper())
        oFileData = oFileData.rename({sVarFile: sVarName})

    # Check availability of variable in datasets
    if sVarName not in oFileVars:

        # Create a data array for adding in dataset
        oVarData = xr.DataArray(a3dVarData,
                                dims=['time', 'south_north', 'west_east'],
                                coords={
                                    'time': ('time', iTimeStep),
                                    'Longitude': (['south_north', 'west_east'], a2dVarGeoX),
                                    'Latitude': (['south_north', 'west_east'], a2dVarGeoY)})

        oFileData[sVarName] = oVarData

    return oFileData
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to add variable to datasets
def addVar2D(oFileData, a2dVarData, a2dVarGeoX, a2dVarGeoY, sVarName='Terrain'):

    # Check if variable is in file list (considering the upper and lower cases)
    oFileVars = list(oFileData.variables)
    if sVarName.lower() in oFileVars:
        iVarID = oFileVars.index(sVarName.lower())
        sVarFile = oFileVars[iVarID]
        oFileData = oFileData.rename({sVarFile: sVarName})
    elif sVarName.upper() in oFileVars:
        iVarID = oFileVars.index(sVarName.upper())
        sVarFile = oFileVars[iVarID]
        oFileData = oFileData.rename({sVarFile: sVarName})

    # Check availability of variable in datasets
    if sVarName not in oFileVars:

        # Create a data array for adding in dataset
        oVarData = xr.DataArray(a2dVarData,
                                dims=['south_north', 'west_east'],
                                coords={'Longitude': (['south_north', 'west_east'], a2dVarGeoX),
                                        'Latitude': (['south_north', 'west_east'], a2dVarGeoY)})

        oFileData[sVarName] = oVarData

    return oFileData
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get file gridded with 3d variable
def getVar3D(oFileName, oFileTime, oDataTime=None, oFileVarsSource=None, oFileVarsOutcome=None,
             oFileVars_DEFAULT=None, sFolderTmp=None, sSuffixTmp='.nc', oFileDims_LUT=None,
             oDataGeo=None):

    if oFileVars_DEFAULT is None:
        oFileVars_DEFAULT = ['Longitude', 'Latitude', 'Terrain', 'time', 'crs']

    if oFileDims_LUT is None:
        oFileDims_LUT = {'X': 'west_east', 'Y': 'south_north', 'time': 'time'}

    if isinstance(oFileName, str):
        oFileName = [oFileName]

    if oFileVarsSource is not None:
        oFileVarsSource_SELECTED = oFileVarsSource + oFileVars_DEFAULT
    else:
        oFileVarsSource_SELECTED = oFileVarsSource

    if oFileVarsOutcome is not None:
        oFileVarsOutcome_SELECTED = oFileVarsOutcome + oFileVars_DEFAULT
    else:
        oFileVarsOutcome_SELECTED = oFileVarsSource_SELECTED

    # Sort filename(s)
    oFileName = sorted(oFileName)

    oFileName_LIST = []
    for sFileName_IN in oFileName:
        if os.path.isfile(sFileName_IN):
            if sFileName_IN.endswith(".gz"):
                oFileName_UNZIP = gzip.open(sFileName_IN, 'rb')
                if sFolderTmp is not None:
                    oFileName_TMP = tempfile.NamedTemporaryFile(dir=sFolderTmp, suffix=sSuffixTmp, delete=False)
                else:
                    oFileName_TMP = tempfile.NamedTemporaryFile(suffix=sSuffixTmp, delete=False)

                try:
                    shutil.copyfileobj(oFileName_UNZIP, oFileName_TMP)
                    oFileName_UNZIP.close()
                    oFileName_TMP.close()
                    sFileName_TMP = oFileName_TMP.name

                except BaseException:

                    Exc.getExc(' =====> WARNING: problems occur in opening ' + sFileName_IN + ' in tmp folder!', 2, 1)

                    oFileName_UNZIP.close()
                    oFileName_TMP.close()

                    if os.path.exists(oFileName_TMP.name):
                        os.remove(oFileName_TMP.name)
                    sFileName_TMP = None
            else:
                sFileName_TMP = sFileName_IN

            if sFileName_TMP is not None:
                oFileName_LIST.append(sFileName_TMP)

    # Check file handle(s) availability
    if oFileName_LIST:

        # Preprocess file(s) to control variable(s) and time(s)
        oFileVarsSource_EXPECTED = []
        for sFileName_LIST in oFileName_LIST:
            with xr.open_dataset(sFileName_LIST) as oDSet:
                oFileVars_LIST = list(oDSet.data_vars)
            oFileVarsSource_EXPECTED.extend(oElem for oElem in oFileVars_LIST if oElem not in oFileVarsSource_EXPECTED)

        oDataTime_EXPECTED = []
        for sDataTime in oDataTime:
            sDataTime = sDataTime.replace(microsecond=0, nanosecond=0)
            oDataTime_EXPECTED.append(sDataTime)

        oFileData_ALL = None
        oFileVarsSource_SELECTED_ID = None
        oFileVarsOutcome_SELECTED_ID = None
        for iFileID_LIST, sFileName_LIST in enumerate(oFileName_LIST):
            with xr.open_dataset(sFileName_LIST) as oFileData:

                # Check time information dimension
                if 'time' not in list(oFileData.dims):
                    oFileData = oFileData.assign_coords(time=pd.to_datetime(oDataTime_EXPECTED))
                    oFileData.coords['time'] = oFileData.coords['time'].astype('datetime64[ns]')
                    oFileData.coords['time'].attrs['calendar'] = 'gregorian'
                    oDataTime_SELECT = oDataTime_EXPECTED
                else:
                    oDataTime_DEFINED = pd.to_datetime(oFileData.coords['time'].values)
                    oDataTime_SELECT = []
                    for sDataTime in oDataTime_DEFINED:
                        sDataTime = sDataTime.replace(microsecond=0, nanosecond=0)
                        oDataTime_SELECT.append(sDataTime)

                # Check time information format
                if not isinstance(oFileData['time'], datetime.datetime):
                    oFileData = oFileData.assign_coords(time=pd.to_datetime(oDataTime_SELECT))
                    oFileData.coords['time'] = oFileData.coords['time'].astype('datetime64[ns]')
                    oFileData.coords['time'].attrs['calendar'] = 'gregorian'

                # Set fill value for crs field
                if "crs" in list(oFileData.variables.keys()):
                    oFileData['crs'].attrs['_FillValue'] = -9999

                if oFileVarsSource_SELECTED_ID is None:
                    oFileVarsSource_SELECTED_ID = deepcopy(oFileVarsSource_SELECTED)

                if oFileVarsOutcome_SELECTED_ID is None:
                    oFileVarsOutcome_SELECTED_ID = deepcopy(oFileVarsOutcome_SELECTED)

                # Drop variables unselected
                oFileData = removeVar2D(oFileData, oFileVarsSource_EXPECTED, oFileVarsSource_SELECTED)

                # Set values for Terrain field
                if oDataGeo is not None:
                    if 'Terrain' not in list(oFileData.variables):
                        oFileData = addVar2D(oFileData,
                                             oDataGeo.a2dGeoData, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                             sVarName='Terrain')
                    if 'Longitude' not in list(oFileData.variables):
                        oFileData = addVar2D(oFileData,
                                             oDataGeo.a2dGeoX, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                             sVarName='Longitude')
                    if 'Latitude' not in list(oFileData.variables):
                        oFileData = addVar2D(oFileData,
                                             oDataGeo.a2dGeoY, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                             sVarName='Latitude')

                # Drop variables with expected time
                if not pd.DatetimeIndex(oDataTime_EXPECTED).equals(pd.DatetimeIndex(oDataTime_SELECT)):
                    # Define datetime index
                    oDataTIME_INTERSECTION = pd.DatetimeIndex(oDataTime_EXPECTED).intersection(
                        pd.DatetimeIndex(oDataTime_SELECT))

                    # Select data according with datetime index
                    oFileData_SELECTED = oFileData.sel(
                        time=slice(oDataTIME_INTERSECTION[0], oDataTIME_INTERSECTION[-1]))

                    # Info
                    if iFileID_LIST == 0:
                        Exc.getExc(' =====> WARNING: dataset time-steps and expected time-steps are different!', 2, 1)
                else:
                    oFileData_SELECTED = oFileData

                # Get file dimension
                iFileN_LIST = oFileName_LIST.__len__()

                if iFileN_LIST > 1:

                    if oFileData_ALL is not None:

                        oFileVars_DATA = list(oFileData_ALL.variables.keys())
                        bFileVars_CHECK = all(oVar in oFileVars_DATA for oVar in oFileVars_DEFAULT)

                        if not bFileVars_CHECK:
                            oFileVarsSource_SELECTED_N = [oFileVarsSource_SELECTED[iFileID_LIST]] + oFileVars_DEFAULT
                            oFileVarsOutcome_SELECTED_N = [oFileVarsOutcome_SELECTED[iFileID_LIST]] + oFileVars_DEFAULT
                        else:
                            oFileVarsSource_SELECTED_N = [oFileVarsSource_SELECTED[iFileID_LIST]]
                            oFileVarsOutcome_SELECTED_N = [oFileVarsOutcome_SELECTED[iFileID_LIST]]
                    else:
                        oFileVarsSource_SELECTED_N = [oFileVarsSource_SELECTED[iFileID_LIST]] + oFileVars_DEFAULT
                        oFileVarsOutcome_SELECTED_N = [oFileVarsOutcome_SELECTED[iFileID_LIST]] + oFileVars_DEFAULT

                else:
                    oFileVarsSource_SELECTED_N = oFileVarsSource_SELECTED
                    oFileVarsOutcome_SELECTED_N = oFileVarsOutcome_SELECTED

                # Change variables name
                oFileData_IN = oFileData
                oFileData_IN_COORDS = oFileData_IN.coords

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=FutureWarning)

                    oFileData_OUT = xr.Dataset(coords=oFileData_IN_COORDS)
                    for sVarName_IN, sVarName_OUT in zip(oFileVarsSource_SELECTED_N, oFileVarsOutcome_SELECTED_N):

                        if sVarName_IN in list(oFileData_SELECTED.variables.keys()):
                            if (sVarName_IN in oFileVarsSource_SELECTED_ID) and (
                                    sVarName_OUT in oFileVarsOutcome_SELECTED_ID):

                                oVarData_IN = oFileData_IN[sVarName_IN]
                                oVarData_IN_DIMS = oVarData_IN.dims
                                oVarData_IN_COORDS = oVarData_IN.coords
                                oVarDArray = xr.DataArray(oVarData_IN, dims=oVarData_IN_DIMS, coords=oVarData_IN_COORDS)

                                oFileData_OUT[sVarName_OUT] = oVarDArray

                    if oFileData_ALL is None:
                        oFileData_ALL = oFileData_OUT
                    else:
                        oFileData_ALL = oFileData_ALL.merge(oFileData_OUT)
    else:
        oFileData_ALL = None

    # Check dimension(s) name
    if oFileData_ALL is not None:

        oFileDims_GET = list(oFileData_ALL.dims)
        oFileDims_CHECK_KEYS = list(oFileDims_LUT.keys())
        oFileDims_CHECK_VALS = list(oFileDims_LUT.values())

        for sFileDim_GET in oFileDims_GET:

            if sFileDim_GET not in oFileDims_CHECK_VALS:
                Exc.getExc(' =====> WARNING: name of dataset dim ' + sFileDim_GET +
                           ' not in default convention ' + str(oFileDims_CHECK_VALS) + '!', 2, 1)
                bFileDim_UPD = True
            else:
                bFileDim_UPD = False

            if sFileDim_GET in oFileDims_CHECK_KEYS:
                sFileDim_CHECK = oFileDims_LUT[sFileDim_GET]
                if sFileDim_GET != sFileDim_CHECK:
                    oFileData_ALL = oFileData_ALL.rename({sFileDim_GET: sFileDim_CHECK})
                    Exc.getExc(' =====> WARNING: name of dataset dim ' + sFileDim_GET +
                               ' is renamed in ' + sFileDim_CHECK + ' according with the default convention!', 2, 1)
            else:
                if bFileDim_UPD:
                    Exc.getExc(' =====> WARNING: name of dataset dim ' + sFileDim_GET +
                               ' not in default convention!', 2, 1)

    return oFileData_ALL, oFileName_LIST

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get file or file(s) gridded with 2d variable
def getVar2D(oFileName, oFileTime, oFileVarsSource=None, oFileVarsOutcome=None,
             oFileVars_DEFAULT=None, sFolderTmp=None, sSuffixTmp='.nc', oFileDims_LUT=None,
             oDataGeo=None):

    global oFileVarsSource_EXPECTED
    global oFileTime_EXPECTED
    global oFileVarsSource_SELECTED

    if oFileVars_DEFAULT is None:
        oFileVars_DEFAULT = ['Longitude', 'Latitude', 'Terrain', 'time', 'crs']

    if oFileDims_LUT is None:
        oFileDims_LUT = {'X': 'west_east', 'Y': 'south_north', 'time': 'time'}

    if isinstance(oFileName, str):
        oFileName = [oFileName]

    if oFileVarsSource is not None:
        oFileVarsSource_SELECTED = oFileVarsSource + oFileVars_DEFAULT
    else:
        oFileVarsSource_SELECTED = oFileVarsSource

    if oFileVarsOutcome is not None:
        oFileVarsOutcome_SELECTED = oFileVarsOutcome + oFileVars_DEFAULT
    else:
        oFileVarsOutcome_SELECTED = oFileVarsSource_SELECTED

    oFileName_LIST = []
    oFileTime_LIST = []
    for sFileTime_IN, sFileName_IN in zip(oFileTime, oFileName):

        if os.path.isfile(sFileName_IN):
            if sFileName_IN.endswith(".gz"):

                oFileName_UNZIP = gzip.open(sFileName_IN, 'rb')

                if sFolderTmp is not None:
                    oFileName_TMP = tempfile.NamedTemporaryFile(dir=sFolderTmp, suffix=sSuffixTmp, delete=False)
                else:
                    oFileName_TMP = tempfile.NamedTemporaryFile(suffix=sSuffixTmp, delete=False)

                try:
                    shutil.copyfileobj(oFileName_UNZIP, oFileName_TMP)
                    oFileName_UNZIP.close()
                    oFileName_TMP.close()

                    sFileName_TMP = oFileName_TMP.name

                except BaseException:

                    Exc.getExc(' =====> WARNING: problems occur in opening ' + sFileName_IN + ' in tmp folder!', 2, 1)

                    oFileName_UNZIP.close()
                    oFileName_TMP.close()

                    if os.path.exists(oFileName_TMP.name):
                        os.remove(oFileName_TMP.name)
                    sFileName_TMP = None
            else:
                sFileName_TMP = sFileName_IN

            if sFileName_TMP is not None:
                oFileTime_LIST.append(sFileTime_IN)
                oFileName_LIST.append(sFileName_TMP)

    # Check file handle(s) availability
    if oFileName_LIST:

        # Preprocess file(s) to control variable(s) and time(s)
        oFileVarsSource_EXPECTED = []
        oFileTime_EXPECTED = []
        for sFileTime_LIST, sFileName_LIST in zip(oFileTime_LIST, oFileName_LIST):

            with xr.open_dataset(sFileName_LIST) as oDSet:
                oFileVars_LIST = list(oDSet.data_vars)

            oFileVarsSource_EXPECTED.extend(oElem for oElem in oFileVars_LIST if oElem not in oFileVarsSource_EXPECTED)
            oFileTime_EXPECTED.append(sFileTime_LIST)

        # Open data filename(s)
        if oFileName_LIST.__len__() > 1:
            oFileData = xr.open_mfdataset(oFileName_LIST, preprocess=fixVar2D, concat_dim='time')
        else:
            oFileData = xr.open_dataset(oFileName_LIST[0])
            oFileData = removeVar2D(oFileData, oFileVarsSource_EXPECTED, oFileVarsSource_SELECTED)

        # Check time information dimension
        if 'time' not in list(oFileData.dims):
            oFileData = oFileData.expand_dims('time')
            oFileData = oFileData.assign_coords(time=pd.to_datetime(oFileTime_EXPECTED))
            oFileData.coords['time'] = oFileData.coords['time'].astype('datetime64[ns]')
            oFileData.coords['time'].attrs['calendar'] = 'gregorian'
        # Check time information format
        if not isinstance(oFileData['time'], datetime.datetime):
            oFileData = oFileData.assign_coords(time=pd.to_datetime(oFileTime_EXPECTED))
            oFileData.coords['time'] = oFileData.coords['time'].astype('datetime64[ns]')
            oFileData.coords['time'].attrs['calendar'] = 'gregorian'

        # Set fill value for crs field
        if "crs" in list(oFileData.variables.keys()):
            oFileData['crs'].attrs['_FillValue'] = -9999

        oFileVarsSource_SELECTED_ID = None
        if oFileVarsSource_SELECTED_ID is None:
            oFileVarsSource_SELECTED_ID = deepcopy(oFileVarsSource_SELECTED)

        oFileVarsOutcome_SELECTED_ID = None
        if oFileVarsOutcome_SELECTED_ID is None:
            oFileVarsOutcome_SELECTED_ID = deepcopy(oFileVarsOutcome_SELECTED)

        # Set values for Terrain field
        if oDataGeo is not None:
            if 'Terrain' not in list(oFileData.variables):
                oFileData = addVar2D(oFileData,
                                     oDataGeo.a2dGeoData, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                     sVarName='Terrain')
            if 'Longitude' not in list(oFileData.variables):
                oFileData = addVar2D(oFileData,
                                     oDataGeo.a2dGeoX, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                     sVarName='Longitude')
            if 'Latitude' not in list(oFileData.variables):
                oFileData = addVar2D(oFileData,
                                     oDataGeo.a2dGeoY, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                     sVarName='Latitude')
        # Change variables name
        oFileData_IN = oFileData
        oFileData_IN_COORDS = oFileData_IN.coords

        oFileData_OUT = xr.Dataset(coords=oFileData_IN_COORDS)
        for sVarName_IN, sVarName_OUT in zip(oFileVarsSource_SELECTED, oFileVarsOutcome_SELECTED):
            if sVarName_IN in list(oFileData.variables.keys()):
                if (sVarName_IN in oFileVarsSource_SELECTED_ID) and (
                        sVarName_OUT in oFileVarsOutcome_SELECTED_ID):

                    oVarData_IN = oFileData_IN[sVarName_IN]
                    oVarData_IN_DIMS = oVarData_IN.dims
                    oVarData_IN_COORDS = oVarData_IN.coords
                    oVarDArray = xr.DataArray(oVarData_IN, dims=oVarData_IN_DIMS, coords=oVarData_IN_COORDS)

                    oFileData_OUT[sVarName_OUT] = oVarDArray

    else:
        oFileData_OUT = None

    # Check dimension(s) name
    if oFileData_OUT is not None:

        oFileDims_GET = list(oFileData_OUT.dims)
        oFileDims_CHECK_KEYS = list(oFileDims_LUT.keys())
        oFileDims_CHECK_VALS = list(oFileDims_LUT.values())

        for sFileDim_GET in oFileDims_GET:

            if sFileDim_GET not in oFileDims_CHECK_VALS:
                Exc.getExc(' =====> WARNING: name of dataset dim ' + sFileDim_GET +
                           ' not in default convention ' + str(oFileDims_CHECK_VALS) + '!', 2, 1)
                bFileDim_UPD = True
            else:
                bFileDim_UPD = False

            if sFileDim_GET in oFileDims_CHECK_KEYS:
                sFileDim_CHECK = oFileDims_LUT[sFileDim_GET]
                if sFileDim_GET != sFileDim_CHECK:
                    oFileData_OUT = oFileData_OUT.rename({sFileDim_GET: sFileDim_CHECK})
                    Exc.getExc(' =====> WARNING: name of dataset dim ' + sFileDim_GET +
                               ' is renamed in ' + sFileDim_CHECK + ' according with the default convention!', 2, 1)
            else:
                if bFileDim_UPD:
                    Exc.getExc(' =====> WARNING: name of dataset dim ' + sFileDim_GET +
                               ' not in default convention!', 2, 1)

    return oFileData_OUT, oFileName_LIST

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to fix variable 2D for parallel merging
def fixVar2D(oDSet):

    # List of expected and selected variable(s)
    oVarList_EXP = oFileVarsSource_EXPECTED
    oVarList_SEL = oFileVarsSource_SELECTED

    # Check and fill missing variable(s)
    for sVarName in oVarList_EXP:
        if sVarName not in oDSet.data_vars:
            a2dVarData = np.zeros([int(oDSet.nrows), int(oDSet.ncols)], dtype=np.float32)
            a2dVarData[:, :] = -9999.0

            a2oVarData = da.from_array(a2dVarData, chunks=(int(oDSet.nrows), int(oDSet.ncols)))

            oVarData = xr.DataArray(a2oVarData, dims=list(oDSet.dims), coords=oDSet.coords)
            oDSet[sVarName] = oVarData

    oDSet = removeVar2D(oDSet, list(oDSet.variables.keys()), oVarList_SEL)

    return oDSet
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to remove variable 2d from dataset
def removeVar2D(oDSet, oVarList_EXP, oVarList_SEL):
    # Drop variables unselected
    for sVarName_EXP in oVarList_EXP:
        if sVarName_EXP not in oVarList_SEL:
            oDSet = oDSet.drop(sVarName_EXP)

    return oDSet
# -------------------------------------------------------------------------------------
