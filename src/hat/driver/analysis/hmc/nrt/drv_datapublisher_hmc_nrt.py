"""
Library Features:

Name:          drv_datapublisher_hmc_nrt
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190213'
Version:       '1.0.2'
"""
#######################################################################################
# Library
import logging
import progressbar
import glob

import pandas as pd

from os import remove, listdir, rmdir
from os.path import exists, isfile, split, splitext
from copy import deepcopy
from numpy import full

from src.common.default.lib_default_args import sPathDelimiter as sPathDelimiter_Default

from src.common.utils.lib_utils_op_system import createFolderByFile
from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import mergeDict, lookupDictKey, setDictValue
from src.common.utils.lib_utils_op_list import reduceList, flatList

from src.hat.dataset.generic.lib_generic_io_method import writeFilePickle, appendFilePickle, readFilePickle
from src.hat.dataset.generic.lib_generic_io_utils import createDArray1D, mergeVar1D, clipVar1D, \
    createDArray2D, mergeVar2D, createStats1D, createStats2D
from src.hat.dataset.generic.lib_generic_io_apps import wrapFileReader, findVarName, findVarTag, createVarName

from src.hat.driver.analysis.hmc.nrt.cpl_datapublisher_hmc_nrt_dewetra import DataPublisher as DataPublisherDewetra
from src.hat.driver.analysis.hmc.nrt.cpl_datapublisher_hmc_nrt_hydrapp import DataPublisher as DataPublisherHydrapp

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Algorithm valid key(s)
oAppTags_Valid = ["dewetra", "hydrapp"]
oVarArgs_Valid = ["ensemble_n", "ensemble_format", "data_period", "data_frequency", "column_id"]
oVarSource_TypeData_Valid = ["observed", "forecast", "result", "analysis"]
oVarSource_TypeExperiment_Valid = ["deterministic", "probabilistic"]
oVarSourceFormat_Valid = ["ascii", "netcdf4"]
oVarSourcePoint_Valid = ['OUTLET_NAME', 'OUTLET_FILE_ANCILLARY']
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
            elif isinstance(oFile, list):
                oFile = flatList(oFile)

            for sFile in oFile:

                if sPathDelimiter_Default in sFile:

                    iN = sFile.count(sPathDelimiter_Default)
                    if iN == 1:
                        sFileRoot = sFile.split(sPathDelimiter_Default)[0]
                        sFileExt = splitext(sFile)[1]
                        sFileSearch = sFileRoot + '*' + sFileExt
                    elif iN > 1:
                        sFileRoot = sFile.split(sPathDelimiter_Default, 1)[0]
                        sFileExt = splitext(sFile)[1]
                        sFileSearch = sFileRoot + '*' + sFileExt
                    elif iN == 0:
                        sFileSearch = sFile
                    a1oFileSelect = glob.glob(sFileSearch)
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
        setattr(oTimeRange, 'time_corrivation', iTimeCorrivation)

        return oTimeRange

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to make data analysis
class DataAnalysisMaker:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, oAppTag, **kwargs):

        # Set argument(s)
        self.oAppTag = oAppTag
        self.oAppArgs = kwargs
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to select data analysis maker
    def selectDataAnalysisMaker(self, oDataInfo, oDataGeo, oDataSection):

        # -------------------------------------------------------------------------------------
        # Iterate over application(s)
        for sAppTag in self.oAppTag:

            # -------------------------------------------------------------------------------------
            # Info start
            oLogStream.info(' ----> Run application ' + sAppTag + ' ... ')
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Hydrapp coupler application
            if sAppTag == 'hydrapp':

                # -------------------------------------------------------------------------------------
                # Call application coupler
                try:
                    # Publish data
                    oDataMakerObj = DataPublisherHydrapp(sAppTag, self.oAppArgs)
                    oDataMakerRegistry = oDataMakerObj.publishData(oDataInfo, oDataGeo, oDataSection)
                    # Info end
                    oLogStream.info(' ----> Run application ' + sAppTag + ' ... DONE!')
                except Warning:
                    # Info for error(s) in running application
                    oDataMakerRegistry = None
                    oLogStream.info(' ----> Run application ' + sAppTag + ' ... FAILED!')
                    Exc.getExc(' =====> WARNING: in running application ' + sAppTag + ' some error(s) occurred!', 2, 1)

                # -------------------------------------------------------------------------------------

            # Dewetra coupler application
            elif sAppTag == 'dewetra':

                # -------------------------------------------------------------------------------------
                # Call application coupler
                try:
                    # Publish data
                    oDataMakerObj = DataPublisherDewetra(sAppTag, self.oAppArgs)
                    oDataMakerRegistry = oDataMakerObj.publishData(oDataInfo, oDataGeo, oDataSection)
                    # Info end
                    oLogStream.info(' ----> Run application ' + sAppTag + ' ... DONE!')
                except Warning:
                    # Info for error(s) in running application
                    oDataMakerRegistry = None
                    oLogStream.info(' ----> Run application ' + sAppTag + ' ... FAILED!')
                    Exc.getExc(' =====> WARNING: in running application ' + sAppTag + ' some error(s) occurred!', 2, 1)
                # -------------------------------------------------------------------------------------

            # Other not available application
            else:

                # -------------------------------------------------------------------------------------
                # Info for error in selecting application
                oDataMakerRegistry = None
                oLogStream.info(' ----> Run application ' + sAppTag + ' ... FAILED!')
                Exc.getExc(' =====> WARNING: application ' + sAppTag + ' is not available! Check your settings!', 2, 1)
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Return data publisher registry
            return oDataMakerRegistry
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to seek data analysis
class DataAnalysisSeeker:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, oAppTag, **kwargs):

        # Set argument(s)
        self.oAppTag = oAppTag
        self.oVarTimeSeek = kwargs['time_seek']
        self.oVarTimePeriod = kwargs['time_period']
        self.oVarDef = kwargs['settings']['analysis']
        self.oVarSource = kwargs['file']
        self.oVarMapping = kwargs['mapping']
        self.oVarTags = kwargs['tags']

        # Map file(s)
        self.oVarFile, self.oVarBaseName = fileMapping(self.oVarSource, self.oVarMapping, self.oVarTags)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to seek data
    def seekDataAnalysis(self, oDataPoint):

        # -------------------------------------------------------------------------------------
        # Get application(s) tag
        oAppTag = self.oAppTag
        # Iterate over application(s) tag
        oVarData_SEEK_WS = {}
        oVarData_SEEK_STATS = {}
        for sAppTag in oAppTag:

            # -------------------------------------------------------------------------------------
            # Info application
            oLogStream.info(' ----> Seeking data for application ' + sAppTag + ' ... ')
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check application tag validity
            if sAppTag in oAppTags_Valid:

                # Get global declaration(s)
                oVarDef = self.oVarDef[sAppTag]
                oVarFile = self.oVarFile
                oVarBaseName = self.oVarBaseName
                oVarTime_SEEK = self.oVarTimeSeek
                oVarTime_PERIOD = self.oVarTimePeriod
                oVarTags = self.oVarTags

                # Set progress bar widget(s)
                oVarPBarWidgets = [
                    ' ===== Seeking data progress: ', progressbar.Percentage(),
                    ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
                    ' ', progressbar.ETA(),
                ]

                # Store seeking step(s)
                oVarData_SEEK_WS[sAppTag] = {}
                oVarData_SEEK_STATS[sAppTag] = {}
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Iterate over dataset(s)
                oVarPBarObj = progressbar.ProgressBar(widgets=oVarPBarWidgets, redirect_stdout=True)
                for sVarKey, oVarFields in oVarPBarObj(oVarDef.items()):

                    # DEBUG
                    # sVarKey = "data_ts" # OK
                    # sVarKey = "data_gridded" # OK
                    # oVarFields = oVarDef[sVarKey]
                    # DEBUG

                    # -------------------------------------------------------------------------------------
                    # Get number of variable(s)
                    iVarN = oVarFields['id']['var_name_in'].__len__()

                    # Get variable information
                    oVarDims = checkVarField(oVarFields['id']['var_dims'], iVarN)
                    oVarTypeData = checkVarField(oVarFields['id']['var_type_data'], iVarN)
                    oVarTypeExp = checkVarField(oVarFields['id']['var_type_experiment'], iVarN)
                    oVarNameSource = checkVarField(oVarFields['id']['var_name_in'], iVarN)
                    oVarNameOutcome = checkVarField(oVarFields['id']['var_name_out'], iVarN)
                    oVarNameGroup = checkVarField(oVarFields['id']['var_name_group'], iVarN)
                    oVarFileTag = checkVarField(oVarFields['id']['var_file_tag'], iVarN)
                    oVarFileGroup = checkVarField(oVarFields['id']['var_file_group'], iVarN)
                    oVarFileAncillary = checkVarField(oVarFields['id']['var_file_ancillary'], iVarN)
                    oVarArgs = checkVarField(oVarFields['id']['var_args'], iVarN,
                                             oListKeys=[oVarDims[0], oVarTypeData[0]])

                    # Get variable attributes
                    oVarFigureDPI = checkVarField(oVarFields['attributes']['figure_dpi'], iVarN)

                    # Set list for reducing variable(s) sample size
                    [oVarDims, oVarTypeData, oVarTypeExp, oVarNameSource, oVarNameOutcome, oVarNameGroup,
                     oVarFileTag, oVarFileGroup] = reduceList(
                        {'list1': oVarDims, 'list2': oVarTypeData, 'list3': oVarTypeExp,
                         'list4': oVarNameSource, 'list5': oVarNameOutcome, 'list6': oVarNameGroup,
                         'list7': oVarFileTag, 'list8': oVarFileGroup
                         }).values()

                    # Store seeking step(s)
                    oVarData_SEEK_WS[sAppTag][sVarKey] = {}
                    oVarData_SEEK_STATS[sAppTag][sVarKey] = {}
                    # -------------------------------------------------------------------------------------

                    # DEBUG #
                    # sVarGroup = "file_forecast_gridded_forcing_deterministic_lami"
                    # iVarID = oVarFileGroup.index(sVarGroup)
                    # oVarDims = oVarDims[iVarID:]
                    # oVarTypeData = oVarTypeData[iVarID:]
                    # oVarTypeExp = oVarTypeExp[iVarID:]
                    # oVarNameSource = oVarNameSource[iVarID:]
                    # oVarNameOutcome = oVarNameOutcome[iVarID:]
                    # oVarNameGroup = oVarNameGroup[iVarID:]
                    # oVarFileTag = oVarFileTag[iVarID:]
                    # oVarFileGroup = oVarFileGroup[iVarID:]
                    # DEBUG

                    # -------------------------------------------------------------------------------------
                    # Iterate over variable(s)
                    for iVarID, (sVarDims, sVarTypeData, sVarTypeExp,
                                 sVarNameSource, sVarNameOutcome, sVarNameGroup,
                                 sVarFileTag, sVarFileAncillary, sVarFileGroup, oVarArg) in \
                            enumerate(zip(oVarDims, oVarTypeData, oVarTypeExp,
                                          oVarNameSource, oVarNameOutcome, oVarNameGroup,
                                          oVarFileTag, oVarFileAncillary, oVarFileGroup, oVarArgs)):

                        # -------------------------------------------------------------------------------------
                        # Info group
                        oLogStream.info(' -----> Seeking data for group ' + sVarFileGroup + ' ... ')
                        oVarPickle_SEEK = {}

                        # Store seeking step(s)
                        oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup] = {}
                        oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup] = {}
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Select using variable dimension(s)
                        if sVarDims == 'var1d':

                            # -------------------------------------------------------------------------------------
                            # Iterate over section(s)
                            oDataGenerator = oDataPoint.iterrows()

                            # DEBUG
                            # n = 12
                            # oDataGenerator = [next(x for i, x in enumerate(oDataGenerator) if i == n)]
                            # DEBUG

                            # Iterate over section(s)
                            for iSectionID, oSectionData in enumerate(oDataGenerator):

                                # -------------------------------------------------------------------------------------
                                # Get section info
                                oSectionInfo = oSectionData[1]
                                sSectionName = oSectionInfo['OUTLET_NAME']
                                sSectionFileAncillary = oSectionInfo['OUTLET_FILE_ANCILLARY']
                                # Info section
                                oLogStream.info(' ------> Seeking time-series data for section ' +
                                                sSectionName + ' ... ')

                                # Store seeking step(s)
                                oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup][sSectionName] = {}
                                oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup][sSectionName] = {}

                                # Declare variable list
                                oVarList_SEEK = None
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Check ancillary section file availability
                                oVarStats_SEEK = None
                                if isfile(sSectionFileAncillary):

                                    # -------------------------------------------------------------------------------------
                                    # Get generic dataset filename(s)
                                    sVarFileName_SEEK = deepcopy(oVarFile[sVarFileTag])
                                    sVarFileName_ANCILLARY = deepcopy(oVarFile[sVarFileAncillary])

                                    # Define file tags
                                    oFileTags_SEEK = {
                                        '$yyyy': str(oVarTime_SEEK.year).zfill(4),
                                        '$mm': str(oVarTime_SEEK.month).zfill(2),
                                        '$dd': str(oVarTime_SEEK.day).zfill(2),
                                        '$HH': str(oVarTime_SEEK.hour).zfill(2),
                                        '$MM': str(oVarTime_SEEK.minute).zfill(2),
                                        '$section': sSectionName,
                                        '$application': sAppTag
                                    }

                                    # Define seek filename (in zipped and unzipped format)
                                    sVarFileName_SEEK = defineString(sVarFileName_SEEK, mergeDict(
                                        oFileTags_SEEK, oVarTags))
                                    sVarFileName_ANCILLARY = defineString(sVarFileName_ANCILLARY, mergeDict(
                                        oFileTags_SEEK, oVarTags))
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Check file availability
                                    if isfile(sVarFileName_SEEK):

                                        # Get file data
                                        oVarDSet_SEEK = wrapFileReader(sVarFileName_SEEK, sVarFileGroup)

                                        # Condition to check if data is available for selected group
                                        if oVarDSet_SEEK is not None:

                                            # Find name(s) of input variable(s)
                                            oVarNameSource_SEEK = findVarName(list(oVarDSet_SEEK.data_vars), sVarNameSource)
                                            # Find tag(s) of input variable(s)
                                            oVarTagPattern_SEEK, oVarTagValue_SEEK = findVarTag(oVarNameSource_SEEK,
                                                                                                sVarNameSource)
                                            # Create name of output variable(s)
                                            oVarNameOutcome_SEEK = createVarName(sVarNameOutcome,
                                                                                 oVarTagPattern_SEEK, oVarTagValue_SEEK)
                                            # Create name of output variable(s)
                                            oVarNameGroup_SEEK = createVarName(sVarNameGroup,
                                                                               oVarTagPattern_SEEK, oVarTagValue_SEEK)

                                            # Clip data under defined condition (to avoid outliers)
                                            if (sVarTypeExp == 'probabilistic') and (sVarTypeData == 'result') \
                                                    and (sVarNameGroup == 'discharge'):
                                                oVarDSet_SEEK = clipVar1D(oVarDSet_SEEK)

                                            # Iterate over variable(s)
                                            for sVarNameSource_SEEK, sVarNameOutcome_SEEK, sVarNameGroup_SEEK in zip(
                                                    oVarNameSource_SEEK, oVarNameOutcome_SEEK, oVarNameGroup_SEEK):

                                                # Get variable data
                                                oVarDArray_SEEK = oVarDSet_SEEK[sVarNameSource_SEEK]
                                                oVarDArray_SEEK = createDArray1D(oVarDArray_SEEK, oVarTime_PERIOD,
                                                                                 sVarName_IN=sVarNameSource_SEEK,
                                                                                 sVarName_OUT=sVarNameOutcome_SEEK)
                                                # Create data array list
                                                vars()[sVarNameOutcome_SEEK] = oVarDArray_SEEK

                                                if oVarList_SEEK is None:
                                                    oVarList_SEEK = [vars()[sVarNameOutcome_SEEK]]
                                                else:
                                                    oVarList_SEEK.append(vars()[sVarNameOutcome_SEEK])

                                                # Delete variable(s) from vars()
                                                if sVarNameOutcome_SEEK in vars():
                                                    del vars()[sVarNameOutcome_SEEK]

                                                # Variable statistics
                                                if sVarNameGroup_SEEK != 'other':
                                                    oVarStats_SEEK = createStats1D(oVarStats_SEEK, oVarDArray_SEEK,
                                                                                   sVarNameGroup_SEEK)
                                            # -------------------------------------------------------------------------------------

                                            # -------------------------------------------------------------------------------------
                                            # Merge data in dataset object
                                            oVarDSet_SEEK = mergeVar1D(oVarList_SEEK)

                                            # Clip data under defined condition (to avoid outliers)
                                            #if (sVarTypeExp == 'probabilistic') and (sVarTypeData == 'result') \
                                            #        and (sVarNameGroup == 'discharge'):
                                            #    oVarDSet_SEEK = clipVar1D(oVarDSet_SEEK)

                                            # Store in a common dictionary
                                            oVarPickle_SEEK[sVarKey] = oVarDSet_SEEK

                                            # Dump data in a pickle file
                                            if not isfile(sVarFileName_ANCILLARY):
                                                createFolderByFile(sVarFileName_ANCILLARY)
                                                writeFilePickle(sVarFileName_ANCILLARY, oVarPickle_SEEK)
                                            else:
                                                appendFilePickle(sVarFileName_ANCILLARY, oVarPickle_SEEK, sVarKey)

                                            # Test
                                            # oVarFile_TEST = readFilePickle(sVarFileName_ANCILLARY)

                                            # Info end
                                            oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup][sSectionName] = True
                                            oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup][sSectionName] = oVarStats_SEEK
                                            oLogStream.info(' ------> Seeking time-series data for section ' +
                                                            sSectionName + ' ... DONE')
                                            # -------------------------------------------------------------------------------------

                                        else:

                                            # -------------------------------------------------------------------------------------
                                            # Exit for missing group in available file
                                            oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup] = False
                                            oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup] = None

                                            oLogStream.info(
                                                ' -----> Seeking data for group ' + sVarFileGroup + ' ... SKIPPED')
                                            Exc.getExc(
                                                ' =====> WARNING: file ' + sVarFileName_SEEK +
                                                ' is available; group ' + sVarFileGroup + ' not available in file!',
                                                2, 1)
                                            # -------------------------------------------------------------------------------------

                                    else:

                                        # -------------------------------------------------------------------------------------
                                        # Exit for mismatch in variable dimension(s)
                                        oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup] = False
                                        oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup] = None

                                        oLogStream.info(
                                            ' -----> Seeking data for group ' + sVarFileGroup + ' ... SKIPPED')
                                        Exc.getExc(' =====> WARNING: file ' + sVarFileName_SEEK + ' is not available!',
                                                   2, 1)
                                        # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------

                                else:

                                    # -------------------------------------------------------------------------------------
                                    # Info end
                                    oVarStats_SEEK = None
                                    oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup][sSectionName] = False
                                    oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup][sSectionName] = None
                                    oLogStream.info(' ------> Seeking time-series data for section ' +
                                                    sSectionName + ' ... DONE')
                                    Exc.getExc(' =====> WARNING: info file for section ' +
                                               sSectionName + ' is not available!', 2, 1)
                                    # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Info group
                            oLogStream.info(' -----> Seeking data for group ' + sVarFileGroup + ' ... DONE')
                            # -------------------------------------------------------------------------------------

                        elif sVarDims == 'var2d':

                            # -------------------------------------------------------------------------------------
                            # Declare variable list
                            oVarList_SEEK = None
                            oVarStats_SEEK = None

                            # Get generic dataset filename(s)
                            sVarFileName_SEEK = deepcopy(oVarFile[sVarFileTag])
                            sVarFileName_ANCILLARY = deepcopy(oVarFile[sVarFileAncillary])

                            # Define file tags
                            oFileTags_SEEK = {
                                '$yyyy': str(oVarTime_SEEK.year).zfill(4),
                                '$mm': str(oVarTime_SEEK.month).zfill(2),
                                '$dd': str(oVarTime_SEEK.day).zfill(2),
                                '$HH': str(oVarTime_SEEK.hour).zfill(2),
                                '$MM': str(oVarTime_SEEK.minute).zfill(2),
                                '$application': sAppTag
                            }

                            # Define seek filename (in zipped and unzipped format)
                            sVarFileName_SEEK = defineString(sVarFileName_SEEK, mergeDict(oFileTags_SEEK, oVarTags))
                            sVarFileName_ANCILLARY = defineString(sVarFileName_ANCILLARY, mergeDict(oFileTags_SEEK,
                                                                                                    oVarTags))
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Check file availability
                            if isfile(sVarFileName_SEEK):

                                # Get file data
                                oVarDSet_SEEK = wrapFileReader(sVarFileName_SEEK, sVarFileGroup)

                                # Find name(s) of input variable(s)
                                oVarNameSource_SEEK = findVarName(list(oVarDSet_SEEK.data_vars), sVarNameSource)
                                # Find tag(s) of input variable(s)
                                oVarTagPattern_SEEK, oVarTagValue_SEEK = findVarTag(oVarNameSource_SEEK, sVarNameSource)
                                # Create name of output variable(s)
                                oVarNameOutcome_SEEK = createVarName(sVarNameOutcome,
                                                                     oVarTagPattern_SEEK, oVarTagValue_SEEK)

                                # Create name of output variable(s)
                                oVarNameGroup_SEEK = createVarName(sVarNameGroup,
                                                                   oVarTagPattern_SEEK, oVarTagValue_SEEK)

                                # Iterate over variable(s)
                                for sVarNameSource_SEEK, sVarNameOutcome_SEEK, sVarNameGroup_SEEK in zip(
                                        oVarNameSource_SEEK, oVarNameOutcome_SEEK, oVarNameGroup_SEEK):

                                    # Info variable start
                                    oLogStream.info(' ------> Seeking data for input variable ' +
                                                    sVarNameSource_SEEK + ' to outcome variable ' +
                                                    sVarNameOutcome_SEEK + ' ... ')

                                    # Get variable data
                                    oVarDArray_SEEK = oVarDSet_SEEK[sVarNameSource_SEEK]
                                    oVarDArray_SEEK = createDArray2D(oVarDArray_SEEK,
                                                                     sVarName_IN=sVarNameSource_SEEK,
                                                                     sVarName_OUT=sVarNameOutcome_SEEK)
                                    # Create data array list
                                    vars()[sVarNameOutcome_SEEK] = oVarDArray_SEEK

                                    if oVarList_SEEK is None:
                                        oVarList_SEEK = [deepcopy(vars()[sVarNameOutcome_SEEK])]
                                    else:
                                        oVarList_SEEK.append(deepcopy(vars()[sVarNameOutcome_SEEK]))

                                    # Delete variable(s) from vars()
                                    if sVarNameOutcome_SEEK in vars():
                                        del vars()[sVarNameOutcome_SEEK]

                                    # Variable statistics
                                    if sVarNameGroup_SEEK != 'other':
                                        oVarStats_SEEK = createStats2D(oVarStats_SEEK, oVarDArray_SEEK,
                                                                       sVarNameGroup_SEEK)

                                    # Info variable end
                                    oLogStream.info(' ------> Seeking data for input variable ' +
                                                    sVarNameSource_SEEK + ' to outcome variable ' +
                                                    sVarNameOutcome_SEEK + ' ... DONE')
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Merge data in dataset object
                                oVarDSet_SEEK = mergeVar2D(oVarList_SEEK)
                                # Store in a common dictionary
                                if sVarKey in oVarPickle_SEEK:
                                    oVarPickle_SEEK = {}
                                oVarPickle_SEEK[sVarKey] = oVarDSet_SEEK

                                # Dump data in a pickle file
                                if not isfile(sVarFileName_ANCILLARY):
                                    createFolderByFile(sVarFileName_ANCILLARY)
                                    writeFilePickle(sVarFileName_ANCILLARY, oVarPickle_SEEK)
                                else:
                                    appendFilePickle(sVarFileName_ANCILLARY, oVarPickle_SEEK, sVarKey)

                                # Test
                                # oVarFile_TEST = readFilePickle(sVarFileName_ANCILLARY)

                                # Store seeking step(s)
                                oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup] = True
                                oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup] = oVarStats_SEEK
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Info group
                                oLogStream.info(' -----> Seeking data for group ' + sVarFileGroup + ' ... DONE')
                                # -------------------------------------------------------------------------------------

                            else:

                                # -------------------------------------------------------------------------------------
                                # Exit for mismatch in variable dimension(s)
                                oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup] = False
                                oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup] = None

                                oLogStream.info(' -----> Seeking data for group ' + sVarFileGroup + ' ... SKIPPED')
                                Exc.getExc(' =====> WARNING: file ' + sVarFileName_SEEK + ' is not available!', 2, 1)
                                # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------

                        else:

                            # -------------------------------------------------------------------------------------
                            # Exit for mismatch in variable dimension(s)
                            oVarData_SEEK_WS[sAppTag][sVarKey][sVarFileGroup] = False
                            oVarData_SEEK_STATS[sAppTag][sVarKey][sVarFileGroup] = None

                            oLogStream.info(' -----> Seeking data for group ' + sVarFileGroup + ' ... SKIPPED')
                            Exc.getExc(' =====> WARNING: variable ' +
                                       sVarNameSource + ' is not declared in a allowed dimension(s)!', 2, 1)
                            # -------------------------------------------------------------------------------------

                        # End condition about variable dimension(s)
                        # -------------------------------------------------------------------------------------

                    # End iteration(s) over variable(s)
                    # -------------------------------------------------------------------------------------

                # End iteration(s) over dataset(s)
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Info application
                oLogStream.info(' ----> Seeking data for application ' + sAppTag + ' ... DONE')
                # -------------------------------------------------------------------------------------

            else:

                # -------------------------------------------------------------------------------------
                # Exit for mismatch in variable dimension(s)
                oLogStream.info(' ----> Seeking data for application ' + sAppTag + ' ... SKIPPED')
                Exc.getExc(' =====> WARNING: application name is not valid! ', 2, 1)
                # -------------------------------------------------------------------------------------

            # End condition about application tag
            # -------------------------------------------------------------------------------------

        # End iteration(s) over application(s)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return variable(s)
        return oVarData_SEEK_WS, oVarData_SEEK_STATS
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

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
