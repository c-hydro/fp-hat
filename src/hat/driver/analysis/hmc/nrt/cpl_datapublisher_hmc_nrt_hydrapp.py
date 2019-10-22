"""
Library Features:

Name:          cpl_datapublisher_hmc_nrt_hydrapp
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import progressbar
import os

import numpy as np
import pandas as pd

from copy import deepcopy

from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import mergeDict

from src.hat.dataset.generic.lib_generic_io_method import readFilePickle

from src.hat.dataset.generic.lib_generic_io_apps import findVarName, findVarTag, createVarName
from src.hat.dataset.generic.lib_generic_io_utils import createVarAttrs, mergeVarAttrs, addVarAttrs, reduceDArray3D
from src.hat.dataset.generic.lib_generic_configuration_utils import configVarFx

from src.hat.framework.hydrapp.lib_hydrapp_io_apps import wrapFileRegistry
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
            oVarMethodName = checkVarField(oVarFields['id']['var_method_publish'], iVarN)
            oVarArgs = checkVarField(oVarFields['id']['var_args'], iVarN)

            # Get variable attributes
            oVarFigureDPI = checkVarField(oVarFields['attributes']['figure_dpi'], iVarN)

            # Get variable statistics
            if sVarKey in list(oVarData_STATS.keys()):
                oVarStats = oVarData_STATS[sVarKey]
            else:
                oVarStats = None

            # Reduce publishing method(s)
            oVarMethodName_RED = {}
            for oVarMethodObj in oVarMethodName:
                for sVarMethodKey, oVarMethodValue in oVarMethodObj.items():
                    if sVarMethodKey not in list(oVarMethodName_RED.keys()):
                        oVarMethodName_RED[sVarMethodKey] = oVarMethodValue
            oVarMethodName_RED = [oVarMethodName_RED]

            # Store data and registry step(s)
            oVarData_DEF_WS[sVarKey] = {}
            oVarRegistry_DEF_WS[sVarKey] = {}
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Iterate over publishing object(s)
            for oVarMethodObj in oVarMethodName_RED:

                # DEBUG
                # n = 1
                # sVarMethodObj = next(x for i, x in enumerate(oVarMethodObj) if i == n)
                # oVarMethodObj_TMP = deepcopy(oVarMethodObj)
                # oVarMethodObj = {sVarMethodObj: oVarMethodObj_TMP[sVarMethodObj]}
                # DEBUG

                # -------------------------------------------------------------------------------------
                # Iterate over publishing method(s) and argument(s)
                for sMethodName, oMethodArgs in oVarMethodObj.items():

                    # -------------------------------------------------------------------------------------
                    # Get method information
                    iVarN_DEF = oMethodArgs['variable_name'].__len__()
                    oVarGroup_DEF = list(oMethodArgs['variable_name'].keys())

                    sGraphName_DEF = oMethodArgs['graph_name'][0]
                    oVarName_DEF = oMethodArgs['variable_name']
                    oVarAppearance_DEF = oMethodArgs['variable_appearance']
                    oFxName_DEF = checkVarField(oMethodArgs['function_graph'], iVarN_DEF)
                    oFileName_DEF = checkVarField(oMethodArgs['file_name'], iVarN_DEF)
                    oFileContent_DEF = checkVarField(oMethodArgs['file_content'], iVarN_DEF)
                    oCMapName_DEF = checkVarField(oMethodArgs['colormap_name'], iVarN_DEF)

                    # Variable information
                    sVarDims = list(set(oVarDims))[0]
                    sVarFileAncillary = list(set(oVarFileAncillary))[0]

                    # Convert str to list (to avoid issue on iterations)
                    if isinstance(oFxName_DEF, str):
                        oFxName_DEF = [oFxName_DEF]
                    if isinstance(oFileName_DEF, str):
                        oFileName_DEF = [oFileName_DEF]
                    if isinstance(oFileContent_DEF, str):
                        oFileContent_DEF = [oFileContent_DEF]
                    if isinstance(oCMapName_DEF, str):
                        oCMapName_DEF = [oCMapName_DEF]

                    # Info method start
                    oLogStream.info(' -----> Publishing data [type: ' + sVarKey +
                                    ' - method: ' + sMethodName + '] ... ')
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Check variable dimension(s)
                    if sVarDims == 'var1d':

                        # -------------------------------------------------------------------------------------
                        # Time series function and filename (one for each graph)
                        sFxName_DEF = oFxName_DEF[0]
                        sFileName_DEF = oFileName_DEF[0]
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Check fx availability
                        if hasattr(libFxTS, sFxName_DEF):

                            # -------------------------------------------------------------------------------------
                            # Iterate over section(s)
                            oSectionStats_WS = {}
                            oDataGenerator = oDataSection.iterrows()

                            # DEBUG
                            # n = 93
                            # oDataGenerator = [next(x for i, x in enumerate(oDataGenerator) if i == n)]
                            # DEBUG

                            for iSectionID, oSectionData in enumerate(oDataGenerator):

                                # -------------------------------------------------------------------------------------
                                # Get section info
                                oSectionInfo = oSectionData[1]
                                sSectionName = oSectionInfo['OUTLET_NAME']
                                sSectionBasin = oSectionInfo['BASIN']

                                # Get section element, cols and rows order
                                if 'HAT_ELEMENT' in oSectionInfo:
                                    iSectionHAT_ELEM = oSectionInfo['HAT_ELEMENT']
                                    iSectionHAT_ID_COLS = oSectionInfo['HAT_ID_COLS']
                                    iSectionHAT_ID_ROWS = oSectionInfo['HAT_ID_ROWS']
                                else:
                                    iSectionHAT_ELEM = None
                                    iSectionHAT_ID_COLS = None
                                    iSectionHAT_ID_ROWS = None

                                sSectionFileName_ANCILLARY = oSectionInfo['OUTLET_FILE_ANCILLARY']
                                # Info section
                                oLogStream.info(' ------> Publishing time-series data for section ' +
                                                sSectionName + ' ... ')
                                # Define section attributes
                                oVarSectionAttrs = createVarAttrs(oSectionInfo)
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Check ancillary section file availability
                                if os.path.isfile(sSectionFileName_ANCILLARY):

                                    # -------------------------------------------------------------------------------------
                                    # Get generic dataset filename(s)
                                    sVarFileName_ANCILLARY = oVarFile[sVarFileAncillary]
                                    sVarFileName_DEF = oVarFile[sFileName_DEF]
                                    sVarFileRegistry_DEF = oVarFile['file_hydrapp_info_ts']

                                    # Define file tags
                                    oFileTags_DEF = {
                                        '$yyyy': str(oVarTime_RUN.year).zfill(4),
                                        '$mm': str(oVarTime_RUN.month).zfill(2),
                                        '$dd': str(oVarTime_RUN.day).zfill(2),
                                        '$HH': str(oVarTime_RUN.hour).zfill(2),
                                        '$MM': str(oVarTime_RUN.minute).zfill(2),
                                        '$section': sSectionName,
                                        '$application': sAppTag,
                                        '$graphname': sGraphName_DEF,
                                        '$group': sSectionBasin,
                                        '$basin': sSectionBasin,
                                        '$row': "{:03d}".format(iSectionHAT_ID_ROWS),
                                        '$col': "{:03d}".format(iSectionHAT_ID_COLS),
                                        '$element': "{:03d}".format(iSectionHAT_ELEM)
                                    }

                                    # Define ancillary filename, graph and registry
                                    sVarFileName_ANCILLARY = defineString(sVarFileName_ANCILLARY, mergeDict(
                                        oFileTags_DEF, oVarTags))
                                    sVarFileName_DEF = defineString(sVarFileName_DEF, mergeDict(
                                        oFileTags_DEF, oVarTags))
                                    sVarFileRegistry_DEF = defineString(sVarFileRegistry_DEF, mergeDict(
                                        oFileTags_DEF, oVarTags))
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Get section statistics (min and max values on selected period)
                                    if sSectionName not in list(oSectionStats_WS.keys()):
                                        oSectionStats_STEP = None
                                        for sVarStats_KEY, oVarStats_DATA in oVarStats.items():
                                            oSectionStats_DATA = oVarStats_DATA[sSectionName]

                                            if oSectionStats_STEP is None:
                                                oSectionStats_STEP = {}

                                            if oSectionStats_DATA is not None:

                                                for sSectionStats_KEY, oSectionStats_VALUES in \
                                                        oSectionStats_DATA.items():

                                                    if sSectionStats_KEY not in oSectionStats_STEP:
                                                        oSectionStats_STEP[sSectionStats_KEY] = {}
                                                        oSectionStats_STEP[sSectionStats_KEY]['min'] = {}
                                                        oSectionStats_STEP[sSectionStats_KEY]['max'] = {}

                                                    dSectionStats_MIN = min(oSectionStats_VALUES['min'])
                                                    dSectionStats_MAX = max(oSectionStats_VALUES['max'])

                                                    if not oSectionStats_STEP[sSectionStats_KEY]['min']:
                                                        oSectionStats_STEP[sSectionStats_KEY]['min'] = dSectionStats_MIN
                                                    else:
                                                        dSectionStats_MIN_OLD = oSectionStats_STEP[sSectionStats_KEY]['min']
                                                        dSectionStats_MIN_UPD = min(dSectionStats_MIN_OLD,
                                                                                    dSectionStats_MIN)
                                                        oSectionStats_STEP[sSectionStats_KEY]['min'] = dSectionStats_MIN_UPD
                                                    if not oSectionStats_STEP[sSectionStats_KEY]['max']:
                                                        oSectionStats_STEP[sSectionStats_KEY]['max'] = dSectionStats_MAX
                                                    else:
                                                        dSectionStats_MAX_OLD = oSectionStats_STEP[sSectionStats_KEY]['max']
                                                        dSectionStats_MAX_UPD = max(dSectionStats_MAX_OLD,
                                                                                    dSectionStats_MAX)
                                                        oSectionStats_STEP[sSectionStats_KEY]['max'] = dSectionStats_MAX_UPD

                                        oSectionStats_WS[sSectionName] = oSectionStats_STEP

                                    # Get section statistics
                                    oSectionStats = oSectionStats_WS[sSectionName]
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Check ancillary section file availability
                                    oVarFile_DEF = None
                                    if os.path.isfile(sVarFileName_ANCILLARY):

                                        # -------------------------------------------------------------------------------------
                                        # Get data file
                                        oVarFile_DEF = readFilePickle(sVarFileName_ANCILLARY)[sVarKey]
                                        # Get time file
                                        oVarTime_DEF = oVarFile_DEF['time'].values
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Iterate over method variable(s) name and appearance
                                        oVarData_DEF = {}
                                        for (sVarAppGroup_TYPE, oVarAppValue_TYPE), \
                                            (sVarNameGroup_TYPE, oVarNameValue_TYPE) in zip(
                                                oVarAppearance_DEF.items(), oVarName_DEF.items()):

                                            # -------------------------------------------------------------------------------------
                                            # Iterate over variable(s) to publish data    using defined function(s)
                                            oVarDataFrame_DEF = None
                                            for iVarID_TYPE_STEP, \
                                                (sFileContent_TYPE_STEP,
                                                 sVarNameValue_TYPE_STEP, sVarAppValue_TYPE_STEP) in enumerate(
                                                    zip(oFileContent_DEF, oVarNameValue_TYPE, oVarAppValue_TYPE)):

                                                # -------------------------------------------------------------------------------------
                                                # Check variable definition
                                                if sVarNameValue_TYPE_STEP in oVarNameOutcome:

                                                    # -------------------------------------------------------------------------------------
                                                    # Get variable information
                                                    iVarIdx_TYPE_STEP = oVarNameOutcome.index(sVarNameValue_TYPE_STEP)

                                                    sVarDims_TYPE_STEP = oVarDims[iVarIdx_TYPE_STEP]
                                                    sVarTypeData_TYPE_STEP = oVarTypeData[iVarIdx_TYPE_STEP]
                                                    sVarTypeExp_TYPE_STEP = oVarTypeExp[iVarIdx_TYPE_STEP]
                                                    sVarNameSource_TYPE_STEP = oVarNameSource[iVarIdx_TYPE_STEP]
                                                    sVarNameOutcome_TYPE_STEP = oVarNameOutcome[iVarIdx_TYPE_STEP]
                                                    sVarNameGroup_TYPE_STEP = oVarNameGroup[iVarIdx_TYPE_STEP]
                                                    sVarFileTag_TYPE_STEP = oVarFileTag[iVarIdx_TYPE_STEP]
                                                    sVarFileGroup_TYPE_STEP = oVarFileGroup[iVarIdx_TYPE_STEP]
                                                    # -------------------------------------------------------------------------------------

                                                    # -------------------------------------------------------------------------------------
                                                    # Find name(s) of input variable(s)
                                                    oVarNameOutcome_TYPE_STEP = findVarName(
                                                        list(oVarFile_DEF.data_vars), sVarNameOutcome_TYPE_STEP)
                                                    # Find tag(s) of input variable(s)
                                                    oVarTagPattern_TYPE_STEP, oVarTagValue_TYPE_STEP = findVarTag(
                                                        oVarNameOutcome_TYPE_STEP, sVarNameOutcome_TYPE_STEP)
                                                    # Create name of output variable(s)
                                                    oVarNameOutcome_TYPE_STEP = createVarName(sVarNameOutcome_TYPE_STEP,
                                                                                              oVarTagPattern_TYPE_STEP,
                                                                                              oVarTagValue_TYPE_STEP)

                                                    # Create name of output variable(s)
                                                    oVarNameGroup_TYPE_STEP = createVarName(sVarNameGroup_TYPE_STEP,
                                                                                            oVarTagPattern_TYPE_STEP,
                                                                                            oVarTagValue_TYPE_STEP)

                                                    # Define algorithm attribute(s)
                                                    oVarAlgAttrs_TYPE_STEP = {
                                                        'var_dims': sVarDims_TYPE_STEP,
                                                        'var_type_data': sVarTypeData_TYPE_STEP,
                                                        'var_type_experiment': sVarTypeExp_TYPE_STEP,
                                                        'var_name_in': sVarNameSource_TYPE_STEP,
                                                        'var_name_out': oVarNameOutcome_TYPE_STEP,
                                                        'var_name_group': oVarNameGroup_TYPE_STEP,
                                                        'var_file_tag': sVarFileTag_TYPE_STEP,
                                                        'var_file_group': sVarFileGroup_TYPE_STEP,
                                                        'var_appearance': sVarAppValue_TYPE_STEP,
                                                        'var_content': sFileContent_TYPE_STEP}
                                                    # -------------------------------------------------------------------------------------

                                                    # -------------------------------------------------------------------------------------
                                                    # Iterate over variable(s)
                                                    oVarDataAttrs_TYPE_STEP = None
                                                    for sVarNameOutcome_TYPE_STEP, sVarNameGroup_TYPE_STEP in zip(
                                                            oVarNameOutcome_TYPE_STEP, oVarNameGroup_TYPE_STEP):

                                                        # Get data for each variable(s)
                                                        oVarDataArray_TYPE_STEP = oVarFile_DEF[sVarNameOutcome_TYPE_STEP]
                                                        oVarDataFrame_TYPE_STEP = oVarDataArray_TYPE_STEP.to_dataframe(
                                                            name=sVarNameOutcome_TYPE_STEP)

                                                        if oVarDataAttrs_TYPE_STEP is None:
                                                            oVarDataAttrs_TYPE_STEP = oVarDataArray_TYPE_STEP.attrs

                                                            # Add min and max value of variable (run based information)
                                                            if sVarNameGroup_TYPE_STEP != 'other':
                                                                oSectioStats_TYPE_STEP = oSectionStats[
                                                                    sVarNameGroup_TYPE_STEP]
                                                                oVarDataAttrs_TYPE_STEP['min'] = oSectioStats_TYPE_STEP[
                                                                    'min']
                                                                oVarDataAttrs_TYPE_STEP['max'] = oSectioStats_TYPE_STEP[
                                                                    'max']
                                                            else:
                                                                oVarDataAttrs_TYPE_STEP['min'] = None
                                                                oVarDataAttrs_TYPE_STEP['max'] = None

                                                                # Manage data frame iteration(s)
                                                        if oVarDataFrame_DEF is None:
                                                            oVarDataFrame_DEF = oVarDataFrame_TYPE_STEP.copy()
                                                        else:
                                                            oVarDataFrame_DEF[sVarNameOutcome_TYPE_STEP] = \
                                                                oVarDataFrame_TYPE_STEP

                                                    # Add attribute(s) to dataframe
                                                    oVarAttrs_DEF = mergeVarAttrs(
                                                        [oVarSectionAttrs, oVarAlgAttrs_TYPE_STEP,
                                                         oVarDataAttrs_TYPE_STEP])
                                                    # -------------------------------------------------------------------------------------
                                                else:
                                                    # -------------------------------------------------------------------------------------
                                                    # Undefined data
                                                    a1dVarData_UNDEF = np.zeros([oVarTime_DEF.__len__()])
                                                    a1dVarData_UNDEF[:] = np.nan
                                                    oVarDataFrame_UNDEF = pd.DataFrame(
                                                        a1dVarData_UNDEF, index=oVarTime_DEF,
                                                        columns=[sVarNameValue_TYPE_STEP])

                                                    if oVarDataFrame_DEF is None:
                                                        oVarDataFrame_DEF = oVarDataFrame_UNDEF
                                                    else:
                                                        oVarDataFrame_DEF[sVarNameValue_TYPE_STEP] = \
                                                            oVarDataFrame_UNDEF
                                                    oVarAlgAttrs_TYPE_STEP = None
                                                    oVarDataAttrs_TYPE_STEP = None

                                                    # Add attribute(s) to data frame
                                                    oVarAttrs_DEF = mergeVarAttrs(
                                                        [oVarSectionAttrs, oVarAlgAttrs_TYPE_STEP,
                                                         oVarDataAttrs_TYPE_STEP])
                                                    # -------------------------------------------------------------------------------------

                                                # -------------------------------------------------------------------------------------

                                                # -------------------------------------------------------------------------------------
                                                # Save data in a dictionary to apply publish function
                                                oVarDataFrame_DEF = addVarAttrs(oVarDataFrame_DEF, oVarAttrs_DEF)
                                                oVarData_DEF[sVarNameGroup_TYPE] = oVarDataFrame_DEF
                                                # -------------------------------------------------------------------------------------

                                            # End of iteration over(s) variable(s) data
                                            # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Defined fx argument(s)
                                        oFxArgs_DEF = configVarArgs(oVarData_DEF)
                                        oFxArgs_DEF["sFileName"] = sVarFileName_DEF
                                        oFxArgs_DEF["oTimeRun"] = oVarTime_RUN
                                        oFxArgs_DEF["sTypeRun"] = sGraphName_DEF

                                        # Call graph fx
                                        oFxData = configVarFx(sFxName_DEF, libFxTS, oFxArgs_DEF)
                                        # oFxData = True
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Create registry data for ts
                                        if oFxData:
                                            if 'filename' not in oVarRegistry_DEF_WS[sVarKey]:
                                                oVarRegistry_DEF_WS[sVarKey]['filename'] = {}
                                                oVarRegistry_DEF_WS[sVarKey]['filename'] = sVarFileRegistry_DEF
                                            if 'registry' not in oVarRegistry_DEF_WS[sVarKey]:
                                                oVarRegistry_DEF_WS[sVarKey]['registry'] = {}

                                            sRegistryString = sSectionBasin.replace(' ', '_')
                                            if sRegistryString not in oVarRegistry_DEF_WS[sVarKey]['registry']:
                                                oVarRegistry_DEF_WS[sVarKey]['registry'][sRegistryString] = {}
                                                oVarRegistry_DEF_WS[sVarKey]['registry'][sRegistryString]['level1'] = \
                                                    [sGraphName_DEF]
                                            else:
                                                oVarReg_GENERIC = oVarRegistry_DEF_WS[sVarKey]['registry']
                                                oRunReg = oVarReg_GENERIC[sRegistryString]['level1']
                                                oRunReg.append(sGraphName_DEF)
                                                oVarRegistry_DEF_WS[sVarKey]['registry'][sRegistryString]['level1'] = \
                                                    list(set(oRunReg))
                                        else:
                                            # Exit condition for error(s) in plotting data
                                            Exc.getExc(' =====> WARNING: error(s) occurred in plotting data! ', 2, 1)
                                        # -------------------------------------------------------------------------------------

                                    else:
                                        # ------------------------------------------------------------------------------------
                                        # Exit data ancillary not found
                                        Exc.getExc(' =====> WARNING: ancillary data file not found! ', 2, 1)
                                        # ------------------------------------------------------------------------------------
                                else:
                                    # ------------------------------------------------------------------------------------
                                    # Exit section ancillary not found
                                    Exc.getExc(' =====> WARNING: ancillary section file not found! ', 2, 1)
                                    # ------------------------------------------------------------------------------------

                                # ------------------------------------------------------------------------------------
                                # Info iteration over section(s)
                                oLogStream.info(' ------> Publishing time-series data for section ' +
                                                sSectionName + ' ... DONE')
                                # ------------------------------------------------------------------------------------
                        else:
                            # ------------------------------------------------------------------------------------
                            # Exit graph method not found in library
                            Exc.getExc(' =====> WARNING: graph method not found in library! ', 2, 1)
                            # ------------------------------------------------------------------------------------

                    elif sVarDims == 'var2d':

                        # -------------------------------------------------------------------------------------
                        # Iterate over graph function(s) and filename(s)
                        for sVarGroup_DEF in oVarGroup_DEF:

                            # DEBUG
                            # sVarGroup_DEF = 'sm_model_obs'
                            # sVarGroup_DEF = 'snow_density_model_obs'
                            # DEBUG

                            # -------------------------------------------------------------------------------------
                            # Info group
                            oLogStream.info(' ------> Publishing group data ' + sVarGroup_DEF + ' ... ')

                            # Get definition(s)
                            sGraphName_DEF = oMethodArgs['graph_name'][0]
                            sVarName_DEF = oVarName_DEF[sVarGroup_DEF][0]
                            sVarAppearance_DEF = oVarAppearance_DEF[sVarGroup_DEF][0]
                            sFxName_DEF = oFxName_DEF[sVarGroup_DEF][0]
                            sFileName_DEF = oFileName_DEF[sVarGroup_DEF][0]
                            sFileContent_DEF = oFileContent_DEF[sVarGroup_DEF][0]
                            sCMapName_DEF = oCMapName_DEF[sVarGroup_DEF][0]
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Check fx availability
                            if hasattr(libFxGridded, sFxName_DEF):

                                # -------------------------------------------------------------------------------------
                                # Check definition of graph filename
                                if sFileName_DEF in oVarFile:

                                    # -------------------------------------------------------------------------------------
                                    # Get variable generic filename(s)
                                    sVarFileName_ANCILLARY = deepcopy(oVarFile[sVarFileAncillary])
                                    sVarFileName_DEF = deepcopy(oVarFile[sFileName_DEF])
                                    sVarFileRegistry_DEF = deepcopy(oVarFile['file_hydrapp_info_gridded'])

                                    # Get variable colormap
                                    if sCMapName_DEF is not None:
                                        if sCMapName_DEF in list(oVarCMap.keys()):
                                            sVarFileCMap_DEF = oVarCMap[sCMapName_DEF]
                                        else:
                                            sVarFileCMap_DEF = sCMapName_DEF
                                    else:
                                        sVarFileCMap_DEF = None

                                    # Define file tags
                                    oFileTags_DEF = {
                                        '$yyyy': str(oVarTime_RUN.year).zfill(4),
                                        '$mm': str(oVarTime_RUN.month).zfill(2),
                                        '$dd': str(oVarTime_RUN.day).zfill(2),
                                        '$HH': str(oVarTime_RUN.hour).zfill(2),
                                        '$MM': str(oVarTime_RUN.minute).zfill(2),
                                        '$application': sAppTag,
                                        '$graphname': sGraphName_DEF,
                                        '$group': sVarAppearance_DEF.replace(" ", "_"),
                                        '$variable': sVarAppearance_DEF.replace(" ", "_")
                                    }

                                    # Define ancillary, data and registry filename(s)
                                    sVarFileName_ANCILLARY = defineString(sVarFileName_ANCILLARY, mergeDict(
                                        oFileTags_DEF, oVarTags))
                                    sVarFileName_DEF = defineString(sVarFileName_DEF, mergeDict(
                                        oFileTags_DEF, oVarTags))
                                    sVarFileRegistry_DEF = defineString(sVarFileRegistry_DEF, mergeDict(
                                        oFileTags_DEF, oVarTags))
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Check ancillary section file availability
                                    if os.path.isfile(sVarFileName_ANCILLARY):

                                        # -------------------------------------------------------------------------------------
                                        # Get data file
                                        oVarFile_DEF = readFilePickle(sVarFileName_ANCILLARY)[sVarKey]
                                        # Get time file
                                        oVarTime_DEF = oVarFile_DEF['time'].values
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Check variable definition
                                        if sVarName_DEF in oVarNameOutcome:

                                            # -------------------------------------------------------------------------------------
                                            # Get variable information
                                            iVarIdx_DEF = oVarNameOutcome.index(sVarName_DEF)

                                            sVarDims_DEF = oVarDims[iVarIdx_DEF]
                                            sVarTypeData_DEF = oVarTypeData[iVarIdx_DEF]
                                            sVarTypeExp_DEF = oVarTypeExp[iVarIdx_DEF]
                                            sVarNameSource_DEF = oVarNameSource[iVarIdx_DEF]
                                            sVarNameOutcome_DEF = oVarNameOutcome[iVarIdx_DEF]
                                            sVarFileTag_DEF = oVarFileTag[iVarIdx_DEF]
                                            sVarFileGroup_DEF = oVarFileGroup[iVarIdx_DEF]
                                            # -------------------------------------------------------------------------------------

                                            # -------------------------------------------------------------------------------------
                                            # Find name(s) of input variable(s)
                                            oVarNameOutcome_DEF = findVarName(
                                                list(oVarFile_DEF.data_vars), sVarNameOutcome_DEF)

                                            # Find tag(s) of input variable(s)
                                            oVarTagPattern_DEF, oVarTagValue_DEF = findVarTag(oVarNameOutcome_DEF,
                                                                                              sVarNameOutcome_DEF)

                                            # Create name of output variable(s)
                                            oVarNameOutcome_DEF = createVarName(sVarNameOutcome_DEF, oVarTagPattern_DEF,
                                                                                oVarTagValue_DEF)

                                            # Create filename(s) of output variable(s)
                                            oVarFileName_DEF = createVarName(sVarFileName_DEF, oVarTagPattern_DEF,
                                                                             oVarTagValue_DEF)

                                            # Create filename(s) of output variable(s)
                                            oVarFileCMap_DEF = createVarName(sVarFileCMap_DEF, oVarTagPattern_DEF,
                                                                             oVarTagValue_DEF)

                                            # Define algorithm attribute(s)
                                            oVarAlgAttrs_DEF = {'var_dims': sVarDims_DEF,
                                                                'var_type_data': sVarTypeData_DEF,
                                                                'var_type_experiment': sVarTypeExp_DEF,
                                                                'var_name_in': sVarNameSource_DEF,
                                                                'var_name_out': oVarNameOutcome_DEF,
                                                                'var_file_tag': sVarFileTag_DEF,
                                                                'var_file_group': sVarFileGroup_DEF,
                                                                'var_appearance': sVarAppearance_DEF,
                                                                'var_content': sFileContent_DEF}
                                            # -------------------------------------------------------------------------------------

                                            # -------------------------------------------------------------------------------------
                                            # Iterate over variable(s)
                                            oVarDataAttrs_DEF = None
                                            for sVarNameOutcome_DEF, sVarFileName_DEF, sVarFileCMap_DEF in zip(
                                                    oVarNameOutcome_DEF, oVarFileName_DEF, oVarFileCMap_DEF):

                                                # -------------------------------------------------------------------------------------
                                                # Info map
                                                oLogStream.info(' -------> Publishing gridded data ' +
                                                                sVarNameOutcome_DEF + ' ... ')

                                                # Get data for each variable(s)
                                                oVarDataArray_DEF = oVarFile_DEF[sVarNameOutcome_DEF]
                                                oVarDataArray_DEF = reduceDArray3D(oVarDataArray_DEF)

                                                if oVarDataAttrs_DEF is None:
                                                    oVarDataAttrs_DEF = oVarDataArray_DEF.attrs

                                                # Manage attribute(s)
                                                oVarAttrs_DEF = mergeVarAttrs([oVarAlgAttrs_DEF, oVarDataAttrs_DEF])
                                                # Update variable appearance
                                                oVarAttrs_DEF['var_appearance'] = sVarNameOutcome_DEF.replace('_', ' ')

                                                # Add attributes to data array
                                                oVarDataArray_DEF = addVarAttrs(oVarDataArray_DEF, oVarAttrs_DEF)
                                                # -------------------------------------------------------------------------------------

                                                # -------------------------------------------------------------------------------------
                                                # Defined fx argument(s)
                                                oFxArgs_DEF = {'oVarData': oVarDataArray_DEF,
                                                               "sFileName": sVarFileName_DEF,
                                                               "sColorMap": sVarFileCMap_DEF,
                                                               "oTimeRun": oVarTime_RUN,
                                                               "sTypeRun": sGraphName_DEF}

                                                # Call graph fx
                                                oFxData = configVarFx(sFxName_DEF, libFxGridded, oFxArgs_DEF)
                                                # oFxData = True
                                                # -------------------------------------------------------------------------------------

                                                # -------------------------------------------------------------------------------------
                                                # Create registry data for ts
                                                if oFxData:

                                                    # Info end
                                                    oLogStream.info(' -------> Publishing gridded data ' +
                                                                    sVarNameOutcome_DEF + ' ... DONE')

                                                    if 'filename' not in oVarRegistry_DEF_WS[sVarKey]:
                                                        oVarRegistry_DEF_WS[sVarKey]['filename'] = {}
                                                        oVarRegistry_DEF_WS[sVarKey]['filename'] = sVarFileRegistry_DEF
                                                    if 'registry' not in oVarRegistry_DEF_WS[sVarKey]:
                                                        oVarRegistry_DEF_WS[sVarKey]['registry'] = {}

                                                    sRegistryString = sVarAppearance_DEF.replace(" ", "_")
                                                    if sRegistryString not in oVarRegistry_DEF_WS[sVarKey]['registry']:
                                                        oVarRegistry_DEF_WS[sVarKey]['registry'][sRegistryString] = {}
                                                        oVarRegistry_DEF_WS[sVarKey]['registry'][sRegistryString][
                                                            'level1'] = [sGraphName_DEF]
                                                    else:
                                                        oVarReg_GENERIC = oVarRegistry_DEF_WS[sVarKey]['registry']
                                                        oRunReg = oVarReg_GENERIC[sRegistryString]['level1']
                                                        oRunReg.append(sGraphName_DEF)
                                                        oVarRegistry_DEF_WS[sVarKey]['registry'][sRegistryString][
                                                            'level1'] = list(set(oRunReg))
                                                else:
                                                    # Info end
                                                    oLogStream.info(' -------> Publishing gridded data ' +
                                                                    sVarNameOutcome_DEF + ' ... FAILED')

                                                    # Exit condition for error(s) in plotting data
                                                    Exc.getExc(' =====> WARNING: error(s) occurred in plotting data! ',
                                                               2, 1)
                                                # -------------------------------------------------------------------------------------

                                            # End iteration(s) over output variable(s)
                                            # -------------------------------------------------------------------------------------
                                        else:
                                            # -------------------------------------------------------------------------------------
                                            # Variable name not found
                                            Exc.getExc(
                                                ' =====> WARNING: variable ' + sVarName_DEF +
                                                ' not found in outcome expected variable!', 2, 1)
                                            # -------------------------------------------------------------------------------------

                                    else:
                                        # -------------------------------------------------------------------------------------
                                        # Exit data ancillary not found
                                        Exc.getExc(' =====> WARNING: ancillary data file not found!', 2, 1)
                                        # -------------------------------------------------------------------------------------
                                else:
                                    # ------------------------------------------------------------------------------------
                                    # Exit due to error in defining graph filename
                                    Exc.getExc(' =====> WARNING: graph filename is not correctly defined!', 2, 1)
                                    # ------------------------------------------------------------------------------------
                            else:
                                # ------------------------------------------------------------------------------------
                                # Exit graph method not found in library
                                Exc.getExc(' =====> WARNING: graph method not found in library! ', 2, 1)
                                # ------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Info group
                            oLogStream.info(' ------> Publishing group data ' + sVarGroup_DEF + ' ... DONE')
                            # -------------------------------------------------------------------------------------

                        # End iteration(s) over graph function(s) and filename(s)
                        # ------------------------------------------------------------------------------------
                    else:
                        # ------------------------------------------------------------------------------------
                        # Exit variable dimension(s) not allowed
                        Exc.getExc(' =====> WARNING: variable dimension(s) not allowed! ', 2, 1)
                        # ------------------------------------------------------------------------------------

                    # Info method end
                    oLogStream.info(' -----> Publishing data [type: ' + sVarKey +
                                    ' - method: ' + sMethodName + '] ... DONE')
                    # End condition(s) over variable dimension(s)
                    # ------------------------------------------------------------------------------------

                # End iteration(s) over publishing method(s)
                # ------------------------------------------------------------------------------------

            # End iteration(s) over publishing object(s)
            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # End iteration(s) over dataset(s)
        if oVarRegistry_DEF_WS is not None:
            wrapFileRegistry(oVarRegistry_DEF_WS)
        else:
            Exc.getExc(' =====> WARNING: registry file is None! Check your settings and data!', 2, 1)

        # Return variable(s)
        return oVarRegistry_DEF_WS
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
