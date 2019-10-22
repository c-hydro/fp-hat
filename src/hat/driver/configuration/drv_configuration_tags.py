"""
Class Features

Name:          drv_configuration_tags
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190220'
Version:       '2.0.8'
"""

#######################################################################################
# Library
import logging
from copy import deepcopy

from src.common.utils.lib_utils_apps_tags import updateTags
from src.common.utils.lib_utils_op_string import defineString

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Log
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Algorithm tags Data structure (undefined value is None)
oVarTags_Valid = dict(Year={'$yyyy': None},
                      Month={'$mm': None},
                      Day={'$dd': None},
                      Hour={'$HH': None},
                      Minute={'$MM': None},
                      VarName={'$VAR': None},
                      RunDomain={'$RUNDOMAIN': None},
                      RunName={'$RUNNAME': None},
                      RunTime={'$RUNTIME': None})
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
class DataObject(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class Tags
class DataTags:

    # -------------------------------------------------------------------------------------
    # Global Variable(s)
    oVarTags_OUT = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, oVarTags_IN):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.oVarTags_IN = oVarTags_IN
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set data tags
    def setDataTags(self):

        # Get tag(s) declaration(s)
        oVarTags_DEF = deepcopy(oVarTags_Valid)
        oVarTags_REF = deepcopy(self.oVarTags_IN)

        # Check tag(s) declaration(s)
        self.checkDataTags(oVarTags_REF, oVarTags_DEF)

        # Parser tag(s) declaration(s)
        oVarTags_OUT = updateTags(oVarTags_DEF, self.oVarTags_IN)

        return oVarTags_OUT
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to check data tag(s)
    @staticmethod
    def checkDataTags(oVarTags_REF, oVarTags_DEF):

        for sTagKey in list(oVarTags_DEF.keys()):
            sVarTag_DEF = list(oVarTags_DEF[sTagKey].keys())[0]

            if sVarTag_DEF not in list(oVarTags_REF.keys()):
                Exc.getExc(' =====> WARNING: valid key [' + sVarTag_DEF + '] is not defined in algorithm key', 2, 1)
            else:
                oVarTags_REF.pop(sVarTag_DEF)

        if oVarTags_REF.__len__() > 1:
            oListTags_UNDEF = list(oVarTags_REF.keys())
            a1sListTags_UNDEF = ','.join(oListTags_UNDEF)
            Exc.getExc(' =====> WARNING: key(s) ' + a1sListTags_UNDEF + ' are undefined! Check your settings!', 2, 1)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define data tag(s)
    @staticmethod
    def defineDataTags(sString, oTags):
        return defineString(sString, oTags)
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
