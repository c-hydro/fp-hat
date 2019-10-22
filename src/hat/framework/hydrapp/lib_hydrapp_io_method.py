"""
Library Features:

Name:          lib_hydrapp_io_method
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190315'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging

import csv
import json
from numpy import int, int16, int32, int64, float, float16, float32, float64

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to write graph file in json format
def writeFileGraph_JSON(sFileName, oFileData):

    oFileData_PARSER = {}
    for sFileKey, oFileValue in oFileData.items():

        if isinstance(oFileValue, (int, int16, int32, int64, float, float16, float32, float64)):
            oFileValue_PARSER = str(oFileValue)
        elif isinstance(oFileValue, list):
            if oFileValue.__len__() == 1:
                oFileValue_PARSER = oFileValue[0]
            else:
                oFileValue_PARSER = ','.join(str(oElem) for oElem in oFileValue)
        elif isinstance(oFileValue, str):
            oFileValue_PARSER = oFileValue
        else:
            oFileValue_PARSER = None

        if sFileKey != 'geometry':
            if oFileValue_PARSER:
                oFileData_PARSER[sFileKey] = oFileValue_PARSER
            elif oFileValue_PARSER is None:
                oFileData_PARSER[sFileKey] = ""

    with open(sFileName, 'w') as oFile:
        json.dump(oFileData_PARSER, oFile)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write registry file in csv format
def writeFileRegistry(sFileName, oFileData):

    csv.register_dialect('registry_dialect')

    with open(sFileName, 'w') as oFile:
        oFileWriter = csv.writer(oFile, delimiter=' ', escapechar=' ', quoting=csv.QUOTE_NONE)
        oFileWriter.writerows(oFileData)

    oFile.close()

# -------------------------------------------------------------------------------------
