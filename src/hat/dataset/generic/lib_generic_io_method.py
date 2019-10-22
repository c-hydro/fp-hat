"""
Library Features:

Name:          lib_generic_io_method
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190211'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import os
import pickle
import _pickle as cPickle

import netCDF4

import numpy as np
import xarray as xr
import pandas as pd
from copy import deepcopy

from src.hat.dataset.generic.lib_generic_io_utils import createVar2D

from src.common.default.lib_default_args import sLoggerName, sTimeFormat
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################

# -------------------------------------------------------------------------------------
# Set environmental variable(s)
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'
# Set dictionary of valid encoding attribute(s)
oVarDecoding_Valid = ['_FillValue', 'ScaleFactor']
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write data in netcdf4 file
def writeFileNC4(sVarFileName, oVarData, oVarAttr=None, sVarGroup=None, sVarMode='w', oVarEngine='h5netcdf',
                 iVarCompression=0):

    oDataEncoded = dict(zlib=True, complevel=iVarCompression)

    oDataEncoding = {}
    for sVarName in oVarData.data_vars:
        
        if isinstance(sVarName, bytes):
            sVarName_UPD = sVarName.decode("utf-8") 
            oVarData = oVarData.rename({sVarName: sVarName_UPD})
            sVarName = sVarName_UPD
            Exc.getExc(' =====> WARNING: in writing netcdf file variable ' + sVarName + ' was in bytes format!', 2, 1)

        oVarData_VAR = oVarData[sVarName]
        if len(oVarData_VAR.dims) > 0:
            oDataEncoding[sVarName] = deepcopy(oDataEncoded)

        if oVarAttr is not None:
            if sVarName in oVarAttr:
                oVarAttr_VAR = oVarAttr[sVarName]
                for sAttrKey, oAttrValue in oVarAttr_VAR.items():

                    if oAttrValue is None:
                        oAttrValue = 'NA'
                        Exc.getExc(' =====> WARNING: in writing netcdf file attribute ' +
                                   sAttrKey + ' is set to None! Default saved value will be NA! Check your data!', 2, 1)

                    if isinstance(oAttrValue, pd.Timestamp):
                        oAttrValue = oAttrValue.strftime(sTimeFormat)

                    if sAttrKey in oVarDecoding_Valid:
                        if sAttrKey == 'ScaleFactor':
                            oDataEncoding[sVarName]['scale_factor'] = oAttrValue
                        else:
                            oDataEncoding[sVarName][sAttrKey] = oAttrValue
                    else:
                        if sAttrKey == 'Valid_range':
                            sAttrKey, oAttrValue = encodeAttrValidRange(oAttrValue)
                        oVarData[sVarName].attrs[sAttrKey] = oAttrValue

    if 'time' in list(oVarData.coords):
        oDataEncoding['time'] = {'calendar': 'gregorian'}
    else:
        Exc.getExc(' =====> WARNING: in writing netcdf file time coordinate is undefined!', 2, 1)
    
    if sVarGroup is not None:
        try:
            oVarData.to_netcdf(path=sVarFileName, format='NETCDF4', mode=sVarMode,
                               group=sVarGroup, engine=oVarEngine, encoding=oDataEncoding)
        except IOError:
            Exc.getExc(' =====> ERROR: in writing netcdf file ' + sVarFileName + ' error(s) occurred!', 1, 1)
    else:
        try:
            oVarData.to_netcdf(path=sVarFileName, format='NETCDF4', mode=sVarMode,
                               engine=oVarEngine, encoding=oDataEncoding)
        except IOError:
            Exc.getExc(' =====> ERROR: in writing netcdf file ' + sVarFileName + ' error(s) occurred!', 1, 1)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read buffer file in netcdf4 format
def readFileNC4(sVarFileName, oVarGroup=None, oVarEngine='h5netcdf'):

    if oVarGroup is not None:
        if isinstance(oVarGroup, str):
            oVarGroup = [oVarGroup]
        oVarData = {}
        for sVarGroup in oVarGroup:

            try:
                with xr.open_dataset(sVarFileName, group=sVarGroup, engine=oVarEngine) as oDSet:
                    oVarData[sVarGroup] = oDSet.load()
                    oDSet.close()
            except BaseException:

                if os.path.exists(sVarFileName):
                    with netCDF4.Dataset(sVarFileName) as oDSet:
                        if hasattr(oDSet, 'groups'):
                            oFileGroups = list(getattr(oDSet, 'groups'))
                        else:
                            oFileGroups = None
                else:
                    oFileGroups = None

                if oFileGroups is None:
                    Exc.getExc(' =====> WARNING: in reading netcdf file ' + sVarFileName + ' error(s) occurred!', 2, 1)
                else:
                    if sVarGroup not in oFileGroups:
                        Exc.getExc(' =====> WARNING: in reading netcdf file ' + sVarFileName +
                                   ' group ' + sVarGroup + ' is not already available in file!',
                                   2, 1)
                    else:
                        Exc.getExc(' =====> WARNING: in reading netcdf file ' + sVarFileName +
                                   ' group ' + sVarGroup + ' is available in file! Error(s) in handling data occurred!',
                                   2, 1)

                oVarData[sVarGroup] = None
    else:
        try:
            with xr.open_dataset(sVarFileName, engine=oVarEngine) as oDSet:
                oVarData = oDSet.load()
                oDSet.close()
        except BaseException:
            Exc.getExc(' =====> WARNING: in reading netcdf file ' + sVarFileName + ' error(s) occurred!', 2, 1)
            oVarData = None

    return oVarData
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to correctly encode valid_range attributes
def encodeAttrValidRange(oAttrData_IN):
    sAttrName_OUT = None
    oAttrData_OUT = None
    if isinstance(oAttrData_IN, list):
        oAttrData_VMin = oAttrData_IN[0]
        oAttrData_VMax = oAttrData_IN[1]
        if (oAttrData_VMin is None) or (oAttrData_VMax is None):
            if oAttrData_VMin is None:
                sAttrName_OUT = 'Valid_max'
                oAttrData_OUT = np.float32(oAttrData_VMax)
            elif oAttrData_VMax is None:
                sAttrName_OUT = 'Valid_min'
                oAttrData_OUT = np.float32(oAttrData_VMin)
        elif (oAttrData_VMin is not None) and (oAttrData_VMax is not None):
            sAttrName_OUT = 'Valid_range'
            oAttrData_OUT = np.asarray(oAttrData_IN, dtype=np.float32)
        elif (oAttrData_VMin is None) and (oAttrData_VMax is None):
            sAttrName_OUT = None
            oAttrData_OUT = None
    else:
        sAttrName_OUT = None
        oAttrData_OUT = None

    return sAttrName_OUT, oAttrData_OUT
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write pickle file
def writeFilePickle(sFileName, oFileData, oFileProtocol=-1):
    with open(sFileName, 'wb') as oFileHandle:
        pickle.dump(oFileData, oFileHandle, protocol=oFileProtocol)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to append pickle file
def appendFilePickle(sFileName, oFileData, sFileKey=None, oFileProtocol=-1):
    with open(sFileName, 'rb') as oFileHandle:
        oFileData_TMP = pickle.load(oFileHandle)

    oFileDSet_STORE_UPD = {}
    if isinstance(oFileData, dict) and isinstance(oFileData_TMP, dict):
        oFileData_STORED_ALL = oFileData_TMP.copy()

        if sFileKey in oFileData_STORED_ALL:
            oFileDSet_STORED_VAR = oFileData_STORED_ALL[sFileKey]
            oFileDSet = oFileData[sFileKey]

            try:
                oFileDSet_STORE_MERGE = oFileDSet_STORED_VAR.merge(oFileDSet)
                oFileDSet_STORE_UPD[sFileKey] = oFileDSet_STORE_MERGE
            except BaseException:

                Exc.getExc(' =====> WARNING: issue in merging datasets! Try to correct Longitude/Latitude coords!', 2, 1)

                for sVarName in list(oFileDSet.data_vars):
                    a3dVarData = oFileDSet[sVarName].values
                    oVarTime = pd.to_datetime(oFileDSet['time'].values)
                    a2dVarGeoY = oFileDSet_STORED_VAR['Latitude'].values
                    a2dVarGeoX = oFileDSet_STORED_VAR['Longitude'].values

                    oVarAttributes = oFileDSet[sVarName].attrs
                    oVarEncoding = oFileDSet[sVarName].encoding

                    oFileDSet_CORRECTED = xr.Dataset(
                        {sVarName: (['time', 'south_north', 'west_east'], a3dVarData)},
                        attrs=oVarAttributes,
                        coords={'Latitude': (['south_north', 'west_east'], a2dVarGeoY),
                                'Longitude': (['south_north', 'west_east'], a2dVarGeoX),
                                'time': oVarTime})
                    oFileDSet_CORRECTED = oFileDSet_STORED_VAR.merge(oFileDSet_CORRECTED)
                    oFileDSet_CORRECTED[sVarName].attrs = oVarAttributes
                    oFileDSet_CORRECTED[sVarName].encoding = oVarEncoding

                oFileDSet_STORE_UPD[sFileKey] = oFileDSet_CORRECTED

        else:
            oFileDSet = oFileData[sFileKey]
            oFileDSet_STORE_UPD[sFileKey] = {}
            oFileDSet_STORE_UPD[sFileKey] = oFileDSet

    with open(sFileName, 'wb') as oFileHandle:
        pickle.dump(oFileDSet_STORE_UPD, oFileHandle, protocol=oFileProtocol)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read pickle file
def readFilePickle(sFileName):

    try:
        with open(sFileName, 'rb') as oFileHandle:
            oFileData = pickle.load(oFileHandle)
    except BaseException:
        #with open(sFileName, 'rb') as oFileHandle:
        oFileData = pd.read_pickle(sFileName)
        Exc.getExc(' =====> WARNING: pickle file was created using another version of pandas library!', 2, 1)

    return oFileData
# -------------------------------------------------------------------------------------
