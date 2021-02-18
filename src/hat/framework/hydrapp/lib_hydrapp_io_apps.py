"""
Library Features:

Name:          lib_hydrapp_io_apps
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190315'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os

from numbers import Number

from src.hat.framework.hydrapp.lib_hydrapp_io_method import writeFileRegistry
from src.common.utils.lib_utils_op_system import createFolderByFile
from src.common.utils.lib_utils_op_list import sortListNatural

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to update root registry
def updateRootRegistry(reg_history, reg_step):

    if isinstance(reg_history, list):
        if reg_step is not None:

            if any(isinstance(el, list) for el in reg_history):

                reg_history.extend([reg_step])
                reg_merge = reg_history
            else:
                reg_merge = [reg_history, reg_step]
        else:
            raise NotImplementedError(' Registry updating received a None list. Check your algorithm!')
    else:
        raise NotImplementedError(' Registry of the history is not defined in list format. Check your algorithm!')

    return reg_merge
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Translate registry string to registry list
def translateRootRegistry(registry, sep='/'):
    reg_tmp = registry.split(sep)
    reg_def = list(filter(None, reg_tmp))
    return reg_def
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Define path root for saving in registry file
def defineRootRegistry(filename, sep_start=None, sep_end=None):

    if sep_start is not None:
        path_start = filename.split(sep_start)[1]

        if path_start.startswith('/'):
            path_start = path_start[1:]

        path_start = os.path.join(sep_start, path_start)

        if not path_start.startswith('/'):
            path_start = os.path.join('/', path_start)

        path_root = os.path.split(path_start)[0]
    else:
        path_root = os.path.split(filename)[0]

    if sep_end is not None:

        path_end = path_root.split(sep_end)[0]

        if not path_end.endswith('/'):
            path_end = os.path.join(path_end, '/')

        path_end = os.path.join(path_end, sep_end)

        if not path_end.endswith('/'):
            path_end = os.path.join(path_end, '')

        path_root = path_end

    return path_root
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Merge data registry of two different simulation to have an unique data registry
def mergeDataRegistry(oDataRegistry1, oDataRegistry2):

    oDataRegistryMerged = {}

    for (oRegKey_1, oRegVal_1), (oRegKey_2, oRegVal_2) in zip(oDataRegistry1.items(), oDataRegistry2.items()):

        if oRegKey_1 == oRegKey_2:

            oRegKey_1_PAR = [oRegKey_1]
            oRegKey_2_PAR = [oRegKey_2]

            oRegKey_Merged = list(set(oRegKey_1_PAR + oRegKey_2_PAR))[0]

            if not oRegKey_Merged == 'geometry':

                if isinstance(oRegVal_1, list):
                    oRegVal_1_PAR = oRegVal_1
                elif isinstance(oRegVal_1, str):
                    oRegVal_1_PAR = [oRegVal_1]
                elif isinstance(oRegVal_1, Number):
                    oRegVal_1_PAR = [oRegVal_1]
                elif oRegVal_1 is None:
                    oRegVal_1_PAR = [oRegVal_1]
                else:
                    raise NotImplementedError(' Case not implemented for parsering data registry')

                if isinstance(oRegVal_2, list):
                    oRegVal_2_PAR = oRegVal_2
                elif isinstance(oRegVal_1, str):
                    oRegVal_2_PAR = [oRegVal_2]
                elif isinstance(oRegVal_2, Number):
                    oRegVal_2_PAR = [oRegVal_2]
                elif oRegVal_2 is None:
                    oRegVal_2_PAR = [oRegVal_2]
                else:
                    raise NotImplementedError(' Case not implemented for parsering values of data registry')

                if oRegVal_1_PAR.__len__() == 1 and oRegVal_2_PAR.__len__() == 1:
                    oRegVal_Merged = list(set(oRegVal_1_PAR + oRegVal_2_PAR))
                else:
                    oRegVal_Merged = oRegVal_1_PAR + oRegVal_2_PAR

                if oRegVal_Merged.__len__() == 1:
                    oRegVal_Merged = oRegVal_Merged[0]

            elif oRegKey_Merged == 'geometry':
                    oRegVal_Merged = oRegVal_1
            else:
                raise NotImplementedError(' Case not implemented for geometry object')

            oDataRegistryMerged[oRegKey_Merged] = oRegVal_Merged

        elif oRegKey_1 != oRegKey_2:

            oDataRegistryMerged[oRegKey_1] = oRegVal_1
            oDataRegistryMerged[oRegKey_2] = oRegVal_2

        else:
            raise NotImplementedError(' Case not implemented for parsering key(s) of data registry')

    return oDataRegistryMerged

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to wrap registry file writing
def wrapFileRegistry(oDataRegistry, sFileNameKey='filename', sFileDataKey='registry'):

    # Iterate over data registry
    for sVarData, oVarData in oDataRegistry.items():
        sVarFileName = oVarData[sFileNameKey]
        oVarFileData = oVarData[sFileDataKey]

        oVarFileLine = []
        for sVarFilePivot, oVarFileLevel in oVarFileData.items():
            sVarPivot = sVarFilePivot

            if any(isinstance(oElem, list) for oElem in oVarFileLevel):
                oVarList = [oElem[1] for oElem in oVarFileLevel]
                oVarList = sortListNatural(oVarList)
                oVarList = list(set(oVarList))
            else:
                oVarList = [oVarFileLevel[1]]

            a1sVarList = ','.join(oVarList)
            oVarLine = [';'.join([sVarPivot, a1sVarList])]
            oVarFileLine.append(oVarLine)

        if not os.path.exists(sVarFileName):
            createFolderByFile(sVarFileName)

        writeFileRegistry(sVarFileName, oVarFileLine)

# -------------------------------------------------------------------------------------
