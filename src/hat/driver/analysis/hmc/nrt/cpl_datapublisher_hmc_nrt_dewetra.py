"""
Library Features:

Name:          cpl_datapublisher_hmc_nrt_dewetra
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190319'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import progressbar
import os
import time

import numpy as np
import pandas as pd

from copy import deepcopy

from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_list import reduceList
from src.common.utils.lib_utils_op_dict import mergeDict

from src.hat.dataset.generic.lib_generic_io_method import readFilePickle

from src.hat.dataset.generic.lib_generic_io_apps import findVarName, findVarTag, createVarName
from src.hat.dataset.generic.lib_generic_io_utils import createVarAttrs, mergeVarAttrs, addVarAttrs, reduceDArray3D

from src.hat.framework.hydrapp.lib_hydrapp_graph_configuration import configVarArgs
import src.hat.framework.hydrapp.lib_hydrapp_graph_ts as libFxTS
import src.hat.framework.hydrapp.lib_hydrapp_graph_gridded as libFxGridded

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Class to publish data analysis
class DataPublisher:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, sAppTag, oAppArgs):

        # Set argument(s)
        self.sAppTag = sAppTag
        self.oVarTime = oAppArgs['time_make']
        self.oVarTimePeriod = oAppArgs['time_period']
        self.oVarDef = oAppArgs['settings']['analysis'][sAppTag]
        self.oVarSource = oAppArgs['file']
        self.oVarMapping = oAppArgs['mapping']
        self.oVarCMap = oAppArgs['cmap']
        self.oVarTags = oAppArgs['tags']

        # Map file(s)
        self.oVarFile, self.oVarBaseName = fileMapping(self.oVarSource, self.oVarMapping, self.oVarTags)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to publish data for selected application
    def publishData(self, oDataInfo, oDataGeo, oDataSection):

        # -------------------------------------------------------------------------------------
        # Get global declaration(s)
        sAppTag = self.sAppTag
        oVarDef = self.oVarDef
        oVarFile = self.oVarFile
        oVarBaseName = self.oVarBaseName
        oVarCMap = self.oVarCMap
        oVarTime_RUN = self.oVarTime
        oVarTime_PERIOD = self.oVarTimePeriod
        oVarTags = self.oVarTags

        # Parser Info
        oVarData_CHECK, oVarData_STATS = infoMapping(oDataInfo, sAppTag)

        # Set progress bar widget(s)
        oVarPBarWidgets = [
            ' ===== Publishing data progress for ' + sAppTag + ' application: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]

        # Store data and registry step(s)
        oVarData_DEF_WS = {}
        oVarRegistry_DEF_WS = {}
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to map information
def infoMapping(oDataInfo, sAppTag):
    oDataINFO_CHECK = None
    oDataINFO_STATS = None
    if oDataInfo.__len__() == 1:
        oDataINFO_CHECK = oDataInfo[sAppTag]
    elif oDataInfo.__len__() == 2:
        for iDataInfo_ID, oDataInfo_STEP in enumerate(oDataInfo):

            oDataInfo_TAG = oDataInfo_STEP[sAppTag]
            if iDataInfo_ID == 0:
                oDataINFO_CHECK = oDataInfo_TAG
            elif iDataInfo_ID == 1:
                oDataINFO_STATS = oDataInfo_TAG
    return oDataINFO_CHECK, oDataINFO_STATS

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to map file
def fileMapping(oVarSource, oVarMapping, oVarTags):
    oVarFile = {}
    oVarBaseName = {}
    for sVarMapping_TAG, oVarMapping_NAMES in oVarMapping.items():
        for sVarMapping_NAME in oVarMapping_NAMES:
            sVarMapping_FILE_RAW = oVarSource[sVarMapping_NAME]
            sVarMapping_FILE_FILLED = defineString(sVarMapping_FILE_RAW, oVarTags)
            oVarFile[sVarMapping_NAME] = sVarMapping_FILE_FILLED
            oVarBaseName[sVarMapping_NAME] = sVarMapping_FILE_RAW
    return oVarFile, oVarBaseName

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to check variable name
def checkVarName(sVarName, oVarValid):
    if sVarName in oVarValid:
        iVarID = oVarValid.index(sVarName)
        return sVarName, iVarID
    else:
        Exc.getExc(' =====> ERROR: variable name is not valid!', 1, 1)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Check variable field
def checkVarField(oVarList, iVarN):
    if isinstance(oVarList, str):
        oVarList = [oVarList]
    if isinstance(oVarList, (int, float)):
        oVarList = [oVarList]

    if oVarList.__len__() != iVarN:
        return [oVarList[0]] * iVarN
    else:
        return oVarList
# -------------------------------------------------------------------------------------