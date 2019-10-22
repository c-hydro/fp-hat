"""
Library Features:

Name:          lib_settings
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '1.0.0'
"""

#######################################################################################
# Library
from os.path import join
from collections import OrderedDict
from copy import deepcopy

from src.common.utils.lib_utils_op_dict import getDictDeep, getDictValues

from src.common.default.lib_default_args import sPathDelimiter
from src.common.utils.lib_utils_op_system import createFolder

from src.common.driver.configuration.drv_configuration_debug import Exc
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to set file path(s)
def setPathFile(oFileValue, oFileKeyDef=None):

    oFileKeyOrder = OrderedDict(sorted(oFileKeyDef.items()))

    oFilePath = {}
    for sFileType, oFileType in oFileValue.items():

        oFilePart = []
        for sKey, sValue in oFileKeyOrder.items():

            oFileExt = getDictValues(oFileType, sValue)

            if oFileExt is not None:
                if not oFilePart:
                    oFilePart = oFileExt
                else:
                    oFilePart = join(oFilePart, oFileExt)

        if not oFilePart:
            oFilePart = None

        oFilePath[sFileType] = oFilePart

    return oFilePath
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get root path(s)
def selectDataSettings(oDataSettings, sPathKey='folder'):
    oDataGet = []
    oDataGet = getDictValues(oDataSettings, sPathKey, value=oDataGet)
    oDataSel = deepcopy(oDataGet)
    return oDataSel
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set root path(s)
def setPathRoot(oPathValue):

    for sPathValue in oPathValue:
        sPathRoot = sPathValue.split(sPathDelimiter)[0]
        createFolder(sPathRoot)

# -------------------------------------------------------------------------------------
