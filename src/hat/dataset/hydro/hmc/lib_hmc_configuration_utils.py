"""
Library Features:

Name:          lib_hmc_configuration_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190125'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import inspect
import glob
import numpy as np
import pandas as pd
import os
from copy import deepcopy
from os.path import join
import datetime

from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import mergeDict, removeDictKey, getDictDeep

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to set dataset time for computing variable
def setDatasetTime_Cmp(sVarTime_TAG, oVarTime_TAGS):

    oVarTime_TAG = None
    for sVarTime_KEY, oVarTime_VALUE in oVarTime_TAGS.items():

        if sVarTime_TAG == sVarTime_KEY:
            oVarTime_TAG = oVarTime_VALUE
            break

    return oVarTime_TAG
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to set variable attribute(s)
def setVarAttributes(oVarData, oAttrsName=None):
    oVarAttrs = {}
    for sAttrKey, oAttrData in oVarData.items():
        if sAttrKey in oAttrsName:
            oVarAttrs[sAttrKey] = oAttrData
    return oVarAttrs
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set dataset tags list
def setDatasetTags_Finder(oVarTime, oVarEnsemble=None):
    oVarTags = {
        '$yyyy': str(oVarTime.year).zfill(4),
        '$mm': str(oVarTime.month).zfill(2),
        '$dd': str(oVarTime.day).zfill(2),
        '$HH': str(oVarTime.hour).zfill(2),
        '$MM': str(oVarTime.minute).zfill(2),
        '$RUNTIME': str(oVarTime.year).zfill(4) + '/' +
                    str(oVarTime.month).zfill(2) + '/' +
                    str(oVarTime.day).zfill(2) + '/' + str(oVarTime.hour).zfill(2),
        '$ensemble': None
    }

    oListTags = []
    if oVarEnsemble is None:
        oVarTags = removeDictKey(oVarTags, ['$ensemble'])
        oListTags = [oVarTags]
    else:
        for sVarEnsemble in oVarEnsemble:
            oListTags.append(mergeDict(oVarTags, {'$ensemble': sVarEnsemble}))

    return oListTags
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define dataset time (starting from machine running time)
def setDatasetTime_Finder(oVarRUN_TIMESTEP, sVarSRC_TYPEDATA, sVarANC_TYPEDATA, sVarSRC_NAME, sVarANC_NAME,
                          oVarFILE_PATHREF, oVarFILE_PATHGENERIC, oVarFILE_MEMORY, oVarTIME_MEMORY,
                          oVarSRC_ENSEMBLE=None,
                          iVarSRC_FREQ='D', iVarSRC_PERIOD=3,
                          iVarANC_FREQ='D', iVarANC_PERIOD=3,
                          sVarSCAN_Freq='H'):

    # Compute time-range for RUN period
    oVarRUN_TIME = pd.date_range(end=oVarRUN_TIMESTEP, periods=iVarSRC_PERIOD, freq=iVarSRC_FREQ)
    oVarRUN_TIME = pd.date_range(start=oVarRUN_TIME[0], end=oVarRUN_TIME[-1], freq=sVarSCAN_Freq)
    oVarRUN_TIME = oVarRUN_TIME.sort_values(return_indexer=False, ascending=False)

    if sVarANC_NAME is not None:
        oDFrame_TYPE = [sVarSRC_TYPEDATA, sVarANC_TYPEDATA]
        oDFrame_COLS = [sVarSRC_NAME, sVarANC_NAME]
    else:
        oDFrame_TYPE = [sVarSRC_TYPEDATA]
        oDFrame_COLS = [sVarSRC_NAME]

    oDFrame_DATA = pd.DataFrame(index=oVarRUN_TIME, columns=oDFrame_COLS)
    oDFrame_DATA.fillna(False)

    # Get generic path(s) of SOURCE and ANCILLARY
    sVarSRC_PATHGENERIC = oVarFILE_PATHGENERIC[sVarSRC_NAME]
    sVarSRC_PATHBASE, sVarSRC_FILEBASE = os.path.split(sVarSRC_PATHGENERIC)

    if sVarANC_NAME is not None:
        sVarANC_PATHGENERIC = oVarFILE_PATHGENERIC[sVarANC_NAME]
        sVarANC_PATHBASE, sVarANC_FILEBASE = os.path.split(sVarANC_PATHGENERIC)

    # Iterate over time-range
    oVarSRC_TIME = {}
    oVarANC_TIME = {}
    for oVarRUN_TIMECHECK in oVarRUN_TIME:

        oVarSRC_TIMECHECK = oVarRUN_TIMECHECK
        oListSRC_TAGS = setDatasetTags_Finder(oVarSRC_TIMECHECK, oVarSRC_ENSEMBLE)

        oVarSRC_TIME[oVarRUN_TIMECHECK] = {}
        for oElemSRC_TAGS in oListSRC_TAGS:

            sVarSRC_PATHCHECK = defineString(sVarSRC_PATHGENERIC, oElemSRC_TAGS)
            oVarSRC_FILECHECK = glob.glob(sVarSRC_PATHCHECK)

            if oVarSRC_FILECHECK:
                if 'data' not in oVarSRC_TIME[oVarRUN_TIMECHECK]:
                    oVarSRC_TIME[oVarRUN_TIMECHECK]['time'] = oVarSRC_TIMECHECK
                    oVarSRC_TIME[oVarRUN_TIMECHECK]['data'] = oVarSRC_FILECHECK
                else:
                    oVarSRC_FILESAVE = oVarSRC_TIME[oVarRUN_TIMECHECK]['data']
                    oVarSRC_FILESAVE.append(oVarSRC_FILECHECK[0])
                    oVarSRC_TIME[oVarRUN_TIMECHECK]['data'] = oVarSRC_FILESAVE

        if not oVarSRC_TIME[oVarRUN_TIMECHECK]:
            oVarSRC_TIME[oVarRUN_TIMECHECK] = None

    for oVarRUN_TIME, oVarSRC_DATA in oVarSRC_TIME.items():
        if oVarSRC_DATA is not None:
            oVarSRC_TIMESTEP = oVarSRC_DATA['time']
            oDFrame_DATA.loc[oVarRUN_TIME, sVarSRC_NAME] = oVarSRC_TIMESTEP

    if sVarANC_NAME is not None:
        oVarANC_TIMEHISTORY = []
        if oVarSRC_TIME:
            for oVarRUN_TIMECHECK, oVarRUN_DATA in oVarSRC_TIME.items():

                oVarANC_TIMERANGE = pd.date_range(start=oVarRUN_TIMECHECK, closed=None,
                                                  periods=iVarANC_PERIOD, freq=iVarANC_FREQ)

                oVarANC_TIMESCAN = pd.date_range(start=oVarANC_TIMERANGE[0], end=oVarANC_TIMERANGE[-1], freq=sVarSCAN_Freq)

                oVarANC_TIME[oVarRUN_TIMECHECK] = {}
                #for oVarANC_TIMECHECK in oVarANC_TIMERANGE:
                for oVarANC_TIMECHECK in oVarANC_TIMESCAN:

                    if oVarANC_TIMECHECK <= oVarRUN_TIMESTEP:

                        if oVarANC_TIMECHECK not in oVarANC_TIMEHISTORY:
                            oVarANC_TIMEHISTORY.append(oVarANC_TIMECHECK)

                            oListANC_TAGS = setDatasetTags_Finder(oVarANC_TIMECHECK, oVarSRC_ENSEMBLE)

                            for oElemANC_TAGS in oListANC_TAGS:

                                sVarANC_PATHCHECK = defineString(sVarANC_PATHGENERIC, oElemANC_TAGS)
                                oVarANC_FILECHECK = glob.glob(sVarANC_PATHCHECK)

                                if oVarANC_FILECHECK:
                                    if 'data' not in oVarANC_TIME[oVarRUN_TIMECHECK]:
                                        oVarANC_TIME[oVarRUN_TIMECHECK]['time'] = oVarANC_TIMECHECK
                                        oVarANC_TIME[oVarRUN_TIMECHECK]['data'] = oVarANC_FILECHECK
                                    else:
                                        oVarANC_FILESAVE = oVarANC_TIME[oVarRUN_TIMECHECK]['data']
                                        oVarANC_FILESAVE.append(oVarANC_FILECHECK[0])
                                        oVarANC_TIME[oVarRUN_TIMECHECK]['data'] = oVarANC_FILESAVE

                if not oVarANC_TIME[oVarRUN_TIMECHECK]:
                    oVarANC_TIME[oVarRUN_TIMECHECK] = None

            for oVarRUN_TIME, oVarANC_DATA in oVarANC_TIME.items():
                if oVarANC_DATA is not None:
                    oVarANC_TIMESTEP = oVarANC_DATA['time']
                    oDFrame_DATA.loc[oVarRUN_TIME, sVarANC_NAME] = oVarANC_TIMESTEP

    # Iteration(s) to find datetime(s) of SRC and ANC dataset(s)
    oDFrame_DATA_REVERSE = oDFrame_DATA[::-1]
    oDict_DATA_SEARCH = None
    oDFrame_DATA_SEARCH = pd.DataFrame(columns=oDFrame_COLS)
    for oDFrame_ROW in oDFrame_DATA_REVERSE.iterrows():
        oVarTIME_ROW = pd.DatetimeIndex([oDFrame_ROW[0]])
        oVarDATA_ROW = list(oDFrame_ROW[1].values)

        if oDict_DATA_SEARCH is None:
            oDict_DATA_SEARCH = dict.fromkeys(oDFrame_COLS, None)

        for sDFrame_COLS, sDFrame_TYPE, oDFrame_VALUE in zip(oDFrame_COLS, oDFrame_TYPE, oVarDATA_ROW):

            if isinstance(oDFrame_VALUE, (datetime.datetime, np.datetime64, datetime.date)):
                if not pd.isnull(oDFrame_VALUE):
                    oDict_DATA_SEARCH[sDFrame_COLS] = oDFrame_VALUE

                if sDFrame_TYPE == 'result':
                    oDict_DATA_VALUES = list(oDict_DATA_SEARCH.values())
                    for sElem_DATA_COLS, oElem_DATA_VALUES in zip(oDFrame_COLS, oDict_DATA_VALUES):
                        if oElem_DATA_VALUES is not None:
                            if not pd.isnull(oDFrame_VALUE):
                                if oDFrame_VALUE < oElem_DATA_VALUES:
                                    oDict_DATA_SEARCH[sElem_DATA_COLS] = None

                if sDFrame_TYPE == 'observed':
                    oDict_DATA_VALUES = list(oDict_DATA_SEARCH.values())
                    for sElem_DATA_COLS, oElem_DATA_VALUES in zip(oDFrame_COLS, oDict_DATA_VALUES):
                        if oElem_DATA_VALUES is not None:
                            if not pd.isnull(oDFrame_VALUE):
                                if oDFrame_VALUE > oElem_DATA_VALUES:
                                    oDict_DATA_SEARCH[sElem_DATA_COLS] = None

                if sDFrame_TYPE == 'forecast':
                    oDict_DATA_VALUES = list(oDict_DATA_SEARCH.values())
                    for sElem_DATA_COLS, oElem_DATA_VALUES in zip(oDFrame_COLS, oDict_DATA_VALUES):
                        if oElem_DATA_VALUES is not None:
                            if not pd.isnull(oDFrame_VALUE):
                                if oDFrame_VALUE > oElem_DATA_VALUES:
                                    oDict_DATA_SEARCH[sElem_DATA_COLS] = None

        if None not in oDict_DATA_SEARCH.values():
            oDFrame_DATA_SEARCH = oDFrame_DATA_SEARCH.append(
                pd.DataFrame(oDict_DATA_SEARCH, index=oVarTIME_ROW))
            oDict_DATA_SEARCH = None
            # break

    # Append value for last part to get also not completed dictionary
    if oDict_DATA_SEARCH is not None:
        if any(oElem is not None for oElem in oDict_DATA_SEARCH.values()):
            oDFrame_DATA_SEARCH = oDFrame_DATA_SEARCH.append(
                pd.DataFrame(oDict_DATA_SEARCH, index=oVarTIME_ROW))

    # Delete rows with all nan(s)
    oDFrame_DATA_ALL = oDFrame_DATA_SEARCH.dropna(axis=0, how='all')
    oDFrame_DATA_FINITE = oDFrame_DATA_SEARCH.dropna(axis=0, how='any')

    if not oDFrame_DATA_FINITE.empty:
        oDFrame_DATA_SELECT = oDFrame_DATA_FINITE
    else:
        Exc.getExc(' =====> WARNING: source and/or ancillary columns is/are null!', 2, 1)
        oDFrame_DATA_SELECT = oDFrame_DATA_ALL

    # Initialize time dictionary (if none is actual value)
    if oVarTIME_MEMORY is None:
        oVarTIME_MEMORY = {}

    # Iterate over time select
    for oDFrame_ROW_SELECT in oDFrame_DATA_SELECT.iterrows():

        # Iterate over columns of SRC and ANC name(s)
        for sDFrame_COLS, sDFrame_TYPE in zip(oDFrame_COLS, oDFrame_TYPE):

            # Check data availability
            if oDFrame_ROW_SELECT:

                # Get selected time
                oVarTIME_ROW_SELECT = oDFrame_ROW_SELECT[1][sDFrame_COLS]

                if sDFrame_COLS in list(oVarTIME_MEMORY.keys()):
                    oVarFILE_TIMESAVED = oVarTIME_MEMORY[sDFrame_COLS]
                    # oVarFILE_TIMEACTUAL = pd.Timestamp(oDFrame_ROW_SELECT[sDFrame_COLS].values[0])
                    oVarFILE_TIMEACTUAL = oVarTIME_ROW_SELECT

                    if oVarFILE_TIMEACTUAL > oVarFILE_TIMESAVED:
                        oVarTIME_MEMORY[sDFrame_COLS] = None
                        oVarFILE_MEMORY[sDFrame_COLS] = False

                # Check to update path(s) only one time
                if not oVarFILE_MEMORY[sDFrame_COLS]:
                    sVarFILE_PATHSELECT = oVarFILE_PATHGENERIC[sDFrame_COLS]
                    # oVarFILE_TIMESELECT = pd.Timestamp(oDFrame_DATA_SELECT[sDFrame_COLS].values[0])
                    oVarFILE_TIMESELECT = oVarTIME_ROW_SELECT

                    oListFILE_TAGS = setDatasetTags_Finder(oVarFILE_TIMESELECT)[0]
                    sVarFILE_PATHBASE, sVarFILE_FILEBASE = os.path.split(sVarFILE_PATHSELECT)

                    if sDFrame_TYPE == 'observed':
                        sVarFILE_PATHREF = join(sVarFILE_PATHBASE, sVarFILE_FILEBASE)
                    elif (sDFrame_TYPE == 'forecast') or (sDFrame_TYPE == 'result'):
                        sVarFILE_PATHDEF = defineString(sVarFILE_PATHBASE, oListFILE_TAGS)
                        sVarFILE_PATHREF = join(sVarFILE_PATHDEF, sVarFILE_FILEBASE)

                    oVarTIME_MEMORY[sDFrame_COLS] = oVarFILE_TIMESELECT
                    oVarFILE_PATHREF[sDFrame_COLS] = sVarFILE_PATHREF
                    oVarFILE_MEMORY[sDFrame_COLS] = True

            else:
                Exc.getExc(' =====> WARNING: dataframe for ' + sDFrame_COLS + ' variable is null!', 2, 1)
                oVarTIME_MEMORY[sDFrame_COLS] = oVarRUN_TIMESTEP
                oVarFILE_MEMORY[sDFrame_COLS] = True

    return oVarTIME_MEMORY, oVarFILE_PATHREF, oVarFILE_MEMORY
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set variable settings
def setVarSettings(sVarDims, sVarTypeData, oVarArg, oVarTime_PERIOD_OBS, oVarTime_PERIOD_FOR):

    # Define complete period
    oVarTime_PERIOD_TOT = oVarTime_PERIOD_OBS.union(oVarTime_PERIOD_FOR)
    iVarTime_PERIOD_TOT = oVarTime_PERIOD_TOT.__len__()
    sVarTime_FREQ_TOT = pd.infer_freq(oVarTime_PERIOD_TOT)

    # Get variable settings using dimensions and type
    oVarSettings = None
    if oVarArg is not None:
        if sVarTypeData in oVarArg[sVarDims]:
            oVarSettings = oVarArg[sVarDims][sVarTypeData]
        else:
            oVarSettings = None
    if oVarSettings is None:
        if sVarTypeData == 'observed':
            oVarSettings = dict(data_period=oVarTime_PERIOD_OBS.__len__(),
                                data_frequency=pd.infer_freq(oVarTime_PERIOD_OBS))
        elif sVarTypeData == 'forecast':
            oVarSettings = dict(data_period=oVarTime_PERIOD_FOR.__len__(),
                                data_frequency=pd.infer_freq(oVarTime_PERIOD_FOR))
        elif sVarTypeData == 'result':

            oVarTime_PERIOD_RESULT = oVarTime_PERIOD_TOT
            oVarSettings = dict(data_period=oVarTime_PERIOD_RESULT.__len__(),
                                data_frequency=pd.infer_freq(oVarTime_PERIOD_RESULT))
        else:
            oVarSettings = None
            Exc.getExc(' =====> ERROR: set variable settings failed! Check your variable definition!', 1, 1)

    if sVarTypeData == 'result':
        if 'data_period' in oVarSettings:

            if isinstance(oVarSettings['data_period'], list):
                iVarTime_PERIOD_SET = oVarSettings['data_period'][0]
            else:
                iVarTime_PERIOD_SET = oVarSettings['data_period']

            if iVarTime_PERIOD_SET < iVarTime_PERIOD_TOT:
                iVarTime_PERIOD_SEL = iVarTime_PERIOD_TOT
                sVarTime_FREQ_SEL = sVarTime_FREQ_TOT
            else:

                if isinstance(oVarSettings['data_period'], list):
                    iVarTime_PERIOD_SEL = oVarSettings['data_period'][0]
                else:
                    iVarTime_PERIOD_SEL = oVarSettings['data_period']

                if isinstance(oVarSettings['data_frequency'], list):
                    sVarTime_FREQ_SEL = oVarSettings['data_frequency'][0]
                else:
                    sVarTime_FREQ_SEL = oVarSettings['data_frequency']
        else:
            iVarTime_PERIOD_SEL = iVarTime_PERIOD_TOT
            sVarTime_FREQ_SEL = sVarTime_FREQ_TOT

        if not isinstance(iVarTime_PERIOD_SEL, list):
            iVarTime_PERIOD_SEL = [iVarTime_PERIOD_SEL]
        if not isinstance(sVarTime_FREQ_SEL, list):
            sVarTime_FREQ_SEL = [sVarTime_FREQ_SEL]

        oVarSettings['data_period'] = iVarTime_PERIOD_SEL
        oVarSettings['data_frequency'] = sVarTime_FREQ_SEL

    return oVarSettings

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set chunk(s) for each variable
def setVarChunk(oVarTime_RUN, oVarTime_DATASET, oVarTime_PERIOD, oVarIdx_PERIOD, sVarType, oVarSettings):

    oVarTime_RUN_SELECTED = None
    oVarTime_REF_SELECTED = None
    oVarIdx_REF_SELECTED = None

    oVarTime_LIST = []
    for sVarTime_LIST in oVarTime_PERIOD:
        oVarTime_LIST.append(sVarTime_LIST)

    if sVarType == "observed":

        iVarTime_IDX_OBS = oVarTime_PERIOD.get_loc(oVarTime_RUN, method="nearest") + 1

        oVarTime_RUN_SELECTED = oVarTime_LIST[0:iVarTime_IDX_OBS]
        oVarTime_REF_SELECTED = oVarTime_LIST[0:iVarTime_IDX_OBS]
        oVarIdx_REF_SELECTED = oVarIdx_PERIOD[0:iVarTime_IDX_OBS]

        oVarTime_RUN_RANGE = None  # To be defined

    elif sVarType == 'forecast':
        oVarFreq = oVarSettings['model_frequency']
        oVarPeriod = oVarSettings['model_period']

        if isinstance(oVarFreq, list):
            sVarFreq = oVarFreq[0]
        else:
            sVarFreq = oVarFreq
        if isinstance(oVarPeriod, list):
            iVarPeriod = oVarPeriod[0]
        else:
            iVarPeriod = oVarPeriod

        oTimeRange = pd.date_range(end=oVarTime_RUN, periods=iVarPeriod, freq=sVarFreq)
        oTimeRange = oTimeRange.floor(sVarFreq)

        # Condition to consider time run and forecast data-set in different days
        if oVarTime_DATASET in oTimeRange:
            oTimeDset = pd.DatetimeIndex([oVarTime_DATASET])
            oTimeIntersection = oTimeRange.intersection(oTimeDset)

            if not oTimeIntersection.empty:
                oTimeRange = oTimeIntersection

        oVarTime_SEL = oTimeRange.sort_values(return_indexer=False, ascending=False)[0]

        iVarTime_IDX_FOR = oVarTime_PERIOD.get_loc(oVarTime_SEL, method="nearest") + 1

        oVarTime_RUN_SELECTED = oVarTime_PERIOD[iVarTime_IDX_FOR:]
        oVarTime_REF_SELECTED = [oVarTime_SEL] * oVarTime_LIST[iVarTime_IDX_FOR:].__len__()
        oVarIdx_REF_SELECTED = oVarIdx_PERIOD[iVarTime_IDX_FOR:]

        oVarTime_RUN_RANGE = oTimeRange

    elif sVarType == 'result':

        oVarTime_RUN_SELECTED = oVarTime_LIST
        oVarTime_REF_SELECTED = oVarTime_LIST
        oVarIdx_REF_SELECTED = oVarIdx_PERIOD

        oVarTime_RUN_RANGE = None # To be defined

    return oVarTime_RUN_SELECTED, oVarTime_REF_SELECTED, oVarIdx_REF_SELECTED, oVarTime_RUN_RANGE
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define time-steps variable for each datetime
def setDatasetTime_Steps(sVarType, oVarSettings, oVarTime, *argv):

    sArgVar_Per = argv[0][0]
    sArgVar_Freq = argv[0][1]

    if (sArgVar_Per in oVarSettings) and (sArgVar_Freq in oVarSettings):

        oArgVar_Per = oVarSettings[sArgVar_Per]
        oArgVar_Freq = oVarSettings[sArgVar_Freq]

        if isinstance(oArgVar_Per, list):
            iArgVar_Per_Sel = oArgVar_Per[0]
        else:
            iArgVar_Per_Sel = oArgVar_Per

        if isinstance(oArgVar_Freq, list):
            sArgVar_Freq_Sel = oArgVar_Freq[0]
        else:
            sArgVar_Freq_Sel = oArgVar_Freq

        iVarData_Per = int(iArgVar_Per_Sel)
        sVarData_Freq = sArgVar_Freq_Sel
    else:
        iVarData_Per = None
        sVarData_Freq = None

    oVarTime_LIST = []
    for sVarTime in oVarTime:

        if (iVarData_Per is None) and (sVarData_Freq is None):
            oVarTime_SEL = [sVarTime]
            oVarTime_LIST.append(oVarTime_SEL)
        else:

            if sVarType == 'forecast':
                oVarTime = pd.date_range(start=sVarTime, periods=2, freq=sVarData_Freq)[1]
            elif sVarType == 'observed':
                oVarTime = pd.to_datetime(sVarTime)
            elif sVarType == 'result':
                oVarTime = pd.to_datetime(sVarTime)
            oVarTime_SEL = pd.date_range(start=oVarTime, periods=iVarData_Per, freq=sVarData_Freq)
            oVarTime_LIST.append(oVarTime_SEL)

    return oVarTime_LIST
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set ensemble for each variable
def setVarEnsemble(sVarTypeData, oVarSettings, *argv):

    if sVarTypeData == 'forecast' or sVarTypeData == 'result':

        sArgEns_N = argv[0][0]
        sArgEns_Format = argv[0][1]

        if oVarSettings is not None:
            if (sArgEns_N in oVarSettings) and (sArgEns_Format in oVarSettings):

                if isinstance(oVarSettings[sArgEns_N], list):
                    iVarEns_SEL = oVarSettings[sArgEns_N][0]
                else:
                    iVarEns_SEL = oVarSettings[sArgEns_N]
                iVarEns_N = int(iVarEns_SEL)

                if isinstance(oVarSettings[sArgEns_N], list):
                    sVarEns_Format = oVarSettings[sArgEns_Format][0]
                else:
                    sVarEns_Format = oVarSettings[sArgEns_Format]

                if iVarEns_N > 0:
                    oVarEns = [sVarEns_Format.format(iVarEns) for iVarEns in range(1, iVarEns_N + 1)]
                else:
                    oVarEns = None
            else:
                oVarEns = None
        else:
            oVarEns = None
    else:
        oVarEns = None

    return oVarEns
# -------------------------------------------------------------------------------------
