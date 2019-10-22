"""
Class Features

Name:          drv_configuration_algorithm
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import json

from src.common.settings.lib_settings import selectDataSettings, setPathRoot, setPathFile
from src.common.default.lib_default_args import sLoggerName
from src.common.default.lib_default_tags import oVarTags as oVarTags_Default

from src.common.utils.lib_utils_op_list import convertList2Dict
from src.common.utils.lib_utils_op_dict import lookupDictKey, mergeDict

# Log
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Variable(s) definition
oFileKeyDef = dict(sKey1='folder', sKey2='filename')
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
class DataObject(dict):
    pass
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class Tags
class DataAlgorithm:

    # -------------------------------------------------------------------------------------
    # Global Variable(s)
    oDataSettings = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, sFileSettings):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.sFileSettings = sFileSettings
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set data tags
    def getDataSettings(self):

        # Get data settings
        sFileSettings = self.sFileSettings
        with open(sFileSettings) as oFileSettings:
            oDataSettings = json.load(oFileSettings)

        # Set root path(s)
        oDataPath = selectDataSettings(oDataSettings, sPathKey='folder')
        setPathRoot(oDataPath)
        # Set file path(s)
        oDataFile = selectDataSettings(oDataSettings, sPathKey='data')
        oDataInfo = findValues(oDataFile, list(oFileKeyDef.values()))
        oDataPath = setPathFile(oDataInfo, oFileKeyDef=oFileKeyDef)

        # Set data mapping(s)
        oDataMapping_Source = findGroups(oDataSettings, ['data', 'dynamic', 'source'])
        oDataMapping_Outcome = findGroups(oDataSettings, ['data', 'dynamic', 'outcome'])
        oDataMapping = mergeDict(oDataMapping_Source, oDataMapping_Outcome)

        # Set data flag(s)
        oDataFlags = selectDataSettings(oDataSettings, sPathKey='flags')
        oDataFlags = convertList2Dict(oDataFlags, var_split={'split': True, 'chunk': 2, 'key': 0})

        # Set colormap path(s)
        oColorMapFile = selectDataSettings(oDataSettings, sPathKey='colormap')
        oColorMapInfo = findValues(oColorMapFile, list(oFileKeyDef.values()))
        oColorMapPath = setPathFile(oColorMapInfo, oFileKeyDef=oFileKeyDef)

        # Filled colormap(s) with a default value
        oColorMapPath = fillColorMap(oColorMapPath, oColorMapInfo)

        return oDataSettings, oDataPath, oDataFlags, oDataMapping, oColorMapPath
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to fill colormap for undefined filename (if a palette is defined)
def fillColorMap(oColorMapPath, oColorMapInfo):
    for sColorMap_KEY, oColorMap_VAL in oColorMapPath.items():
        if oColorMap_VAL is None:
            if sColorMap_KEY in oColorMapInfo:
                oColorMapInfo_KEY = oColorMapInfo[sColorMap_KEY]
                for sColorMapInfo_KEY, sColorMapInfo_VALUE in oColorMapInfo_KEY.items():
                    if sColorMapInfo_VALUE is not None:
                        oColorMapPath[sColorMap_KEY] = sColorMapInfo_VALUE
    return oColorMapPath
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to recursively find value of variable(s)
def findValues(oFile, oValueRef=['folder','filename']):

    oVarDict = {}
    for oVar in oFile:
        if isinstance(oFile, list):
            oVarName = oVar[0]
            oVarField = oVar[1]

        elif isinstance(oFile, dict):
            oVarName = oVar
            oVarField = oFile[oVar]

        if isinstance(oVarField, dict):

            if all(sValue in oVarField for sValue in oValueRef):
                sVarName = oVarName
                oVarDict[sVarName] = oVarField
            else:
                oVarDict_Upd = findValues(oVarField, oValueRef)
                if oVarDict:
                    for sKey, oValue in oVarDict_Upd.items():
                        oVarDict[sKey] = oValue
                else:
                    oVarDict = oVarDict_Upd

    return oVarDict
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to find group of data using a common data tag
def findGroups(oDictData_ALL, oDickKey, sDictGroupKey='group', sDictGroupData='collection'):

    oDictData_SEL = lookupDictKey(oDictData_ALL, *oDickKey)

    oDictData_MAPPING = {}
    for oDictData_STEP in oDictData_SEL.items():
        sDictData_NAME = oDictData_STEP[0]
        sDictData_VALUE = oDictData_STEP[1]

        if sDictGroupKey in sDictData_VALUE.keys():
            if sDictData_VALUE[sDictGroupKey]:
                oDictData_COLLECTION = list(sDictData_VALUE[sDictGroupData].keys())

                oDictData_MAPPING[sDictData_NAME] = oDictData_COLLECTION

        else:
            oDictData_MAPPING[sDictData_NAME] = [sDictData_NAME]

    return oDictData_MAPPING
# -------------------------------------------------------------------------------------
