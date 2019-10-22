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

from src.hat.framework.hydrapp.lib_hydrapp_io_method import writeFileRegistry
from src.common.utils.lib_utils_op_system import createFolderByFile
from src.common.utils.lib_utils_op_list import sortListNatural

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


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
            oVarList = list(oVarFileLevel.values())[0]

            oVarList = sortListNatural(oVarList)

            a1sVarList = ','.join(oVarList)
            oVarLine = [';'.join([sVarPivot, a1sVarList])]
            oVarFileLine.append(oVarLine)

        if not os.path.exists(sVarFileName):
            createFolderByFile(sVarFileName)

        writeFileRegistry(sVarFileName, oVarFileLine)

# -------------------------------------------------------------------------------------
