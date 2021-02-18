"""
Library Features:

Name:          drv_datamanager_hmc_nrt
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190508'
Version:       '1.5.0'
"""
#################################################################################
# Library
import logging
import progressbar
import glob
import os

import pandas as pd
import xarray as xr

from os import remove, listdir, rmdir
from os.path import exists, isfile, split
from copy import deepcopy
from numpy import full, isnan, where

from src.common.default.lib_default_args import sPathDelimiter as sPathDelimiter_Default

from src.common.utils.lib_utils_op_system import createFolderByFile, deleteFileName
from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import mergeDict, lookupDictKey, setDictValue, getDictDeep
from src.common.utils.lib_utils_op_list import countListElemFreq, reduceList
from src.common.utils.lib_utils_apps_zip import removeExtZip

from src.hat.dataset.hydro.hmc.lib_hmc_configuration_utils import setVarSettings, setVarAttributes, \
    setVarChunk, setVarEnsemble, setDatasetTime_Steps, setDatasetTime_Finder, setDatasetTime_Cmp

import src.hat.dataset.hydro.hmc.lib_hmc_data_gridded as oLibGridded
import src.hat.dataset.hydro.hmc.lib_hmc_data_point as oLibPoint
import src.hat.dataset.hydro.hmc.lib_hmc_method_cmp_ts as oLibCmpTS
import src.hat.dataset.hydro.hmc.lib_hmc_method_cmp_gridded as oLibCmpGridded

from src.hat.dataset.generic.lib_generic_configuration_utils import configVarFx
from src.hat.dataset.generic.lib_generic_io_method import writeFileNC4, readFileNC4

from src.common.driver.dataset.drv_data_io_zip import Drv_Data_Zip

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#################################################################################

# -------------------------------------------------------------------------------------
# Set environmental variable(s)
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm valid key(s)
oVarArgs_Valid = ["ensemble_n", "ensemble_format", "data_period", "data_frequency", "column_id"]
oVarSource_TypeData_Valid = ["observed", "forecast", "result", "analysis"]
oVarSource_TypeExperiment_Valid = ["deterministic", "probabilistic"]
oVarSourcePoint_Valid = ['OUTLET_NAME', 'OUTLET_FILE_ANCILLARY', 'ID']
oVarAttributes_Valid = ['units', 'ScaleFactor', 'Missing_value', 'Valid_range', '_FillValue',
                        'time_dataset', 'time_run']
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to clean data analysis
class DataAnalysisCleaner:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.a1oFile = kwargs['file']
        self.a1bFlag = kwargs['flag']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean selected file(s)
    def cleanDataAnalysis(self):

        if isinstance(self.a1bFlag, bool):
            self.a1bFlag = [self.a1bFlag]
        if isinstance(self.a1oFile, str):
            self.a1oFile = [self.a1oFile]

        if self.a1bFlag.__len__() < self.a1oFile.__len__():
            self.a1bFlag = full(self.a1oFile.__len__(),  self.a1bFlag[0], dtype=bool)

        for bFlag, oFile in zip(self.a1bFlag, self.a1oFile):
            if isinstance(oFile, str):
                oFile = [oFile]

            for sFile in oFile:
                if sPathDelimiter_Default in sFile:
                    sFileRoot, sFileNoTag = sFile.split(sPathDelimiter_Default)
                    a1oFileSelect = glob.glob(sFileRoot + '*')
                else:
                    a1oFileSelect = [sFile]

                for sFileSelect in a1oFileSelect:
                    if exists(sFileSelect):
                        if isfile(sFileSelect):
                            if bFlag:
                                remove(sFileSelect)
                    sPathRest = None
                    sPathRef = sFileSelect
                    while sPathRest != '':
                        sPathRest, sPathTail = split(sPathRef)
                        if exists(sPathRest):
                            oPathElement = listdir(sPathRest)
                            if oPathElement.__len__() > 0:
                                break
                            else:
                                rmdir(sPathRest)
                                sPathRef = sPathRest
                        else:
                            break
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to compute time analysis
class DataAnalysisTime:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.sTimeStep = kwargs['time']
        self.oTimeInfo = kwargs['settings']['data']['dynamic']['time']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data time
    def computeDataTime(self, oData_Geo):

        # Get time information
        oTimeStep = pd.to_datetime(self.sTimeStep)
        oTimeInfo = self.oTimeInfo

        # Get time extra step(s)
        if 'time_extra_period' in oTimeInfo and 'time_extra_frequency' in oTimeInfo:
            iTimeExtra_Period = oTimeInfo['time_extra_period']
            if iTimeExtra_Period < 0:
                oTimeInfo['time_extra_period'] = oData_Geo.iGeoTc
                iTimeCorrivation = oData_Geo.iGeoTc
            else:
                iTimeCorrivation = oTimeInfo['time_extra_period']
        else:
            oTimeInfo['time_extra_period'] = 0
            oTimeInfo['time_extra_frequency'] = "H"
            iTimeCorrivation = 0

        # Get time observed step(s)
        if 'time_observed_period' in oTimeInfo and 'time_observed_frequency' in oTimeInfo:
            oTimeRange_OBS_EXP = pd.date_range(end=oTimeStep,
                                               periods=oTimeInfo["time_observed_period"],
                                               freq=oTimeInfo["time_observed_frequency"])

            oTimeRange_OBS_EXTRA = pd.date_range(start=oTimeStep,
                                                 periods=oTimeInfo["time_extra_period"] + 1,
                                                 freq=oTimeInfo["time_extra_frequency"],
                                                 closed="right")

            oTimeRange_OBS = oTimeRange_OBS_EXP.union(oTimeRange_OBS_EXTRA)

        else:
            oTimeRange_OBS = None

        # Get time forecast step(s)
        if 'time_forecast_period' in oTimeInfo and 'time_forecast_frequency' in oTimeInfo:
            oTimeRange_FOR_EXP = pd.date_range(start=oTimeStep,
                                               periods=oTimeInfo["time_observed_period"] + 1,
                                               freq=oTimeInfo["time_observed_frequency"],
                                               closed="right")

            oTimeRange_FOR_EXTRA = pd.date_range(start=oTimeRange_FOR_EXP[-1],
                                                 periods=oTimeInfo["time_extra_period"] + 1,
                                                 freq=oTimeInfo["time_extra_frequency"],
                                                 closed="right")

            oTimeRange_FOR = oTimeRange_FOR_EXP.union(oTimeRange_FOR_EXTRA)

        else:
            oTimeRange_FOR = None

        # Get starting time
        if ('time_starting_period' not in oTimeInfo) or (
                'time_starting_frequency' not in oTimeInfo) or ('time_starting_eta' not in oTimeInfo):
            oTimeInfo['time_starting_period'] = 48
            oTimeInfo['time_starting_frequency'] = 'H'
            oTimeInfo['time_starting_eta'] = 'D'
            Exc.getExc(' =====> WARNING: starting time parameter(s) is/are not defined, '
                       'algorithm will use default parameters! Check your time settings!', 2, 1)

        if (oTimeInfo['time_starting_period'] is None) or (
                oTimeInfo['time_starting_frequency'] is None) or (oTimeInfo['time_starting_eta'] is None):
            oTimeInfo['time_starting_period'] = 48
            oTimeInfo['time_starting_frequency'] = 'H'
            oTimeInfo['time_starting_eta'] = 'D'
            Exc.getExc(' =====> WARNING: starting time parameter(s) is/are defined with null, '
                       'algorithm will use default parameters! Check your time settings!', 2, 1)

        if 'time_starting_period' in oTimeInfo and 'time_starting_frequency' in oTimeInfo:

            oTimeStarting = oTimeStep - pd.to_timedelta(oTimeInfo["time_starting_period"],
                                                        unit=oTimeInfo["time_starting_frequency"])
            oTimeStarting = oTimeStarting.floor(oTimeInfo['time_starting_eta'])

        else:
            Exc.getExc(' =====> ERROR: starting time is null! Check your time settings!', 1, 1)

        oTimeRange = None
        if (oTimeRange_OBS is not None) and (oTimeRange_FOR is not None):
            oTimeRange = oTimeRange_OBS.union(oTimeRange_FOR)
        elif oTimeRange_FOR is None:
            oTimeRange = oTimeRange_OBS
        elif oTimeRange_OBS is None:
            oTimeRange = oTimeRange_FOR
        else:
            Exc.getExc(' =====> ERROR: date time is null! Check your time settings!', 1, 1)

        # Add attributes to date time obj
        setattr(oTimeRange, 'info', oTimeInfo)
        setattr(oTimeRange, 'time_run', oTimeStep)
        setattr(oTimeRange, 'time_starting', oTimeStarting)
        setattr(oTimeRange, 'time_corrivation', iTimeCorrivation)

        return oTimeRange

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to manage gridded data analysis
class DataAnalysisManagerGridded:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        # Set argument(s)
        self.oVarBuffer = kwargs['settings']['buffer']
        self.oVarTimeRun = kwargs['time_run']
        self.oVarTimePeriod = kwargs['time_period']
        self.oVarDef = kwargs['settings']['variables']['source']
        self.oVarSource = kwargs['file']
        self.oVarMapping = kwargs['mapping']
        self.oVarTags = kwargs['tags']

        # Map file(s)
        self.oVarFile, self.oVarBaseName, self.oVarMemory = fileMapping(
            self.oVarSource, self.oVarMapping, self.oVarTags)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data analysis
    def computeDataAnalysis(self, oVarDataDynamic, oDataGeo):

        # -------------------------------------------------------------------------------------
        # Get global declaration(s)
        oVarDef = self.oVarDef
        oVarTime_RUN = self.oVarTimeRun
        oVarTime_PERIOD = self.oVarTimePeriod

        oVarBaseName_MAP = self.oVarBaseName
        if oVarDataDynamic:
            oDatasetTime_MAP = oVarDataDynamic['memory_time_dataset']
            oVarFile_MAP = oVarDataDynamic['memory_file_variable']
            oVarUpd_MAP = oVarDataDynamic['memory_upd_variable']
        else:
            Exc.getExc(' =====> WARNING: data dynamic source information not found! Default values set!'
                       'Errors could occur during experiment!', 2, 1)
            oDatasetTime_MAP = None
            oVarFile_MAP = self.oVarFile
            oVarUpd_MAP = self.oVarMemory

        # Get buffer data information
        iVarTime_STORE_MAX = self.oVarBuffer['subset_max_step']
        sVarTime_STORE_FORMAT = self.oVarBuffer['subset_format']

        # Create indexes to chunk list (for buffering data)
        iVarTime_IDX = oVarTime_PERIOD.get_loc(oVarTime_RUN, method="nearest") + 1
        oVarTime_PERIOD_OBS = oVarTime_PERIOD[0:iVarTime_IDX]
        oVarTime_PERIOD_FOR = oVarTime_PERIOD[iVarTime_IDX:]
        oVarIdx_PERIOD = chunkList(oVarTime_PERIOD, iVarTime_STORE_MAX)

        # Set progress bar widget(s)
        oVarPBarWidgets = [
            ' ===== Getting data gridded progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over dataset(s)
        oGriddedData_WS = {}
        oGriddedAttrs_WS = {}
        oVarPBarObj = progressbar.ProgressBar(widgets=oVarPBarWidgets, redirect_stdout=True)
        for sVarKey, oVarFields in oVarPBarObj(oVarDef.items()):

            # DEBUG
            # sVarKey = "data_result_ts_discharge_ws" #
            # sVarKey = "data_obs_ts_discharge" #
            # sVarKey = "data_obs_gridded_forcing" # OK
            # sVarKey = "data_result_gridded_outcome" # OK
            # sVarKey = "data_forecast_gridded_forcing_probabilistic_ecmwf" # OK
            # sVarKey = "data_forecast_gridded_forcing_deterministic_ecmwf" # OK
            # sVarKey = "data_result_ts_discharge_probabilistic_ecmwf" #
            # sVarKey = "data_result_ts_discharge_deterministic_ecmwf"  #
            # sVarKey = "data_test_nodata"
            # oVarFields = oVarDef[sVarKey]
            # DEBUG

            # -------------------------------------------------------------------------------------
            # Get number of variable(s)
            iVarN = oVarFields['id']['var_name_in'].__len__()

            # Get variable information
            oVarDims = checkVarField(oVarFields['id']['var_dims'], iVarN)
            oVarTypeData = checkVarField(oVarFields['id']['var_type_data'], iVarN)
            oVarTypeAncillary = checkVarField(oVarFields['id']['var_type_ancillary'], iVarN)
            oVarTypeExp = checkVarField(oVarFields['id']['var_type_experiment'], iVarN)
            oVarNameSource = checkVarField(oVarFields['id']['var_name_in'], iVarN)
            oVarNameOutcome = checkVarField(oVarFields['id']['var_name_out'], iVarN)
            oVarSourceData = checkVarField(oVarFields['id']['var_file_data'], iVarN)
            oVarSourceAncillary = checkVarField(oVarFields['id']['var_file_ancillary'], iVarN)
            oVarSourceFormat = checkVarField(oVarFields['id']['var_file_format'], iVarN)
            oVarMethodName = checkVarField(oVarFields['id']['var_method_cmp_name_gridded'], iVarN)
            oVarArgs = checkVarField(oVarFields['id']['var_args'], iVarN, oListKeys=[oVarDims[0], oVarTypeData[0]])
            # Get variable attributes
            oVarUnits = checkVarField(oVarFields['attributes']['units'], iVarN)
            oVarScaleFactor = checkVarField(oVarFields['attributes']['ScaleFactor'], iVarN)
            oVarMissingValue = checkVarField(oVarFields['attributes']['Missing_value'], iVarN)
            oVarValidRange = checkVarField(oVarFields['attributes']['Valid_range'], iVarN)
            oVarFillValue = checkVarField(oVarFields['attributes']['_FillValue'], iVarN)

            # Set list for reducing variable(s) sample size
            [oVarDims, oVarTypeData, oVarTypeAncillary, oVarTypeExp,
             oVarSourceData, oVarSourceAncillary, oVarSourceFormat] = reduceList(
                {'list1': oVarDims, 'list2': oVarTypeData, 'list3': oVarTypeAncillary,
                 'list4': oVarTypeExp, 'list5': oVarSourceData, 'list6': oVarSourceAncillary,
                 'list7': oVarSourceFormat}).values()
            # Set list for method(s), source and outcome variable name(s)
            [oVarMethodName, oVarNameSource, oVarNameOutcome,
             oVarUnits, oVarScaleFactor, oVarMissingValue, oVarFillValue] = reduceList(
                {'list1': oVarMethodName, 'list2': oVarNameSource, 'list3': oVarNameOutcome,
                 'list4': oVarUnits, 'list5': oVarScaleFactor,
                 'list6': oVarMissingValue, 'list7': oVarFillValue}).values()
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Iterate over variable(s)
            for iVarID, (sVarDims, sVarTypeData, sVarTypeAncillary, sVarTypeExp,
                         sVarSourceData, sVarSourceAncillary, sVarSourceFormat,
                         sVarMethodName, oVarArg) in \
                    enumerate(zip(oVarDims, oVarTypeData, oVarTypeAncillary, oVarTypeExp,
                                  oVarSourceData, oVarSourceAncillary, oVarSourceFormat,
                                  oVarMethodName, oVarArgs)):

                # -------------------------------------------------------------------------------------
                # Info of buffering dataset
                oLogStream.info(' ---> Buffering -- Group: ' + sVarSourceData + ' ... ')

                # Select variable dimension(s)
                if (sVarDims == 'var2d') or (sVarDims == 'var3d'):

                    # Method to define variable settings
                    oVarSettings = setVarSettings(sVarDims, sVarTypeData, oVarArg, oVarTime_PERIOD_OBS,
                                                  oVarTime_PERIOD_FOR)

                    # Method to define variable attribute(s)
                    oVarAttributes = setVarAttributes(oVarDataDynamic[sVarSourceData], oVarAttributes_Valid)

                    # Define ensemble based on variable info
                    oDatasetEns_REF_SUBPERIOD = setVarEnsemble(
                        sVarTypeData, oVarSettings,
                        [checkVarName('ensemble_n', oVarArgs_Valid)[0],
                         checkVarName("ensemble_format", oVarArgs_Valid)[0]])

                    # Define time step based on effective data available on variable path
                    oDatasetTime_MAP, oVarFile_MAP, oVarUpd_MAP = setDatasetTime_Finder(
                        oVarTime_RUN,
                        sVarTypeData, sVarTypeAncillary, sVarSourceData, sVarSourceAncillary,
                        oVarFile_MAP, oVarBaseName_MAP, oVarUpd_MAP, oDatasetTime_MAP,
                        oVarSRC_ENSEMBLE=oDatasetEns_REF_SUBPERIOD)

                    # Define data chunks based subset info
                    [oVarTime_RUN_SUBPERIOD, oVarTime_REF_SUBPERIOD,
                     oVarIdx_REF_SUBPERIOD, oVarTime_RUN_RANGE] = setVarChunk(
                        oVarTime_RUN, oDatasetTime_MAP[sVarSourceData],
                        oVarTime_PERIOD,
                        oVarIdx_PERIOD,
                        sVarTypeData,
                        oVarSettings)

                    # Define time step based on variable info
                    oDatasetTime_REF_SUBPERIOD = setDatasetTime_Steps(
                        sVarTypeData, oVarSettings,
                        oVarTime_REF_SUBPERIOD,
                        [checkVarName('data_period', oVarArgs_Valid)[0],
                         checkVarName("data_frequency", oVarArgs_Valid)[0]])
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Iterate over buffer indexes
                    oVarData_BUFFER = None
                    oVarData_WS = None
                    oVarIdx_STORE_STEP = None
                    for iVarIdx_REF_STEP, iFreqIdx_REF_STEP in zip(set(oVarIdx_PERIOD), countListElemFreq(oVarIdx_PERIOD)):

                        # -------------------------------------------------------------------------------------
                        # Get generic dataset filename(s)
                        sVarFileName_BUFFER = oVarFile_MAP['file_buffer_source_data']

                        # Chunk element
                        sVarIdx_REF_STEP = sVarTime_STORE_FORMAT.format(iVarIdx_REF_STEP)
                        if oVarIdx_STORE_STEP is None:
                            oVarIdx_STORE_STEP = [iVarIdx_REF_STEP]
                        else:
                            oVarIdx_STORE_STEP.append(iVarIdx_REF_STEP)

                        # Define buffer filename
                        oFileTags_BUFFER = {
                            '$yyyy': str(oVarTime_RUN.year).zfill(4),
                            '$mm': str(oVarTime_RUN.month).zfill(2),
                            '$dd': str(oVarTime_RUN.day).zfill(2),
                            '$HH': str(oVarTime_RUN.hour).zfill(2),
                            '$MM': str(oVarTime_RUN.minute).zfill(2),
                            '$subset': sVarIdx_REF_STEP
                        }

                        # Get filename from file definition(s) using file tag in outcome variable(s)
                        sVarFileName_BUFFER = defineString(deepcopy(sVarFileName_BUFFER), oFileTags_BUFFER)
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Get variable(s) in data array format
                        if isfile(sVarFileName_BUFFER):

                            # -------------------------------------------------------------------------------------
                            # Get buffer file
                            oVarFile_BUFFER = readFileNC4(sVarFileName_BUFFER, oVarGroup=sVarSourceData)
                            # Get buffer data
                            oVarData_BUFFER = oVarFile_BUFFER[sVarSourceData]
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Select variable case
                            if oVarData_BUFFER is not None:

                                # -------------------------------------------------------------------------------------
                                # Get var2D or var3D data
                                if oVarData_WS is None:
                                    oVarData_WS = oVarData_BUFFER
                                else:
                                    oVarData_WS = xr.auto_combine([oVarData_WS, oVarData_BUFFER], concat_dim='time')
                                # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------

                    # Info of buffering dataset
                    oLogStream.info(' ---> Buffering -- Group: ' + sVarSourceData + ' ... DONE')
                    # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Info of buffering dataset
                    oLogStream.info(' ---> Buffering -- Group: ' +
                                    sVarSourceData + ' ... SKIPPED. Variable dimensions are not 2D or 3D.')
                    oVarData_WS = None
                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Info of buffering dataset
                oLogStream.info(' ---> Analyzing -- Group: ' + sVarSourceData + ' ... ')

                # Check data availability
                if oVarData_WS is not None:

                    # ------------------------------------------------------------------------------------
                    # Get information about variable(s) settings about resample method, time period and steps
                    oVarFreq_SEL = []
                    a1oVarPeriod_SEL = []
                    oVarTag_SEL = []
                    oVarStep_SEL = []
                    for oVarArgs_STEP in oVarArgs:
                        oVarArg_STEP = oVarArgs_STEP[sVarDims][sVarTypeData]

                        if 'var_frequency' in oVarArg_STEP:
                            oVarFreq_SEL.append(oVarArg_STEP['var_frequency'][0])
                        if 'var_period' in oVarArg_STEP:
                            a1oVarPeriod_SEL.append(oVarArg_STEP['var_period'][0])
                        if 'var_tag' in oVarArg_STEP:
                            oVarTag_SEL.append(oVarArg_STEP['var_tag'][0])
                        if 'var_step' in oVarArg_STEP:
                            oVarStep_SEL.append(oVarArg_STEP['var_step'][0])

                    # Fill data workspace
                    if sVarSourceData not in oGriddedData_WS:
                        oGriddedData_WS[sVarSourceData] = {}
                        oGriddedAttrs_WS[sVarSourceData] = {}
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Set ensemble mode (if needed)
                    if oDatasetEns_REF_SUBPERIOD is not None:

                        # Select probabilistic case
                        iEnsembleN = oDatasetEns_REF_SUBPERIOD.__len__()

                        # Select probabilistic case
                        oVarNameOutcome_ENS = []
                        for sVarNameOutcome_RAW in oVarNameOutcome:
                            for sDatasetEns_NAME in oDatasetEns_REF_SUBPERIOD:
                                sVarNameOutcome_ENS = defineString(
                                    sVarNameOutcome_RAW, {'$ensemble': sDatasetEns_NAME})
                                oVarNameOutcome_ENS.append(sVarNameOutcome_ENS)

                        oVarNameOutcome_SEL = deepcopy(oVarNameOutcome_ENS)
                        oVarMethodName_SEL = checkVarField(oVarMethodName, iEnsembleN)
                        oVarUnits_SEL = checkVarField(oVarUnits, iEnsembleN)
                        oVarScalarFactor_SEL = checkVarField(oVarScaleFactor, iEnsembleN)
                        oVarMissingValue_SEL = checkVarField(oVarMissingValue, iEnsembleN)
                        a1oVarValidRange_SEL = checkVarField(oVarValidRange, iEnsembleN)
                        oVarFillValue_SEL = checkVarField(oVarFillValue, iEnsembleN)

                        oVarFreq_SEL = checkVarField(oVarFreq_SEL, iEnsembleN)
                        a1oVarPeriod_SEL = checkVarField(a1oVarPeriod_SEL, iEnsembleN)
                        oVarTag_SEL = checkVarField(oVarTag_SEL, iEnsembleN)

                    else:

                        # Select deterministic case
                        oVarNameOutcome_SEL = oVarNameOutcome
                        oVarMethodName_SEL = oVarMethodName
                        oVarUnits_SEL = oVarUnits
                        oVarScalarFactor_SEL = oVarScaleFactor
                        oVarMissingValue_SEL = oVarMissingValue
                        a1oVarValidRange_SEL = oVarValidRange
                        oVarFillValue_SEL = oVarFillValue

                        oVarFreq_SEL = checkVarField(oVarFreq_SEL, oVarNameOutcome_SEL.__len__())
                        a1oVarPeriod_SEL = checkVarField(a1oVarPeriod_SEL, oVarNameOutcome_SEL.__len__())
                        oVarTag_SEL = checkVarField(oVarTag_SEL, oVarNameOutcome_SEL.__len__())
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Iterate over variable method and outcome name
                    oVarDSet_SEL = None
                    oVarAttr_SEL = {}
                    for sVarMethodName_SEL, sVarNameOutcome_SEL, \
                        sVarUnits_SEL, iVarScalaFactor_SEL, dVarMissingValue_SEL,\
                        oVarValidRange_SEL, dVarFillValue_SEL, \
                        sVarFreq_SEL, oVarPeriod_SEL, sVarTag_SEL in \
                            zip(oVarMethodName_SEL, oVarNameOutcome_SEL,
                                oVarUnits_SEL, oVarScalarFactor_SEL, oVarMissingValue_SEL,
                                a1oVarValidRange_SEL, oVarFillValue_SEL,
                                oVarFreq_SEL, a1oVarPeriod_SEL, oVarTag_SEL):

                        # -------------------------------------------------------------------------------------
                        # Info start outcome variable
                        oLogStream.info(' ----> Analysis gridded data for variable ' + sVarNameOutcome_SEL + ' ... ')

                        # Check information for customize outcome gridded variable
                        if (sVarFreq_SEL is not None) and (oVarPeriod_SEL is not None) and (sVarTag_SEL is not None):

                            # Iterate over resample period
                            for iVarPeriod_SEL in oVarPeriod_SEL:

                                # -------------------------------------------------------------------------------------
                                # Define variable name
                                sVarName_SEL = defineString(sVarTag_SEL,
                                                            {'$var': sVarNameOutcome_SEL, '$period': str(iVarPeriod_SEL)})

                                # Info start
                                oLogStream.info(' -----> Computing gridded data for variable ' + sVarName_SEL + ' ... ')
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Select computing method to get time series
                                oVarDSet_ATTRS = {}
                                if sVarMethodName_SEL is not None:

                                    # -------------------------------------------------------------------------------------
                                    # Check method availability in selected library
                                    if hasattr(oLibCmpGridded, sVarMethodName_SEL):

                                        # -------------------------------------------------------------------------------------
                                        # Select data using time range
                                        if sVarTypeData == 'observed':
                                            oVarDateTime_SEL = oVarTime_PERIOD_OBS[-1]
                                            oVarDateRange_SEL = pd.date_range(end=oVarDateTime_SEL,
                                                                              periods=iVarPeriod_SEL, freq=sVarFreq_SEL)

                                        elif sVarTypeData == 'forecast':
                                            oVarDateTime_SEL = oVarTime_PERIOD_FOR[0]
                                            oVarDateRange_SEL = pd.date_range(start=oVarTime_PERIOD_FOR[0],
                                                                              periods=iVarPeriod_SEL, freq=sVarFreq_SEL)
                                        elif sVarTypeData == 'result':
                                            oVarDateTime_SEL = oVarTime_RUN
                                            oVarDateRange_SEL = pd.date_range(end=oVarTime_RUN,
                                                                              periods=iVarPeriod_SEL, freq=sVarFreq_SEL)
                                        else:
                                            oVarDateTime_SEL = None
                                            oVarDateRange_SEL = None
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Select data
                                        if oVarDateRange_SEL is not None:

                                            # -------------------------------------------------------------------------------------
                                            # Select data using date times
                                            oVarDateRange_WS = pd.DatetimeIndex(oVarData_WS.time.values)
                                            oVarDataRange_DIFF = oVarDateRange_SEL.difference(oVarDateRange_WS)

                                            # Check if all time steps are defined in datasets
                                            if not oVarDataRange_DIFF.empty:
                                                oVarDateRange_FILL = oVarDateRange_WS.union(oVarDataRange_DIFF)
                                                oVarData_FILL = xr.Dataset(
                                                    coords={'time': (['time'], pd.to_datetime(oVarDateRange_FILL))})
                                                oVarData_FILLED = oVarData_FILL.combine_first(oVarData_WS)

                                                Exc.getExc(
                                                    ' =====> WARNING: some time step(s) are missed: ' +
                                                    str(oVarDataRange_DIFF.to_list()) + '. Step(s) filled using NaNs!',
                                                    2, 1)
                                            else:
                                                oVarData_FILLED = oVarData_WS

                                            # Find finite time step(s)
                                            _, oVarDateRange_FINITE = oLibCmpTS.findVarFinite(
                                                oVarData_FILLED, sVarName=sVarNameOutcome_SEL)
                                            # Find common time step(s) between finite and generic selection
                                            oVarDateRange_INTER = oVarDateRange_FINITE.intersection(oVarDateRange_SEL)

                                            # Select data by using finite time step(s)
                                            if oVarDateRange_INTER.size < oVarDateRange_SEL.size:
                                                oVarDateRange_FINITE_SEL = oVarDateRange_FINITE[-oVarDateRange_SEL.size:]
                                            else:
                                                oVarDateRange_FINITE_SEL = oVarDateRange_SEL

                                            # Check availability of all time step(s)
                                            oVarData_SEL = oVarData_FILLED.sel(time=oVarDateRange_FINITE_SEL)
                                            bVarData_SEL = list(oVarData_SEL.indexes.values())[0].equals(
                                                oVarDateRange_FINITE_SEL)
                                            # -------------------------------------------------------------------------------------

                                            # -------------------------------------------------------------------------------------
                                            # Apply method to data
                                            if bVarData_SEL:

                                                # Add information about effective computating time step(s)
                                                oVarAttributes['time_from'] = oVarDateRange_FINITE_SEL[0]
                                                oVarAttributes['time_to'] = oVarDateRange_FINITE_SEL[-1]

                                                # Set variable attributes
                                                oVarGridded_ATTRIBUTES = mergeDict(
                                                    {'units': sVarUnits_SEL, 'ScaleFactor': iVarScalaFactor_SEL,
                                                     'Missing_value': dVarMissingValue_SEL,
                                                     'Valid_range': oVarValidRange_SEL,
                                                     '_FillValue': dVarFillValue_SEL}, oVarAttributes)

                                                # Set argument(s)
                                                oFxArgs = {'oVarData': oVarData_SEL[sVarNameOutcome_SEL],
                                                           'oVarMask': oDataGeo.a2dGeoData,
                                                           'sVarIdx': oVarStep_SEL,
                                                           'oVarTime': oVarDateTime_SEL,
                                                           'oVarAttributes': oVarGridded_ATTRIBUTES}

                                                # Compute variable data
                                                oVarGridded_SEL = configVarFx(sVarMethodName_SEL, oLibCmpGridded,
                                                                              oFxArgs)

                                                # Info end
                                                oLogStream.info(' -----> Computing gridded data for variable ' +
                                                                sVarName_SEL + ' ... DONE')
                                            else:
                                                # Exit for incomplete time period
                                                oVarGridded_SEL = None
                                                oVarGridded_ATTRIBUTES = None
                                                # Info end
                                                oLogStream.info(' -----> Computing gridded data for variable ' +
                                                                sVarName_SEL + ' ... SKIPPED')
                                                Exc.getExc(' =====> WARNING: incomplete data period!', 2, 1)
                                            # -------------------------------------------------------------------------------------
                                        else:
                                            # -------------------------------------------------------------------------------------
                                            # Exit for undefined time period
                                            oVarGridded_SEL = None
                                            oVarGridded_ATTRIBUTES = None
                                            # Info end
                                            oLogStream.info(' -----> Computing gridded data for variable ' +
                                                            sVarName_SEL + ' ... SKIPPED')
                                            Exc.getExc(' =====> WARNING: undefined data period!', 2, 1)
                                            # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                    else:
                                        # -------------------------------------------------------------------------------------
                                        # Exit for undefined method
                                        oVarGridded_SEL = None
                                        oVarGridded_ATTRIBUTES = None
                                        # Info end
                                        oLogStream.info(' -----> Computing gridded data for variable ' +
                                                        sVarName_SEL + ' ... SKIPPED')
                                        Exc.getExc(' =====> WARNING: computing method not defined in library!', 2, 1)
                                        # -------------------------------------------------------------------------------------
                                else:
                                    # -------------------------------------------------------------------------------------
                                    # Exit for undefined method
                                    oVarGridded_SEL = None
                                    oVarGridded_ATTRIBUTES = None
                                    # Info end
                                    oLogStream.info(' -----> Computing gridded data for variable ' +
                                                    sVarName_SEL + ' ... SKIPPED')
                                    Exc.getExc(' =====> WARNING: computing method not defined!', 2, 1)
                                    # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Save variable(s) in a common dataset
                                if oVarGridded_SEL is not None:

                                    oVarDSet_DATA = oVarGridded_SEL.to_dataset(name=sVarName_SEL)
                                    # oVarDSet_DATA = addDataSetAttr(oVarDSet_DATA, oVarGridded_SEL.attrs)

                                    if oVarDSet_SEL is None:
                                        oVarDSet_SEL = oVarDSet_DATA
                                    else:
                                        oVarDSet_SEL = xr.auto_combine([oVarDSet_SEL, oVarDSet_DATA],
                                                                       concat_dim='time')

                                    if sVarName_SEL not in oVarAttr_SEL:
                                        oVarAttr_SEL[sVarName_SEL] = oVarGridded_ATTRIBUTES
                                # -------------------------------------------------------------------------------------

                            # ------------------------------------------------------------------------------------
                            # Info end
                            oLogStream.info(' ----> Analysis gridded data for variable ' +
                                            sVarNameOutcome_SEL + ' ... DONE')
                            # ------------------------------------------------------------------------------------
                        else:
                            # ------------------------------------------------------------------------------------
                            # Exit for undefined method
                            oLogStream.info(' ----> Analysis gridded data for variable ' +
                                            sVarNameOutcome_SEL + ' ... SKIPPED')
                            Exc.getExc(' =====> WARNING: some information for outcome variable are missed!', 2, 1)
                            # ------------------------------------------------------------------------------------

                        # ------------------------------------------------------------------------------------

                    # ------------------------------------------------------------------------------------
                    # Store data in a common workspace
                    if oVarDSet_SEL is not None:
                        oGriddedData_WS[sVarSourceData] = {}
                        oGriddedData_WS[sVarSourceData] = oVarDSet_SEL

                        oGriddedAttrs_WS[sVarSourceData] = {}
                        oGriddedAttrs_WS[sVarSourceData] = oVarAttr_SEL

                    # ------------------------------------------------------------------------------------

                    # ------------------------------------------------------------------------------------
                    # Info of buffering dataset
                    oLogStream.info(' ---> Analyzing -- Group: ' + sVarSourceData + ' ... DONE')
                    # ------------------------------------------------------------------------------------

                else:

                    # -------------------------------------------------------------------------------------
                    # Info of buffering dataset
                    oLogStream.info(' ---> Analyzing -- Group: ' + sVarSourceData + ' ... SKIPPED')
                    Exc.getExc(' =====> WARNING: selected data are null!', 2, 1)
                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        oVarDataGridded_WS = {'data': oGriddedData_WS, 'attributes': oGriddedAttrs_WS}
        return oVarDataGridded_WS
        # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to manage time-series data analysis
class DataAnalysisManagerTimeSeries:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        # Set argument(s)
        self.oVarBuffer = kwargs['settings']['buffer']
        self.oVarTimeRun = kwargs['time_run']
        self.oVarTimePeriod = kwargs['time_period']
        self.oVarDef = kwargs['settings']['variables']['source']
        self.oVarSource = kwargs['file']
        self.oVarMapping = kwargs['mapping']
        self.oVarTags = kwargs['tags']

        # Map file(s)
        self.oVarFile , self.oVarBaseName, self.oVarMemory = fileMapping(
            self.oVarSource, self.oVarMapping, self.oVarTags)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data analysis
    def computeDataAnalysis(self, oVarDataDynamic, oDataPoint):

        # -------------------------------------------------------------------------------------
        # Get global declaration(s)
        oVarDef = self.oVarDef
        oVarTime_RUN = self.oVarTimeRun
        oVarTime_PERIOD = self.oVarTimePeriod

        if hasattr(self.oVarTimePeriod, 'time_starting'):
            oVarTime_STARTING = self.oVarTimePeriod.time_starting
        else:
            oVarTime_STARTING = None
            Exc.getExc(' =====> WARNING: starting time is not available! Errors could occur during experiment!', 2, 1)

        oVarBaseName_MAP = self.oVarBaseName
        if oVarDataDynamic:
            oDatasetTime_MAP = oVarDataDynamic['memory_time_dataset']
            oVarFile_MAP = oVarDataDynamic['memory_file_variable']
            oVarUpd_MAP = oVarDataDynamic['memory_upd_variable']
        else:
            Exc.getExc(' =====> WARNING: data dynamic source information not found! Default values set!'
                       'Errors could occur during experiment!', 2, 1)
            oDatasetTime_MAP = None
            oVarFile_MAP = self.oVarFile
            oVarUpd_MAP = self.oVarMemory

        # Get buffer data information
        iVarTime_STORE_MAX = self.oVarBuffer['subset_max_step']
        sVarTime_STORE_FORMAT = self.oVarBuffer['subset_format']

        # Create indexes to chunk list (for buffering data)
        iVarTime_IDX = oVarTime_PERIOD.get_loc(oVarTime_RUN, method="nearest") + 1
        oVarTime_PERIOD_OBS = oVarTime_PERIOD[0:iVarTime_IDX]
        oVarTime_PERIOD_FOR = oVarTime_PERIOD[iVarTime_IDX:]
        oVarIdx_PERIOD = chunkList(oVarTime_PERIOD, iVarTime_STORE_MAX)

        # Set progress bar widget(s)
        oVarPBarWidgets = [
            ' ===== Getting data timeseries progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over dataset(s)
        oSectionData_WS = {}
        oSectionAttrs_WS = {}
        oVarPBarObj = progressbar.ProgressBar(widgets=oVarPBarWidgets, redirect_stdout=True)
        for sVarKey, oVarFields in oVarPBarObj(oVarDef.items()):

            # DEBUG
            # sVarKey = "data_result_ts_discharge_ws" # OK
            # sVarKey = "data_obs_ts_discharge" #
            # sVarKey = "data_obs_gridded_forcing" # OK
            # sVarKey = "data_result_gridded_outcome" # OK
            # sVarKey = "data_forecast_gridded_forcing_probabilistic_ecmwf" # OK
            # sVarKey = "data_forecast_gridded_forcing_deterministic_ecmwf" #
            # sVarKey = "data_result_ts_discharge_probabilistic_ecmwf" # OK
            # sVarKey = "data_result_ts_discharge_deterministic_ecmwf"  #
            # sVarKey = "data_forecast_gridded_forcing_probabilistic_lami" #
            # sVarKey = "data_forecast_gridded_forcing_deterministic_lami" #
            # sVarKey = "data_test_nodata"
            # oVarFields = oVarDef[sVarKey]
            # DEBUG

            # -------------------------------------------------------------------------------------
            # Get number of variable(s)
            iVarN = oVarFields['id']['var_name_in'].__len__()

            # Get variable information
            oVarDims = checkVarField(oVarFields['id']['var_dims'], iVarN)
            oVarTypeData = checkVarField(oVarFields['id']['var_type_data'], iVarN)
            oVarTypeAncillary = checkVarField(oVarFields['id']['var_type_ancillary'], iVarN)
            oVarTypeExp = checkVarField(oVarFields['id']['var_type_experiment'], iVarN)
            oVarNameSource = checkVarField(oVarFields['id']['var_name_in'], iVarN)
            oVarNameOutcome = checkVarField(oVarFields['id']['var_name_out'], iVarN)
            oVarSourceData = checkVarField(oVarFields['id']['var_file_data'], iVarN)
            oVarSourceAncillary = checkVarField(oVarFields['id']['var_file_ancillary'], iVarN)
            oVarSourceFormat = checkVarField(oVarFields['id']['var_file_format'], iVarN)
            oVarMethodName = checkVarField(oVarFields['id']['var_method_cmp_name_ts'], iVarN)
            oVarArgs = checkVarField(oVarFields['id']['var_args'], iVarN, oListKeys=[oVarDims[0], oVarTypeData[0]])
            # Get variable attributes
            oVarUnits = checkVarField(oVarFields['attributes']['units'], iVarN)
            oVarScaleFactor = checkVarField(oVarFields['attributes']['ScaleFactor'], iVarN)
            oVarMissingValue = checkVarField(oVarFields['attributes']['Missing_value'], iVarN)
            oVarValidRange = checkVarField(oVarFields['attributes']['Valid_range'], iVarN)
            oVarFillValue = checkVarField(oVarFields['attributes']['_FillValue'], iVarN)

            # Set list for reducing variable(s) sample size
            [oVarDims, oVarTypeData, oVarTypeAncillary, oVarTypeExp,
             oVarSourceData, oVarSourceAncillary, oVarSourceFormat] = reduceList(
                {'list1': oVarDims, 'list2': oVarTypeData, 'list3': oVarTypeAncillary, 'list4': oVarTypeExp,
                 'list5': oVarSourceData, 'list6': oVarSourceAncillary, 'list7': oVarSourceFormat}).values()
            # Set list for method(s), source and outcome variable name(s)
            [oVarMethodName, oVarNameSource, oVarNameOutcome] = reduceList(
                {'list1': oVarMethodName, 'list2': oVarNameSource, 'list3': oVarNameOutcome}).values()
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Iterate over variable(s)
            for iVarID, (sVarDims, sVarTypeData, sVarTypeAncillary, sVarTypeExp,
                         sVarSourceData, sVarSourceAncillary, sVarSourceFormat,
                         sVarMethodName, oVarArg) in \
                    enumerate(zip(oVarDims, oVarTypeData, oVarTypeAncillary, oVarTypeExp,
                                  oVarSourceData, oVarSourceAncillary, oVarSourceFormat,
                                  oVarMethodName, oVarArgs)):

                # -------------------------------------------------------------------------------------
                # Info of buffering dataset
                oLogStream.info(' ---> Buffering -- Group: ' + sVarSourceData + ' ... ')

                # Method to define variable settings
                oVarSettings = setVarSettings(sVarDims, sVarTypeData, oVarArg, oVarTime_PERIOD_OBS, oVarTime_PERIOD_FOR)
                # Method to define variable attribute(s)
                oVarAttributes = setVarAttributes(oVarDataDynamic[sVarSourceData], oVarAttributes_Valid)

                # Define ensemble based on variable info
                oDatasetEns_REF_SUBPERIOD = setVarEnsemble(
                    sVarTypeData, oVarSettings,
                    [checkVarName('ensemble_n', oVarArgs_Valid)[0],
                     checkVarName("ensemble_format", oVarArgs_Valid)[0]])

                # Define time step based on effective data available on variable path
                oDatasetTime_MAP, oVarFile_MAP, oVarUpd_MAP = setDatasetTime_Finder(
                    oVarTime_RUN,
                    sVarTypeData, sVarTypeAncillary, sVarSourceData, sVarSourceAncillary,
                    oVarFile_MAP, oVarBaseName_MAP, oVarUpd_MAP, oDatasetTime_MAP,
                    oVarSRC_ENSEMBLE=oDatasetEns_REF_SUBPERIOD)

                # Define data chunks based subset info
                [oVarTime_RUN_SUBPERIOD, oVarTime_REF_SUBPERIOD,
                 oVarIdx_REF_SUBPERIOD, oVarTime_RUN_RANGE] = setVarChunk(
                    oVarTime_RUN, oDatasetTime_MAP[sVarSourceData],
                    oVarTime_PERIOD,
                    oVarIdx_PERIOD,
                    sVarTypeData,
                    oVarSettings)

                # Define time step based on variable info
                oDatasetTime_REF_SUBPERIOD = setDatasetTime_Steps(
                    sVarTypeData, oVarSettings,
                    oVarTime_REF_SUBPERIOD,
                    [checkVarName('data_period', oVarArgs_Valid)[0],
                     checkVarName("data_frequency", oVarArgs_Valid)[0]])
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Iterate over buffer indexes
                oVarData_WS = None
                oVarIdx_STORE_STEP = None
                for iVarIdx_REF_STEP, iFreqIdx_REF_STEP in zip(set(oVarIdx_PERIOD), countListElemFreq(oVarIdx_PERIOD)):

                    # -------------------------------------------------------------------------------------
                    # Get generic dataset filename(s)
                    sVarFileName_BUFFER = oVarFile_MAP['file_buffer_source_data']

                    # Chunk element
                    sVarIdx_REF_STEP = sVarTime_STORE_FORMAT.format(iVarIdx_REF_STEP)
                    if oVarIdx_STORE_STEP is None:
                        oVarIdx_STORE_STEP = [iVarIdx_REF_STEP]
                    else:
                        oVarIdx_STORE_STEP.append(iVarIdx_REF_STEP)

                    # Define buffer filename
                    oFileTags_BUFFER = {
                        '$yyyy': str(oVarTime_RUN.year).zfill(4),
                        '$mm': str(oVarTime_RUN.month).zfill(2),
                        '$dd': str(oVarTime_RUN.day).zfill(2),
                        '$HH': str(oVarTime_RUN.hour).zfill(2),
                        '$MM': str(oVarTime_RUN.minute).zfill(2),
                        '$subset': sVarIdx_REF_STEP
                    }

                    # Get filename from file definition(s) using file tag in outcome variable(s)
                    sVarFileName_BUFFER = defineString(deepcopy(sVarFileName_BUFFER), oFileTags_BUFFER)

                    # Get dataset time
                    oVarTime_DATASET = oDatasetTime_MAP[sVarSourceData]
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Get variable(s) in data array format
                    if isfile(sVarFileName_BUFFER):

                        # -------------------------------------------------------------------------------------
                        # Get buffer file
                        oVarFile_BUFFER = readFileNC4(sVarFileName_BUFFER, oVarGroup=sVarSourceData)
                        # Get buffer data
                        oVarData_BUFFER = oVarFile_BUFFER[sVarSourceData]
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Select variable case
                        if oVarData_BUFFER is not None:

                            # -------------------------------------------------------------------------------------
                            # Select variable dimension(s)
                            if (sVarDims == 'var2d') or (sVarDims == 'var3d'):

                                # -------------------------------------------------------------------------------------
                                # Get var2D or var3D data
                                # bVarChk = all(sElem in oVarData_BUFFER.variables.keys() for sElem in oVarNameOutcome)

                                if oVarData_WS is None:
                                    oVarData_WS = oVarData_BUFFER
                                else:
                                    oVarData_WS = xr.auto_combine([oVarData_WS, oVarData_BUFFER], concat_dim='time')
                                # -------------------------------------------------------------------------------------

                            elif sVarDims == 'var1d':

                                # -------------------------------------------------------------------------------------
                                # Get var1D data
                                if oVarData_WS is None:
                                    oVarData_WS = oVarData_BUFFER.to_array()
                                else:
                                    oVarData_WS = xr.concat([oVarData_WS, oVarData_BUFFER.to_array()], dim='time')
                                # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------

                # Info of buffering dataset
                oLogStream.info(' ---> Buffering -- Group: ' + sVarSourceData + ' ... DONE')
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Info of buffering dataset
                oLogStream.info(' ---> Analyzing -- Group: ' + sVarSourceData + ' ... ')
                # Check data availability
                if oVarData_WS is not None:

                    # DEBUG
                    # oDataPoint = oDataPoint.iloc[1:2]
                    # DEBUG

                    # -------------------------------------------------------------------------------------
                    # Iterate over section(s)
                    for iSectionID, oSectionData in enumerate(oDataPoint.iterrows()):

                        # -------------------------------------------------------------------------------------
                        # Get section info
                        oSectionInfo = oSectionData[1]
                        sSectionName = oSectionInfo['OUTLET_NAME']
                        sSectionFileAncillary = oSectionInfo['OUTLET_FILE_ANCILLARY']
                        # Info start
                        oLogStream.info(' ----> Analysis time-series data for section ' + sSectionName + ' ... ')

                        if sSectionName not in oSectionData_WS:
                            oSectionData_WS[sSectionName] = {}
                            oSectionAttrs_WS[sSectionName] = {}
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Check ancillary section file availability
                        if isfile(sSectionFileAncillary):

                            # ------------------------------------------------------------------------------------
                            # Get section ancillary file
                            oSectionInfo = readFileNC4(sSectionFileAncillary, oVarEngine='h5netcdf')
                            # ------------------------------------------------------------------------------------

                            # ------------------------------------------------------------------------------------
                            # Select variable dimension(s)
                            oSectionATTR_SEL = {}
                            oSectionDF_SEL = oLibCmpTS.createVarDataFrame(oVarTime_PERIOD)
                            if (sVarDims == 'var2d') or (sVarDims == 'var3d'):

                                # ------------------------------------------------------------------------------------
                                # Create section mask
                                oSectionMask = oSectionInfo['Mask'].values
                                oSectionMask = where(isnan(oSectionMask), -9999.0, oSectionMask)

                                # Insert mask in data workspace
                                oVarData_WS.coords['Mask'] = (('south_north', 'west_east'), oSectionMask)
                                oSectionData_SEL = oVarData_WS.where(oVarData_WS.Mask > 0)

                                # Set ensemble mode (if needed)
                                if oDatasetEns_REF_SUBPERIOD is not None:

                                    # Select probabilistic case
                                    iEnsembleN = oDatasetEns_REF_SUBPERIOD.__len__()

                                    # Select probabilistic case
                                    oVarNameOutcome_ENS = []
                                    for sVarNameOutcome_RAW in oVarNameOutcome:
                                        for sDatasetEns_NAME in oDatasetEns_REF_SUBPERIOD:
                                            sVarNameOutcome_ENS = defineString(
                                                sVarNameOutcome_RAW, {'$ensemble': sDatasetEns_NAME})
                                            oVarNameOutcome_ENS.append(sVarNameOutcome_ENS)

                                    oVarNameOutcome_SEL = deepcopy(oVarNameOutcome_ENS)
                                    oVarMethodName_SEL = checkVarField(oVarMethodName, iEnsembleN)
                                    oVarUnits_SEL = checkVarField(oVarUnits, iEnsembleN)
                                    oVarScalarFactor_SEL = checkVarField(oVarScaleFactor, iEnsembleN)
                                    oVarMissingValue_SEL = checkVarField(oVarMissingValue, iEnsembleN)
                                    a1oVarValidRange_SEL = checkVarField(oVarValidRange, iEnsembleN)
                                    oVarFillValue_SEL = checkVarField(oVarFillValue, iEnsembleN)
                                    oVarArgs_SEL = checkVarField(oVarArgs, iEnsembleN,
                                                                 oListKeys=[sVarDims, sVarTypeData])

                                else:

                                    # Select deterministic case
                                    oVarNameOutcome_SEL = oVarNameOutcome
                                    oVarMethodName_SEL = oVarMethodName
                                    oVarUnits_SEL = oVarUnits
                                    oVarScalarFactor_SEL = oVarScaleFactor
                                    oVarMissingValue_SEL = oVarMissingValue
                                    a1oVarValidRange_SEL = oVarValidRange
                                    oVarFillValue_SEL = oVarFillValue
                                    oVarArgs_SEL = oVarArgs

                                # Iterate over outcome variable(s)
                                for sVarNameTS_SEL, sVarMethodName_SEL, \
                                    sVarUnits_SEL, iVarScaleFactor_SEL, dVarMissingValue_SEL, \
                                    oVarValidRange_SEL, dVarFillValue_SEL, \
                                    oVarArg_SEL in zip(oVarNameOutcome_SEL, oVarMethodName_SEL, oVarUnits_SEL,
                                                       oVarScalarFactor_SEL, oVarMissingValue_SEL, a1oVarValidRange_SEL,
                                                       oVarFillValue_SEL, oVarArgs_SEL):
                                    # Get variable data
                                    oSectionData_SUBSET = oSectionData_SEL[sVarNameTS_SEL]
                                    # Set variable attributes
                                    oSectionData_ATTRIBUTES = mergeDict(
                                        {'units': sVarUnits_SEL, 'ScaleFactor': iVarScaleFactor_SEL,
                                         'Missing_value': dVarMissingValue_SEL,
                                         'Valid_range': oVarValidRange_SEL,
                                         '_FillValue': dVarFillValue_SEL}, oVarAttributes)

                                    # Get computing times (from and to)
                                    oVarCMP_SEL = getDictDeep(oVarArg_SEL, 'var_cmp_ts')

                                    if oVarCMP_SEL is not None:
                                        oTimeCMP_FROM = setDatasetTime_Cmp(oVarCMP_SEL[0][0],
                                                                           {'time_starting': oVarTime_STARTING,
                                                                            'time_run':oVarTime_RUN,
                                                                            'time_dataset': oVarTime_DATASET})

                                        oTimeCMP_TO = setDatasetTime_Cmp(oVarCMP_SEL[0][1],
                                                                           {'time_starting': oVarTime_STARTING,
                                                                            'time_run':oVarTime_RUN,
                                                                            'time_dataset': oVarTime_DATASET})
                                    else:
                                        oTimeCMP_FROM = None
                                        oTimeCMP_TO = None

                                    # Select computing method to get time series
                                    if sVarMethodName_SEL is not None:
                                        if hasattr(oLibCmpTS, sVarMethodName_SEL):
                                            # Set argument(s)
                                            oFxArgs = {'oVarData': oSectionData_SUBSET, 'oVarMask': oSectionMask,
                                                       'oVarTime_FROM': oTimeCMP_FROM, 'oVarTime_TO': oTimeCMP_TO}

                                            # Compute variable data
                                            oSectionTS_SUBSET = configVarFx(sVarMethodName_SEL, oLibCmpTS, oFxArgs)
                                        else:
                                            # Set argument(s)
                                            oFxArgs = {'oVarData': oSectionData_SUBSET}
                                            # Compute variable data
                                            oSectionTS_SUBSET = configVarFx('cmpVarMean', oLibCmpTS, oFxArgs)
                                    else:
                                        oSectionTS_SUBSET = None

                                    # Store data in a default dataframe
                                    if oSectionTS_SUBSET is not None:

                                        # Get data section and set attribute(s)
                                        oSectionDArray_SUBSET = oSectionTS_SUBSET.to_xarray()
                                        # oSectionDArray_SUBSET = addDataSetAttr(oSectionDArray_SUBSET,
                                        #                                        oSectionData_ATTRIBUTES)
                                        oSectionDSet_SUBSET = oSectionDArray_SUBSET.to_dataset(name=sVarNameTS_SEL)

                                        # Combine dataset to the same period
                                        oSectionDSet_RAW = xr.Dataset(coords={'time': (['time'], oVarTime_PERIOD)})
                                        oSectionDSet_COMBINE = oSectionDSet_RAW.combine_first(oSectionDSet_SUBSET)

                                        # Store into common dataframe
                                        oSectionDF_SEL[sVarNameTS_SEL] = oSectionDSet_COMBINE[sVarNameTS_SEL]
                                        oSectionATTR_SEL[sVarNameTS_SEL] = oSectionData_ATTRIBUTES

                                # ------------------------------------------------------------------------------------

                            elif sVarDims == 'var1d':

                                # ------------------------------------------------------------------------------------
                                # Get variable data
                                oSectionTS_SEL = oVarData_WS.loc[sSectionName, :]
                                oSectionName_SEL = oSectionTS_SEL.indexes['name']

                                # Get variable attributes
                                oVarUnits_SEL = checkVarField(oVarUnits, oSectionName_SEL.__len__())
                                oVarScaleFactor_SEL = checkVarField(oVarScaleFactor, oSectionName_SEL.__len__())
                                oVarMissingValue_SEL = checkVarField(oVarMissingValue, oSectionName_SEL.__len__())
                                oVarValidRange_SEL = checkVarField(oVarValidRange, oSectionName_SEL.__len__())
                                oVarFillValue_SEL = checkVarField(oVarFillValue, oSectionName_SEL.__len__())
                                oVarArgs_SEL = checkVarField(oVarArgs, oSectionName_SEL.__len__(),
                                                             oListKeys=[sVarDims, sVarTypeData])

                                # Check variable data
                                if oSectionTS_SEL is not None:

                                    # Iterate over data
                                    for iSectionTS_ID, sSectionTS_TYPE in enumerate(list(oSectionName_SEL)):

                                        # Set section data attribute(s)
                                        oSectionData_ATTRIBUTES = mergeDict(
                                            {'units': oVarUnits_SEL[iSectionTS_ID],
                                             'ScaleFactor': oVarScaleFactor_SEL[iSectionTS_ID],
                                             'Missing_value': oVarMissingValue_SEL[iSectionTS_ID],
                                             'Valid_range': oVarValidRange_SEL[iSectionTS_ID],
                                             '_FillValue': oVarFillValue_SEL[iSectionTS_ID]},
                                            oVarAttributes)

                                        # Get data section (and combine to fit time steps) and set attribute(s)
                                        oSectionDArray_SUBSET = oLibCmpTS.combineVarDataArray(
                                            oSectionTS_SEL, sSectionTS_TYPE, oVarTime_PERIOD)

                                        # Store data in a default data array
                                        oSectionDF_SEL[sSectionTS_TYPE] = oSectionDArray_SUBSET
                                        oSectionATTR_SEL[sSectionTS_TYPE] = oSectionData_ATTRIBUTES

                                # ------------------------------------------------------------------------------------

                            # ------------------------------------------------------------------------------------
                            # Store data and attributes in a common workspace
                            if oSectionDF_SEL is not None:
                                if sVarSourceData not in oSectionData_WS[sSectionName]:
                                    # Data
                                    oSectionData_WS[sSectionName][sVarSourceData] = {}
                                    oSectionData_WS[sSectionName][sVarSourceData] = oSectionDF_SEL
                                    # Attributes
                                    oSectionAttrs_WS[sSectionName][sVarSourceData] = {}
                                    oSectionAttrs_WS[sSectionName][sVarSourceData] = oSectionATTR_SEL

                            # Info end
                            oLogStream.info(' ----> Analysis time-series data for section ' +
                                            sSectionName + ' ... DONE!')
                            # ------------------------------------------------------------------------------------

                        else:
                            # ------------------------------------------------------------------------------------
                            # Info error
                            oLogStream.info(' ----> Analysis time-series data for section ' +
                                            sSectionName + ' ... SKIPPED!')
                            Exc.getExc(' =====> WARNING: section ancillary file not found', 2, 1)
                            # ------------------------------------------------------------------------------------

                    # ------------------------------------------------------------------------------------
                    # Info of buffering dataset
                    oLogStream.info(' ---> Analyzing -- Group: ' + sVarSourceData + ' ... DONE')
                    # ------------------------------------------------------------------------------------
                else:
                    # ------------------------------------------------------------------------------------
                    # Info of buffering dataset
                    oLogStream.info(' ---> Analyzing -- Group: ' + sVarSourceData + ' ... SKIPPED')
                    Exc.getExc(' =====> WARNING: selected data are null!', 2, 1)
                    # ------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        oVarDataTS_WS = {'data': oSectionData_WS, 'attributes': oSectionAttrs_WS}
        return oVarDataTS_WS
        # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to finalize data analysis
class DataAnalysisFinalizer:

    # -------------------------------------------------------------------------------------
    # Class declaration(s)
    oVarCM = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):

        # Set argument(s)
        self.oVarBuffer = kwargs['settings']['buffer']
        self.oVarTimeRun = kwargs['time_run']
        self.oVarTimePeriod = kwargs['time_period']
        self.oVarDef = kwargs['settings']['variables']['outcome']
        self.oVarSource = kwargs['file']
        self.oVarMapping = kwargs['mapping']
        self.oVarTags = kwargs['tags']

        self.oVarWorkspace_TS = kwargs['data_ts']
        self.oVarWorkspace_GRIDDED = kwargs['data_gridded']

        # Map file(s)
        self.oVarFile, self.oVarBaseName, self.oVarMemory = fileMapping(
            self.oVarSource, self.oVarMapping, self.oVarTags)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to save data
    def saveDataAnalysis(self, oVarDataDynamic, oVarData_SECTION=None, oVarData_GEO=None):

        # -------------------------------------------------------------------------------------
        # Get global declaration(s)
        oVarDef = self.oVarDef
        oVarWorkspace_TS = self.oVarWorkspace_TS
        oVarWorkspace_GRIDDED = self.oVarWorkspace_GRIDDED
        oVarTime_RUN = self.oVarTimeRun

        if oVarDataDynamic:
            oVarFile_MAP = oVarDataDynamic['memory_file_variable']
        else:
            Exc.getExc(' =====> WARNING: data dynamic source information not found! Default values set!'
                       'Errors could occur during experiment!', 2, 1)
            oVarFile_MAP = self.oVarFile

        # Set progress bar widget(s)
        oVarPBarWidgets = [
            ' ===== Saving data progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over dataset(s)
        oVarPBarObj = progressbar.ProgressBar(widgets=oVarPBarWidgets, redirect_stdout=True)
        for sVarKey, oVarFields in oVarPBarObj(oVarDef.items()):

            # DEBUG
            # sVarKey = "data_product_ts" # OK
            # sVarKey = "data_product_gridded" # OK
            # oVarFields = oVarDef[sVarKey]
            # DEBUG

            # -------------------------------------------------------------------------------------
            # Get number of variable(s)
            iVarN = oVarFields['id']['var_file_in'].__len__()

            # Get variable information
            oVarDims = checkVarField(oVarFields['id']['var_dims'], iVarN)
            oVarTypeData = checkVarField(oVarFields['id']['var_type_data'], iVarN)
            oVarFileSource = checkVarField(oVarFields['id']['var_file_in'], iVarN)
            oVarFileOutcome = checkVarField(oVarFields['id']['var_file_out'], iVarN)
            oVarFileCMap = checkVarField(oVarFields['id']['var_file_colormap'], iVarN)
            oVarMethodName = checkVarField(oVarFields['id']['var_method_save_name'], iVarN)
            oVarArgs = checkVarField(oVarFields['id']['var_args'], iVarN, oListKeys=[oVarDims[0], oVarTypeData[0]])

            [oVarDims, oVarTypeData,
             oVarFileSource, oVarFileOutcome, oVarFileCMap, oVarMethodName, oVarArgs] = reduceList(
                {'list1': oVarDims, 'list2': oVarTypeData, 'list3': oVarFileSource, 'list4': oVarFileOutcome,
                 'list5': oVarFileCMap, 'list6': oVarMethodName, 'list7': oVarArgs}).values()

            # Define save filename
            oFileTags_SAVE_GENERIC = {
                '$yyyy': str(oVarTime_RUN.year).zfill(4),
                '$mm': str(oVarTime_RUN.month).zfill(2),
                '$dd': str(oVarTime_RUN.day).zfill(2),
                '$HH': str(oVarTime_RUN.hour).zfill(2),
                '$MM': str(oVarTime_RUN.minute).zfill(2),
            }
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Select product type
            if sVarKey == 'data_product_ts':

                # -------------------------------------------------------------------------------------
                # Get data and attributes from global workspace
                oVarData_TS = oVarWorkspace_TS['data']
                oVarAttr_TS = oVarWorkspace_TS['attributes']
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Iterate over section(s)
                for iSectionID, oSectionData in enumerate(oVarData_SECTION.iterrows()):

                    # -------------------------------------------------------------------------------------
                    # Get section info
                    oSectionInfo = oSectionData[1]
                    sSectionName = oSectionInfo['OUTLET_NAME']

                    # Define save filename
                    oFileTags_SECTION = mergeDict(oFileTags_SAVE_GENERIC, {"$section": sSectionName})

                    # Get section data and attribute(s)
                    oVarData_SECTION = oVarData_TS[sSectionName]
                    oVarAttr_SECTION = oVarAttr_TS[sSectionName]

                    # Info start
                    oLogStream.info(' ----> Save time-series data for section ' + sSectionName + ' ... ')
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Iterate over file data
                    for sVarDims, sVarTypeData, \
                        sVarFileSource, sVarFileOutcome, sVarFileCMap, \
                        sVarMethodName, sVarArgs in zip(oVarDims, oVarTypeData,
                                                        oVarFileSource, oVarFileOutcome, oVarFileCMap,
                                                        oVarMethodName, oVarArgs):

                        # -------------------------------------------------------------------------------------
                        # Define in/out filename(s)
                        sVarFileSource_IN_GROUP = sVarFileSource
                        sVarFileName_OUT_GROUP, sVarFileZipExt_OUT_GROUP = removeExtZip(defineString(deepcopy(
                            oVarFile_MAP[sVarFileOutcome]), oFileTags_SECTION))

                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Info group start
                        oLogStream.info(' -----> Save group ' + sVarFileSource_IN_GROUP + ' ... ')

                        # Check group name in data workspace
                        if sVarFileSource_IN_GROUP in oVarData_SECTION:

                            # -------------------------------------------------------------------------------------
                            # Get data and attributes for group
                            oVarDSet_GROUP = oVarData_SECTION[sVarFileSource_IN_GROUP].to_xarray()
                            oVarAttr_GROUP = oVarAttr_SECTION[sVarFileSource_IN_GROUP]
                            
                            # Create output file (if needed)
                            if not isfile(sVarFileName_OUT_GROUP):
                                # Create folder for data buffered
                                createFolderByFile(sVarFileName_OUT_GROUP)
                                sFileMode_GROUP = 'w'
                            else:
                                sFileMode_GROUP = 'a'
                            
                            # Write data to output file in netcdf format
                            writeFileNC4(sVarFileName_OUT_GROUP, oVarDSet_GROUP, oVarAttr_GROUP,
                                         sVarGroup=sVarFileSource_IN_GROUP, sVarMode=sFileMode_GROUP,
                                         oVarEngine='h5netcdf')

                            # Info group end
                            oLogStream.info(' -----> Save group ' + sVarFileSource_IN_GROUP + ' ... DONE')
                            # -------------------------------------------------------------------------------------
                        else:
                            # -------------------------------------------------------------------------------------
                            # Info group end
                            oLogStream.info(' -----> Save group ' + sVarFileSource_IN_GROUP + ' ... SKIPPED')
                            Exc.getExc(' =====> WARNING: group not available in data section', 2, 1)
                            # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Check file time-series availability
                    if exists(sVarFileName_OUT_GROUP):

                        # -------------------------------------------------------------------------------------
                        # Open zip driver
                        oZipDriver = Drv_Data_Zip(sVarFileName_OUT_GROUP, 'z',
                                                  None, sVarFileZipExt_OUT_GROUP).oFileWorkspace
                        [oFile_ZIP, oFile_UNZIP] = oZipDriver.oFileLibrary.openZip(
                            oZipDriver.sFileName_IN, oZipDriver.sFileName_OUT, oZipDriver.sZipMode)
                        oZipDriver.oFileLibrary.zipFile(oFile_ZIP, oFile_UNZIP)
                        oZipDriver.oFileLibrary.closeZip(oFile_ZIP, oFile_UNZIP)

                        # Delete unzip file
                        deleteFileName(sVarFileName_OUT_GROUP)

                        # Info end
                        oLogStream.info(' ----> Save time-series data for section ' + sSectionName + ' ... DONE')
                        # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Info end
                        oLogStream.info(' ----> Save time-series data for section ' + sSectionName + ' ... SKIPPED')
                        Exc.getExc(' =====> WARNING: file is not available. All data are null!', 2, 1)
                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------

            elif sVarKey == 'data_product_gridded':

                # -------------------------------------------------------------------------------------
                # Get data and attributes from global workspace
                oVarData_GRIDDED = oVarWorkspace_GRIDDED['data']
                oVarAttr_GRIDDED = oVarWorkspace_GRIDDED['attributes']
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Info start
                oLogStream.info(' ----> Save gridded data ... ')

                # Iterate over file data
                for sVarDims, sVarTypeData, \
                    sVarFileSource, sVarFileOutcome, sVarFileCMap, \
                    sVarMethodName, sVarArgs in zip(oVarDims, oVarTypeData,
                                                    oVarFileSource, oVarFileOutcome, oVarFileCMap,
                                                    oVarMethodName, oVarArgs):

                    # -------------------------------------------------------------------------------------
                    # Define in/out filename(s)
                    sVarFileSource_IN_GROUP = sVarFileSource
                    sVarFileName_OUT_GROUP, sVarFileZipExt_OUT_GROUP = removeExtZip(defineString(deepcopy(
                        oVarFile_MAP[sVarFileOutcome]), oFileTags_SAVE_GENERIC))
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info group start
                    oLogStream.info(' -----> Save group ' + sVarFileSource_IN_GROUP + ' ... ')

                    # Check group name in data workspace
                    if sVarFileSource_IN_GROUP in oVarData_GRIDDED:

                        # -------------------------------------------------------------------------------------
                        # Get data file
                        oVarDSet_GROUP = oVarData_GRIDDED[sVarFileSource_IN_GROUP]
                        oVarAttr_GROUP = oVarAttr_GRIDDED[sVarFileSource_IN_GROUP]

                        # Create output file (if needed)
                        if not isfile(sVarFileName_OUT_GROUP):
                            # Create folder for data buffered
                            createFolderByFile(sVarFileName_OUT_GROUP)
                            sFileMode_GROUP = 'w'
                        else:
                            sFileMode_GROUP = 'a'

                        # Write data to output file in netcdf format
                        writeFileNC4(sVarFileName_OUT_GROUP, oVarDSet_GROUP, oVarAttr_GROUP,
                                     sVarGroup=sVarFileSource_IN_GROUP, sVarMode=sFileMode_GROUP,
                                     oVarEngine='h5netcdf')

                        # Info group end
                        oLogStream.info(' -----> Save group ' + sVarFileSource_IN_GROUP + ' ... DONE')
                        # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Info group end
                        oLogStream.info(' -----> Save group ' + sVarFileSource_IN_GROUP + ' ... SKIPPED')
                        Exc.getExc(' =====> WARNING: group not available in data section', 2, 1)
                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Check file time-series availability
                if exists(sVarFileName_OUT_GROUP):

                    # -------------------------------------------------------------------------------------
                    # Open zip driver
                    oZipDriver = Drv_Data_Zip(sVarFileName_OUT_GROUP, 'z',
                                              None, sVarFileZipExt_OUT_GROUP).oFileWorkspace
                    [oFile_ZIP, oFile_UNZIP] = oZipDriver.oFileLibrary.openZip(
                        oZipDriver.sFileName_IN, oZipDriver.sFileName_OUT, oZipDriver.sZipMode)
                    oZipDriver.oFileLibrary.zipFile(oFile_ZIP, oFile_UNZIP)
                    oZipDriver.oFileLibrary.closeZip(oFile_ZIP, oFile_UNZIP)

                    # Delete unzip file
                    deleteFileName(sVarFileName_OUT_GROUP)

                    # Info end
                    oLogStream.info(' ----> Save gridded data ... DONE')
                    # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Info end
                    oLogStream.info(' ----> Save gridded data ... SKIPPED')
                    Exc.getExc(' =====> WARNING: file is not available. All data are null!', 2, 1)
                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to build data analysis
class DataAnalysisBuilder:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        # Set argument(s)
        self.oVarBuffer = kwargs['settings']['buffer']
        self.oVarTimeRun = kwargs['time_run']
        self.oVarTimePeriod = kwargs['time_period']
        self.oVarDef = kwargs['settings']['variables']['source']
        self.oVarSource = kwargs['file']
        self.oVarMapping = kwargs['mapping']
        self.oVarTags = kwargs['tags']

        # Map file(s)
        self.oVarFile, self.oVarBaseName, self.oVarMemory = fileMapping(
            self.oVarSource, self.oVarMapping, self.oVarTags)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get data
    def getDataAnalysis(self, oLandData, oPointData):

        # -------------------------------------------------------------------------------------
        # Get global declaration(s)
        oVarDef = self.oVarDef
        oVarFile_MAP = self.oVarFile
        oVarBaseName_MAP = self.oVarBaseName
        oVarUpd_MAP = self.oVarMemory
        oVarTime_RUN = self.oVarTimeRun
        oVarTime_PERIOD = self.oVarTimePeriod

        # Get buffer data information
        iVarTime_STORE_MAX = self.oVarBuffer['subset_max_step']
        sVarTime_STORE_FORMAT = self.oVarBuffer['subset_format']

        # Create indexes to chunk list (for buffering data)
        iVarTime_IDX = oVarTime_PERIOD.get_loc(oVarTime_RUN, method="nearest") + 1
        oVarTime_PERIOD_OBS = oVarTime_PERIOD[0:iVarTime_IDX]
        oVarTime_PERIOD_FOR = oVarTime_PERIOD[iVarTime_IDX:]
        oVarIdx_PERIOD = chunkList(oVarTime_PERIOD, iVarTime_STORE_MAX)

        # Get temporary folder
        if 'temp' in self.oVarSource:
            sVarFolder_TMP = self.oVarSource['temp']
        else:
            sVarFolder_TMP = None

        # Set progress bar widget(s)
        oVarPBarWidgets = [
            ' ===== Getting data progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over dataset(s)
        oVarWS_INFO = {}
        oVarPBarObj = progressbar.ProgressBar(widgets=oVarPBarWidgets, redirect_stdout=True)
        oVarWS_STORE_STEP = None
        oDatasetTime_MAP = None
        for sVarKey, oVarFields in oVarPBarObj(oVarDef.items()):

            # DEBUG
            # sVarKey = "data_result_ts_discharge_ws" # OK
            # sVarKey = "data_obs_ts_discharge" # OK
            # sVarKey = "data_obs_gridded_forcing" # OK
            # sVarKey = "data_result_gridded_outcome" # OK
            # sVarKey = "data_forecast_gridded_forcing_probabilistic_ecmwf" # OK
            # sVarKey = "data_forecast_gridded_forcing_deterministic_ecmwf" # OK
            # sVarKey = "data_result_ts_discharge_probabilistic_ecmwf" # OK
            # sVarKey = "data_result_ts_discharge_deterministic_ecmwf"  # OK
            # sVarKey = "data_forecast_gridded_forcing_deterministic_lami"
            # sVarKey = "data_forecast_gridded_forcing_probabilistic_lami"
            # sVarKey = "data_result_ts_discharge_deterministic_lami" # OK
            # sVarKey = "data_result_ts_discharge_probabilistic_lami" # OK
            # sVarKey = "data_test_nodata" # OK
            # oVarFields = oVarDef[sVarKey]
            # DEBUG

            # -------------------------------------------------------------------------------------
            # Get number of variable(s)
            iVarN = oVarFields['id']['var_name_in'].__len__()

            # Get input variable information
            oVarDims = checkVarField(oVarFields['id']['var_dims'], iVarN)
            oVarTypeData = checkVarField(oVarFields['id']['var_type_data'], iVarN)
            oVarTypeAncillary = checkVarField(oVarFields['id']['var_type_ancillary'], iVarN)
            oVarTypeExp = checkVarField(oVarFields['id']['var_type_experiment'], iVarN)
            oVarNameSource = checkVarField(oVarFields['id']['var_name_in'], iVarN)
            oVarNameOutcome = checkVarField(oVarFields['id']['var_name_out'], iVarN)
            oVarSourceData = checkVarField(oVarFields['id']['var_file_data'], iVarN)
            oVarSourceAncillary = checkVarField(oVarFields['id']['var_file_ancillary'], iVarN)
            oVarSourceFormat = checkVarField(oVarFields['id']['var_file_format'], iVarN)
            oVarMethodName = checkVarField(oVarFields['id']['var_method_get_name'], iVarN)
            oVarArgs = checkVarField(oVarFields['id']['var_args'], iVarN, oListKeys=[oVarDims[0], oVarTypeData[0]])

            [oVarDims, oVarTypeData, oVarTypeAncillary, oVarTypeExp,
             oVarSourceData, oVarSourceAncillary, oVarSourceFormat, oVarMethodName] = reduceList(
                {'list1': oVarDims, 'list2': oVarTypeData, 'list3': oVarTypeAncillary,
                 'list4': oVarTypeExp,
                 'list5': oVarSourceData, 'list6': oVarSourceAncillary,
                 'list7': oVarSourceFormat, 'list8': oVarMethodName}).values()
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Iterate over variable(s)
            for iVarID, (sVarDims, sVarTypeData, sVarTypeAncillary, sVarTypeExp, sVarSourceData, sVarSourceAncillary,
                         sVarSourceFormat, sVarMethodName, oVarArg) in \
                    enumerate(zip(oVarDims, oVarTypeData, oVarTypeAncillary, oVarTypeExp,
                                  oVarSourceData, oVarSourceAncillary,
                                  oVarSourceFormat, oVarMethodName, oVarArgs)):

                # -------------------------------------------------------------------------------------
                # Info of buffering dataset
                oLogStream.info(' ---> Buffering -- Group: ' + sVarSourceData + ' ... ')
                
                # Method to define variable settings
                oVarSettings = setVarSettings(sVarDims, sVarTypeData, oVarArg, oVarTime_PERIOD_OBS, oVarTime_PERIOD_FOR)

                # Define ensemble based on variable info
                oDatasetEns_REF_SUBPERIOD = setVarEnsemble(
                    sVarTypeData, oVarSettings,
                    [checkVarName('ensemble_n', oVarArgs_Valid)[0],
                     checkVarName("ensemble_format", oVarArgs_Valid)[0]])

                # Define time step based on effective data available on variable path
                oDatasetTime_MAP, oVarFile_MAP, oVarUpd_MAP = setDatasetTime_Finder(
                    oVarTime_RUN,
                    sVarTypeData, sVarTypeAncillary, sVarSourceData, sVarSourceAncillary,
                    oVarFile_MAP, oVarBaseName_MAP, oVarUpd_MAP, oDatasetTime_MAP,
                    oVarSRC_ENSEMBLE=oDatasetEns_REF_SUBPERIOD)

                # Define data chunks based subset info
                [oVarTime_RUN_SUBPERIOD, oVarTime_REF_SUBPERIOD,
                 oVarIdx_REF_SUBPERIOD, oVarTime_RUN_RANGE] = setVarChunk(
                    oVarTime_RUN, oDatasetTime_MAP[sVarSourceData],
                    oVarTime_PERIOD,
                    oVarIdx_PERIOD,
                    sVarTypeData,
                    oVarSettings)

                # Define time step based on variable info
                oDatasetTime_REF_SUBPERIOD = setDatasetTime_Steps(
                    sVarTypeData, oVarSettings,
                    oVarTime_REF_SUBPERIOD,
                    [checkVarName('data_period', oVarArgs_Valid)[0],
                     checkVarName("data_frequency", oVarArgs_Valid)[0]])
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Iterate over times
                oVarFile_STORE_BUFFER = None
                oVarFile_STORE_STEP = None
                oVarTime_STORE_STEP = None
                oVarIdx_STORE_STEP = None
                iVarTime_STORE_STEP = 0
                for iVarTime_STEP, (oVarTime_RUN_STEP, oVarTime_REF_STEP, iVarIdx_REF_STEP, oDatasetTime_REF_STEP) in \
                        enumerate(zip(oVarTime_RUN_SUBPERIOD,
                                      oVarTime_REF_SUBPERIOD, oVarIdx_REF_SUBPERIOD, oDatasetTime_REF_SUBPERIOD)):

                    # -------------------------------------------------------------------------------------
                    # Get generic dataset filename(s)
                    sVarFileName_STEP = oVarFile_MAP[sVarSourceData]
                    sVarFileName_BUFFER = oVarFile_MAP['file_buffer_source_data']
                    oDatasetTime_RUN = oDatasetTime_MAP[sVarSourceData]

                    # Save information of dataset(s)
                    if sVarSourceData not in oVarWS_INFO:
                        oVarWS_INFO[sVarSourceData] = {}
                        oVarWS_INFO[sVarSourceData]['variable_id'] = iVarID
                        oVarWS_INFO[sVarSourceData]['variable_dims'] = sVarDims
                        oVarWS_INFO[sVarSourceData]['variable_type_data'] = sVarTypeData
                        oVarWS_INFO[sVarSourceData]['variable_type_ancillary'] = sVarTypeAncillary
                        oVarWS_INFO[sVarSourceData]['variable_type_experiment'] = sVarTypeExp
                        oVarWS_INFO[sVarSourceData]['variable_source_data'] = sVarSourceData
                        oVarWS_INFO[sVarSourceData]['variable_source_ancillary'] = sVarSourceAncillary
                        oVarWS_INFO[sVarSourceData]['time_dataset'] = oDatasetTime_RUN
                        oVarWS_INFO[sVarSourceData]['time_run'] = oVarTime_RUN
                        oVarWS_INFO[sVarSourceData]['memory_time_dataset'] = oDatasetTime_MAP
                        oVarWS_INFO[sVarSourceData]['memory_file_variable'] = oVarFile_MAP
                        oVarWS_INFO[sVarSourceData]['memory_upd_variable'] = oVarUpd_MAP

                    # Chunk element
                    sVarIdx_REF_STEP = sVarTime_STORE_FORMAT.format(iVarIdx_REF_STEP)
                    if oVarIdx_STORE_STEP is None:
                        oVarIdx_STORE_STEP = [iVarIdx_REF_STEP]
                    else:
                        oVarIdx_STORE_STEP.append(iVarIdx_REF_STEP)

                    # Define file tags according with data type
                    if sVarTypeData == 'observed':
                        # Define tags using time step(s) according with time run
                        oFileTags_STEP = {
                            '$yyyy': str(oVarTime_REF_STEP.year).zfill(4),
                            '$mm': str(oVarTime_REF_STEP.month).zfill(2),
                            '$dd': str(oVarTime_REF_STEP.day).zfill(2),
                            '$HH': str(oVarTime_REF_STEP.hour).zfill(2),
                            '$MM': str(oVarTime_REF_STEP.minute).zfill(2),
                        }

                    elif sVarTypeData == 'result':
                        # Define tags using time step(s) according with time run
                        oFileTags_STEP = {
                            '$yyyy': str(oVarTime_REF_STEP.year).zfill(4),
                            '$mm': str(oVarTime_REF_STEP.month).zfill(2),
                            '$dd': str(oVarTime_REF_STEP.day).zfill(2),
                            '$HH': str(oVarTime_REF_STEP.hour).zfill(2),
                            '$MM': str(oVarTime_REF_STEP.minute).zfill(2),
                        }

                    elif sVarTypeData == 'forecast':
                        # Define tags using time step(s) according with time dataset
                        oFileTags_STEP = {
                            '$yyyy': str(oDatasetTime_RUN.year).zfill(4),
                            '$mm': str(oDatasetTime_RUN.month).zfill(2),
                            '$dd': str(oDatasetTime_RUN.day).zfill(2),
                            '$HH': str(oDatasetTime_RUN.hour).zfill(2),
                            '$MM': str(oDatasetTime_RUN.minute).zfill(2)
                        }

                    # Define buffer tags
                    oFileTags_BUFFER = {
                        '$yyyy': str(oVarTime_RUN.year).zfill(4),
                        '$mm': str(oVarTime_RUN.month).zfill(2),
                        '$dd': str(oVarTime_RUN.day).zfill(2),
                        '$HH': str(oVarTime_RUN.hour).zfill(2),
                        '$MM': str(oVarTime_RUN.minute).zfill(2),
                        '$subset': sVarIdx_REF_STEP
                    }
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Define step filename(s) and source and outcome variable(s)
                    oVarFileName_STEP = None
                    oVarNameSource_STEP = None
                    oVarNameOutcome_STEP = None

                    # Choose deterministic or probabilistic data
                    if oDatasetEns_REF_SUBPERIOD is not None:

                        # Select probabilistic case
                        for sDatasetEns in oDatasetEns_REF_SUBPERIOD:

                            if oVarFileName_STEP is None:
                                oVarFileName_STEP = []
                            if oVarNameSource_STEP is None:
                                oVarNameSource_STEP = []
                            if oVarNameOutcome_STEP is None:
                                oVarNameOutcome_STEP = []

                            oVarFileName_STEP.append(defineString(
                                deepcopy(sVarFileName_STEP), mergeDict(oFileTags_STEP, {'$ensemble': sDatasetEns})))

                            oVarNameSource_STEP.append(oVarNameSource[0])
                            for sVarNameOutcome in oVarNameOutcome:
                                if not oVarNameOutcome_STEP:
                                    oVarNameOutcome_STEP = [defineString(sVarNameOutcome, {'$ensemble': sDatasetEns})]
                                else:
                                    oVarNameOutcome_STEP.append(
                                        defineString(sVarNameOutcome, {'$ensemble': sDatasetEns}))

                    else:

                        # Select deterministic case
                        if (sVarDims == 'var2d') or (sVarDims == 'var3d'):
                            # Variable 2D or 3D
                            oVarFileName_STEP = [defineString(deepcopy(sVarFileName_STEP), oFileTags_STEP)]
                            oVarNameSource_STEP = oVarNameSource
                            oVarNameOutcome_STEP = oVarNameOutcome
                        elif sVarDims == 'var1d':
                            # Variable 1D
                            oVarFileName_STEP = [defineString(deepcopy(sVarFileName_STEP), oFileTags_STEP)]
                            oVarNameSource_STEP = [oVarNameSource[iVarID]]
                            oVarNameOutcome_STEP = [oVarNameOutcome[iVarID]]

                    # Define buffer filename
                    oVarFileName_BUFFER = [defineString(deepcopy(sVarFileName_BUFFER), oFileTags_BUFFER)]
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Define store buffer filename(s)
                    if oVarFile_STORE_BUFFER is None:
                        oVarFile_STORE_BUFFER = oVarFileName_BUFFER
                    else:
                        oVarFile_STORE_BUFFER = oVarFile_STORE_BUFFER + oVarFileName_BUFFER

                    # Define store step filename(s)
                    if oVarFile_STORE_STEP is None:
                        oVarFile_STORE_STEP = oVarFileName_STEP
                    else:
                        oVarFile_STORE_STEP = oVarFile_STORE_STEP + oVarFileName_STEP

                    # Define store step time(s)
                    if oVarTime_STORE_STEP is None:
                        oVarTime_STORE_STEP = [oVarTime_RUN_STEP]
                    else:
                        oVarTime_STORE_STEP = oVarTime_STORE_STEP + [oVarTime_RUN_STEP]
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Define store step information
                    oVarWS_STEP = [iVarTime_STEP, iVarIdx_REF_STEP, oVarTime_STORE_STEP,
                                   sVarIdx_REF_STEP, oVarTime_REF_STEP, oVarFileName_STEP, oVarFileName_BUFFER]
                    if oVarWS_STORE_STEP is None:
                        oVarWS_STORE_STEP = [oVarWS_STEP]
                    else:
                        oVarWS_STORE_STEP.append(oVarWS_STEP)
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Save data using buffer step(s)
                    if (iVarTime_STORE_STEP == iVarTime_STORE_MAX - 1) or \
                            iVarTime_STEP == oVarTime_RUN_SUBPERIOD.__len__() - 1:

                        # -------------------------------------------------------------------------------------
                        # Filter filename(s) and ind(x) to unique and sorted values
                        oVarIdx_STORE_STEP = sorted(list(set(oVarIdx_STORE_STEP)))
                        oVarFile_STORE_STEP = sorted(list(set(oVarFile_STORE_STEP)))
                        oVarFile_STORE_BUFFER = sorted(list(set(oVarFile_STORE_BUFFER)))
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Method to get gridded variable(s)
                        oVarObj_BUFFER = None
                        oFileObj_BUFFER = None
                        if sVarDims == 'var2d':

                            # -------------------------------------------------------------------------------------
                            # Define variable argument(s)
                            oFxArgs = {'oFileName': oVarFile_STORE_STEP,
                                       'oFileTime': oVarTime_STORE_STEP,
                                       'oFileVarsSource': oVarNameSource_STEP,
                                       'oFileVarsOutcome': oVarNameOutcome_STEP,
                                       'sFolderTmp': sVarFolder_TMP,
                                       'oDataGeo': oLandData}

                            # Compute variable data
                            oVarObj_BUFFER, oFileObj_BUFFER = configVarFx(sVarMethodName, oLibGridded, oFxArgs)
                            # -------------------------------------------------------------------------------------

                        elif sVarDims == 'var3d':

                            # -------------------------------------------------------------------------------------
                            # Define variable argument(s)
                            oFxArgs = {'oFileName': oVarFile_STORE_STEP,
                                       'oFileTime': oVarTime_STORE_STEP,
                                       'oFileVarsSource': oVarNameSource_STEP,
                                       'oFileVarsOutcome': oVarNameOutcome_STEP,
                                       'oDataTime': oDatasetTime_REF_STEP,
                                       'sFolderTmp': sVarFolder_TMP,
                                       'oDataGeo': oLandData}

                            # Compute variable data
                            oVarObj_BUFFER, oFileObj_BUFFER = configVarFx(sVarMethodName, oLibGridded, oFxArgs)
                            # -------------------------------------------------------------------------------------

                        elif sVarDims == 'var1d':

                            # -------------------------------------------------------------------------------------
                            # Define variable argument(s)
                            oVarField_STORE = list(oPointData[oVarSourcePoint_Valid[0]])
                            oVarID_STORE = list(oPointData[oVarSourcePoint_Valid[2]].values)

                            # Re-order name section according with observed and result file(s)
                            oVarField_STORE_ORDER_ID = [iX for _, iX in sorted(zip(oVarID_STORE, oVarField_STORE))]

                            if 'column_id' in oVarSettings:
                                if isinstance(oVarSettings['column_id'], list):
                                    iFileCol = oVarSettings['column_id'][0]
                                else:
                                    iFileCol = oVarSettings['column_id']
                            else:
                                iFileCol = 0

                            oVarFile_STORE_STEP = list(
                                divide_chunks(oVarFile_STORE_STEP, oVarTime_STORE_STEP.__len__()))

                            oFxArgs = {'oFileName': oVarFile_STORE_STEP,
                                       'oFileTime': oVarTime_STORE_STEP,
                                       'oFileVarsSource': oVarNameSource_STEP,
                                       'oFileVarsOutcome': oVarNameOutcome_STEP,
                                       'oFileField': oVarField_STORE_ORDER_ID,
                                       'iFileCol': iFileCol,
                                       'sFolderTmp': sVarFolder_TMP}

                            # Compute variable data
                            oVarObj_BUFFER, oFileObj_BUFFER = configVarFx(sVarMethodName, oLibPoint, oFxArgs)
                            # -------------------------------------------------------------------------------------

                        else:

                            # -------------------------------------------------------------------------------------
                            # Exit for error in defining variable dimensions
                            Exc.getExc(' =====> ERROR: selected variable dimensions are not defined', 1, 1)
                            # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Adapt data to time expected
                        oVarTime_STORE_DEL = None
                        oVarIdx_STORE_SAVE = sorted(list(set(oVarIdx_STORE_STEP)))
                        oVarFile_STORE_SAVE = sorted(list(set(oVarFile_STORE_BUFFER)))
                        for iVarIdx_STORE_SAVE, sVarFile_STORE_SAVE in zip(oVarIdx_STORE_SAVE, oVarFile_STORE_SAVE):

                            # -------------------------------------------------------------------------------------
                            # Info of chunk step
                            oLogStream.info(' ----> Buffering -- Chunk: ' + str(iVarIdx_STORE_SAVE) + ' ... ')

                            # Check buffered data availability
                            if oVarObj_BUFFER is not None:

                                # -------------------------------------------------------------------------------------
                                # Check buffer file available on disk
                                if not isfile(sVarFile_STORE_SAVE):
                                    # Create folder for data buffered
                                    createFolderByFile(sVarFile_STORE_SAVE)
                                    sFileMode_BUFFER = 'w'
                                    oVarDSET_STORE_SAVED = None
                                else:
                                    # Append data to an existent buffer file
                                    sFileMode_BUFFER = 'a'
                                    oVarDSET_STORE_SAVED = readFileNC4(sVarFile_STORE_SAVE, oVarGroup=sVarSourceData)

                                    if oVarDSET_STORE_SAVED[sVarSourceData] is not None:
                                        oVarDSET_STORE_SAVED = oVarDSET_STORE_SAVED[sVarSourceData]
                                    else:
                                        oVarDSET_STORE_SAVED = None
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Get index of chunks
                                a1iVarIdx_STORE_SAVE = \
                                    [iIdx for iIdx, iVal in enumerate(oVarIdx_PERIOD) if iVal == iVarIdx_STORE_SAVE]

                                # Get save and step time(s)
                                oVarTime_STORE_SAVE = oVarTime_PERIOD[a1iVarIdx_STORE_SAVE]
                                oVarTime_STORE_STEP = pd.DatetimeIndex(oVarTime_STORE_STEP)

                                # Combine variable(s) to save data in chunk file(s)
                                oVarDSET_COMBINE = None
                                if sVarDims == 'var1d':

                                    oVarDSET_COMBINE = oLibPoint.convertVarDFrame(oVarObj_BUFFER)

                                    if oVarTime_STORE_STEP.__len__() != oVarDSET_COMBINE.time.__len__():
                                        Exc.getExc(
                                            ' =====> WARNING: buffered data length for 1D var is not equal '
                                            'to expected times! Check your configuration file', 2, 1)
                                        oVarDSET_COMBINE = None

                                elif (sVarDims == 'var2d') or (sVarDims == 'var3d'):

                                    # Check for already processed time steps
                                    if oVarTime_STORE_DEL is not None:
                                        oVarTime_STORE_STEP = oVarTime_STORE_STEP.drop(oVarTime_STORE_DEL)

                                    # Create datetime index
                                    oVarTime_COMBINE_INTSEC = oVarTime_STORE_SAVE.intersection(oVarTime_STORE_STEP)
                                    # oVarTime_COMBINE_DIFFER = oVarTime_STORE_SAVE.difference(oVarTime_STORE_STEP)

                                    # Store empty dataset on expected time steps
                                    oVarDSET_COMBINE_BUFFER_EXPECTED = xr.Dataset(
                                        coords={'time': (['time'], pd.to_datetime(oVarTime_STORE_STEP))})
                                    # Fill empty dataset with collected dataset
                                    oVarDSET_COMBINE_BUFFER_FILLED = oVarDSET_COMBINE_BUFFER_EXPECTED.combine_first(
                                        oVarObj_BUFFER)

                                    # Selected dataset only on intersected time steps
                                    oVarDSET_COMBINE_BUFFER = oVarDSET_COMBINE_BUFFER_FILLED.sel(
                                        time=oVarTime_COMBINE_INTSEC)

                                    if oVarDSET_STORE_SAVED is not None:
                                        oVarDSET_COMBINE_BUFFER_FILL = oVarDSET_STORE_SAVED.combine_first(
                                            oVarDSET_COMBINE_BUFFER)
                                    else:
                                        oVarDSET_COMBINE_BUFFER_FILL = oVarDSET_COMBINE_BUFFER

                                    # Combine dataset with other chunked dataset (if needed)
                                    oVarDSET_COMBINE_CHUNK = xr.Dataset(
                                        coords={'time': (['time'], pd.to_datetime(oVarTime_STORE_SAVE))})
                                    oVarDSET_COMBINE = xr.auto_combine(
                                        [oVarDSET_COMBINE_CHUNK, oVarDSET_COMBINE_BUFFER_FILL], concat_dim='time')

                                    # Save times already processed
                                    oVarTime_STORE_DEL = oVarTime_COMBINE_INTSEC

                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Info of chunk time
                                oLogStream.info(' ----> Buffering -- Analysis period: ' +
                                                str(oVarTime_STORE_SAVE[0].strftime(format='%Y/%m/%d %H:%M')) +
                                                ' :: ' + str(oVarTime_STORE_SAVE[-1].strftime(format='%Y/%m/%d %H:%M')))

                                # Write or append data to netcdf buffered file
                                if oVarDSET_COMBINE is not None:

                                    writeFileNC4(sVarFile_STORE_SAVE, oVarDSET_COMBINE,
                                                 sVarGroup=sVarSourceData, sVarMode=sFileMode_BUFFER)

                                    # Info of chunk step
                                    oLogStream.info(
                                        ' ----> Buffering -- Chunk: ' + str(iVarIdx_STORE_SAVE) + ' ... DONE')
                                else:
                                    # Info of chunk step
                                    oLogStream.info(
                                        ' ----> Buffering -- Chunk: ' + str(iVarIdx_STORE_SAVE) + ' ... FAILED')
                                    Exc.getExc(
                                        ' =====> WARNING: buffered data are set to null! Check your settings!', 2, 1)
                                # -------------------------------------------------------------------------------------

                            else:

                                # -------------------------------------------------------------------------------------
                                # Info of chunk step
                                oLogStream.info(
                                    ' ----> Buffering -- Chunk: ' + str(iVarIdx_STORE_SAVE) + ' ... FAILED')
                                # Exit for warning in buffering data
                                Exc.getExc(
                                    ' =====> WARNING: buffered data are null! Check your settings!', 2, 1)
                                # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Delete temp filename(s) to save space in tmp folder (if not defined otherwise)
                        if oFileObj_BUFFER is not None:
                            for sFileObj_BUFFER in oFileObj_BUFFER:
                                if os.path.exists(sFileObj_BUFFER):
                                    os.remove(sFileObj_BUFFER)

                        # Re-initialize variable(s) and counter(s)
                        oVarFile_STORE_STEP = None
                        oVarTime_STORE_STEP = None
                        iVarTime_STORE_STEP = 0
                        oVarIdx_STORE_STEP = None
                        oVarFile_STORE_BUFFER = None
                        # -------------------------------------------------------------------------------------

                    else:

                        # -------------------------------------------------------------------------------------
                        # Counter(s)
                        iVarTime_STORE_STEP += 1
                        # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Info of buffering dataset
                oLogStream.info(' ---> Buffering -- Group: ' + sVarSourceData + ' ... DONE')
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Save global value of memory object(s)
        if 'memory_time_dataset' not in oVarWS_INFO:
            oVarWS_INFO['memory_time_dataset'] = oDatasetTime_MAP
        if 'memory_file_variable' not in oVarWS_INFO:
            oVarWS_INFO['memory_file_variable'] = oVarFile_MAP
        if 'memory_upd_variable' not in oVarWS_INFO:
            oVarWS_INFO['memory_upd_variable'] = oVarUpd_MAP

        # Return variable(s)
        return oVarWS_INFO
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to map file
def fileMapping(oVarSource, oVarMapping, oVarTags):
    oVarFile = {}
    oVarBaseName = {}
    oVarMemory = {}
    for sVarMapping_TAG, oVarMapping_NAMES in oVarMapping.items():
        for sVarMapping_NAME in oVarMapping_NAMES:
            sVarMapping_FILE_RAW = oVarSource[sVarMapping_NAME]
            sVarMapping_FILE_FILLED = defineString(sVarMapping_FILE_RAW, oVarTags)
            oVarFile[sVarMapping_NAME] = sVarMapping_FILE_FILLED
            oVarBaseName[sVarMapping_NAME] = sVarMapping_FILE_RAW
            oVarMemory[sVarMapping_NAME] = False
    return oVarFile, oVarBaseName, oVarMemory
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
def checkVarField(oVarList, iVarN, oListKeys=None):

    sCheckType = None
    if all(isinstance(oElem, str) for oElem in oVarList):
        sCheckType = 'str'
    elif all(isinstance(oElem, str) for oElem in oVarList):
        sCheckType = 'list'
    elif all(isinstance(oElem, dict) for oElem in oVarList):
        sCheckType = 'dict'
    else:
        sCheckType = 'other'

    if sCheckType == 'str':
        iListN = oVarList.__len__()
    if sCheckType == 'list':
        for iN, oVar in enumerate(oVarList):
            iListN = iN + 1
    if sCheckType == 'other':
        iListN = oVarList.__len__()
    if sCheckType == 'dict':
        oVarStore = {}
        for oVarDict in oVarList:
            oVarData = lookupDictKey(oVarDict, *oListKeys)
            for sVarKey, oVarDataStep in oVarData.items():
                iDataN = oVarDataStep.__len__()
                if iDataN != iVarN:
                    oVarDataN = oVarDataStep * iVarN
                else:
                    oVarDataN = oVarDataStep

                for iN, oVarDataSel in enumerate(oVarDataN):
                    if iN not in oVarStore.keys():
                        oVarStore[iN] = {}
                    oVarStore[iN][sVarKey] = [oVarDataSel]

        oVarList = []
        for oVarStoreKey, oVarStoreValue in oVarStore.items():
            oDictStore_STEP = {}
            for sListKey in oListKeys[::-1]:
                oDictStore_STEP = oDictStore_STEP.fromkeys([sListKey], oDictStore_STEP)
            oDictStore_STEP = setDictValue(oDictStore_STEP, oListKeys, oVarStoreValue)
            oVarList.append(oDictStore_STEP)

        return oVarList

    if iListN != iVarN:
        return [oVarList[0]] * iVarN
    else:
        return oVarList
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute chunks
def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to chuck list in spaced integer indexes
def chunkList(oList, iElemN, iElemIdx=0):

    oChunks = list(divide_chunks(oList, iElemN))

    oChunkIdx = None
    for oChunk in oChunks:
        iChunkDim = oChunk.__len__()
        oChunkList = [iElemIdx] * iChunkDim
        if oChunkIdx is None:
            oChunkIdx = oChunkList
        else:
            oChunkIdx = oChunkIdx + oChunkList

        iElemIdx += 1
    return oChunkIdx
# -------------------------------------------------------------------------------------
