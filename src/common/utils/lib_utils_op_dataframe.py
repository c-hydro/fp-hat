"""
Library Features:

Name:          lib_generic_op_dataframe
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180517'
Version:       '0.0.1'
"""

#######################################################################################
# Library
import logging

import pandas as pd

from hmc.algorithm.default import sLoggerFormat

# Log
oLogStream = logging.getLogger(sLoggerFormat)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to convert dictionary to dataframe
def convertDict2DF(oDict):
    return pd.DataFrame.from_dict(oDict)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to cast dataframe columns
def castDF(oDF, sColumnName='Data', sColumnType='object'):

    if sColumnName is not None:
        if sColumnName in oDF.columns:
            if sColumnType == 'numeric':
                oDF[sColumnName] = oDF[sColumnName].apply(pd.to_numeric)
            if sColumnType == 'datetime':
                oDF[sColumnName] = oDF[sColumnName].apply(pd.to_datetime)
            if sColumnType == 'object':
                pass
            if sColumnType == 'string':
                pass
    return oDF
# -------------------------------------------------------------------------------------
