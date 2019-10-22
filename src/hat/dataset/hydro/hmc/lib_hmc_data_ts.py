"""
Library Features:

Name:          lib_hmc_data_ts
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190115'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import pandas as pd

from src.hat.default.lib_default_args import sLoggerName
from src.hat.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to get time series variable(s)
def getVarTimeSeries(sFileName, sFileField='section'):

    # Read time-series
    oFileTS = pd.read_table(sFileName, header=None, lineterminator='\n', names=['data'])

    a1oTS_TIME = []
    a2oTS_DATA = []

    for iI, oTS in enumerate(oFileTS['data']):
        oTS = oTS.split('\t')

        a1oTS_RAW = oTS[0].split()

        oTS_TIME = a1oTS_RAW[0]
        a1oTS_DATA = a1oTS_RAW[1:]
        a1dTS_DATA = [float(iI) for iI in a1oTS_DATA]

        a1oTS_TIME.append(oTS_TIME)
        a2oTS_DATA.append(a1dTS_DATA)

    iTS_N = a2oTS_DATA[0].__len__()

    oTS_Columns = [sFileField + "_{:}".format(iIdx) for iIdx in range(1, iTS_N + 1)]

    oTS_Data = pd.DataFrame(a2oTS_DATA)
    oTS_Data.columns = oTS_Columns

    oTS_Data = oTS_Data.set_index(pd.DatetimeIndex(pd.to_datetime(a1oTS_TIME)))

    return oTS_Data
# -------------------------------------------------------------------------------------
