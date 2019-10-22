"""
Library Features:

Name:          lib_generic_configuration_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190125'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import inspect
import glob
import pandas as pd
import os
from copy import deepcopy
from os.path import join

from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import mergeDict

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to configure fx to get data
def configVarFx(sVarFxName, oVarFxLibrary, kwargs):

    # Get and parser variable
    if hasattr(oVarFxLibrary, sVarFxName):

        if kwargs is not None:
            oFxArgs = kwargs
        else:
            oFxArgs = None

        oFxObj = getattr(oVarFxLibrary, sVarFxName)
        oFxSign = inspect.signature(oFxObj)

        oFxParams = {}
        for sFxParamsKey, oFxParamValue in oFxSign.parameters.items():
            if sFxParamsKey in list(oFxArgs.keys()):
                oFxParams[sFxParamsKey] = oFxArgs[sFxParamsKey]
            else:
                oFxParams[sFxParamsKey] = oFxParamValue.default

        oDataObj = oFxObj(**oFxParams)

        return oDataObj

    else:
        # Exit for error in defining methods to get data
        Exc.getExc(' =====> ERROR: selected method ' + sVarFxName +
                   ' not available in ' + str(oVarFxLibrary) + ' library', 1, 1)

# -------------------------------------------------------------------------------------
