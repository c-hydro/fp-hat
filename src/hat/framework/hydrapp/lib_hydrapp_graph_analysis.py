"""
Library Features:

Name:          lib_hydrapp_graph_analysis
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190226'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging

import numpy as np
import pandas as pd

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute variable(s) peak(s)
def computeVarPeaks(oVar_DATA_DFrame, dVar_PEAK_MIN=0):

    oVar_DATA_COLS = list(oVar_DATA_DFrame.columns)

    oVar_PEAK_DFrame = pd.DataFrame(index=oVar_DATA_COLS, columns=['peak', 'time'])
    for sVar_DATA_COL in oVar_DATA_COLS:
        oVar_DATA_TS = oVar_DATA_DFrame[sVar_DATA_COL]

        oVar_PEAK_VALUE = oVar_DATA_TS.max(axis=0)
        oVar_PEAK_TIME = oVar_DATA_TS.idxmax(axis=0)

        if oVar_PEAK_VALUE > dVar_PEAK_MIN:
            oVar_PEAK_DFrame.loc[sVar_DATA_COL, 'peak'] = oVar_PEAK_VALUE
        oVar_PEAK_DFrame.loc[sVar_DATA_COL, 'time'] = oVar_PEAK_TIME

    return oVar_PEAK_DFrame

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute variable(s) quantile(s)
def computeVarQuantile(oVarData_ENSEMBLE, sVarData_QTL='qtls', oVarData_QTL=None, iVarAxis=1):

    if oVarData_QTL is None:
        oVarData_QTL = [0, 0.25, 0.5, 0.75, 1],

    oVarData_QTL = oVarData_ENSEMBLE.quantile(oVarData_QTL, axis=iVarAxis)

    for iVarID, iVarQTL in enumerate(oVarData_QTL.index):
        oVarData_ENSEMBLE[sVarData_QTL + str(iVarQTL)] = oVarData_QTL.values[iVarID]

    return oVarData_ENSEMBLE

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to detect data outlier
def detectVarOutlier(oVarData_ENSEMBLE):

    # Check first value of data frame of probabilistic simulation(s). All values must be the same.
    a1dVarData_ENSEMBLE_FIRST = oVarData_ENSEMBLE.values[0]
    a1dVarData_ENSEMBLE_UNIQUE, a1iVarData_ENSEMBLE_COUNT = np.unique(a1dVarData_ENSEMBLE_FIRST, return_counts=True)

    if a1dVarData_ENSEMBLE_UNIQUE.shape[0] > 1:

        a1iVarData_ENSEMBLE_COUNT_SORT = np.sort(a1iVarData_ENSEMBLE_COUNT)
        a1iVarData_ENSEMBLE_INDEX_SORT = np.argsort(a1iVarData_ENSEMBLE_COUNT)

        a1dVarData_ENSEMBLE_UNIQUE_SORT = a1dVarData_ENSEMBLE_UNIQUE[a1iVarData_ENSEMBLE_INDEX_SORT]

        a1iVarData_ENSEMBLE_COUNT_SORT = a1iVarData_ENSEMBLE_COUNT_SORT[::-1]
        a1dVarData_ENSEMBLE_UNIQUE_SORT = a1dVarData_ENSEMBLE_UNIQUE_SORT[::-1]

        a1bVarData_OUTLIER = np.full((a1dVarData_ENSEMBLE_UNIQUE.shape[0]), False, dtype=bool)
        for iVarData_ENSEMBLE_ID, (dVarData_ENSEMBLE_OUTLIER, iVarData_ENSEMBLE_COUNT) in enumerate(
                zip(a1dVarData_ENSEMBLE_UNIQUE_SORT[1:], a1iVarData_ENSEMBLE_COUNT_SORT[1:])):

            if not np.isnan(dVarData_ENSEMBLE_OUTLIER):
                iVarData_ENSEMBLE_OUTLIER = np.where(a1dVarData_ENSEMBLE_FIRST == dVarData_ENSEMBLE_OUTLIER)[0]
                sVarData_ENSEMBLE_OUTLIER = str(iVarData_ENSEMBLE_OUTLIER + 1)

                Exc.getExc(' =====> WARNING: in probabilistic simulation(s) ensemble ' + sVarData_ENSEMBLE_OUTLIER
                           + ' starts with outlier value ' + str(dVarData_ENSEMBLE_OUTLIER) + ' !', 2, 1)

                a1dVarData_OUTLIER = oVarData_ENSEMBLE.values[:, iVarData_ENSEMBLE_OUTLIER[0]]
                if a1dVarData_OUTLIER.size > 5:
                    a1iVarIdx_OUTLIER = [0, 1, 2, 3]
                else:
                    a1iVarIdx_OUTLIER = [0]

                a1sVarData_OUTLIER = ', '.join(str(dValue) for dValue in (np.take(a1dVarData_OUTLIER, a1iVarIdx_OUTLIER)))
                Exc.getExc(' =====> WARNING: ensemble with following starting values [' + a1sVarData_OUTLIER
                           + ' ... ] will be filtered! ', 2, 1)

                a1bVarData_OUTLIER[iVarData_ENSEMBLE_ID] = True
            else:
                a1bVarData_OUTLIER[iVarData_ENSEMBLE_ID] = False

        if np.any(a1bVarData_OUTLIER):
            bVarData_OUTLIER = True
        else:
            bVarData_OUTLIER = False
    else:
        bVarData_OUTLIER = False

    # Filter last values of data frame (to avoid some writing errors in closing ascii file)
    oVarData_ENSEMBLE.iloc[-1] = np.nan

    return oVarData_ENSEMBLE, bVarData_OUTLIER
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to filter data removing outliers from data frame
# https://stackoverflow.com/questions/35827863/remove-outliers-in-pandas-dataframe-using-percentiles
def filterVarOutlier(oVarData_ENSEMBLE, dVar_QTL_HIGH=0.99, iVarAxis=1):

    oVarData_QTL = oVarData_ENSEMBLE.quantile([0.0, dVar_QTL_HIGH], axis=iVarAxis)
    oVarData_FILTER = oVarData_ENSEMBLE.apply(lambda x: x[(x < oVarData_QTL.loc[dVar_QTL_HIGH, x.name])], axis=iVarAxis)

    return oVarData_FILTER

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to filter data masking values outside the limits
def filterVarLimit(oVar_DATA, oVar_META, dVar_MIN_OUTLIER=None, dVar_MAX_OUTLIER=None):

    if 'Valid_min' in oVar_META:
        dVar_RUN_MIN = oVar_META['Valid_min']
    else:
        dVar_RUN_MIN = None

    if 'Valid_max' in oVar_META:
        dVar_RUN_MAX = oVar_META['Valid_max']
    else:
        dVar_RUN_MAX = None

    if dVar_RUN_MIN is not None:
        oVar_DATA = oVar_DATA.where(oVar_DATA >= dVar_RUN_MIN)

    if dVar_RUN_MAX is not None:
        oVar_DATA = oVar_DATA.where(oVar_DATA <= dVar_RUN_MAX)

    if dVar_MIN_OUTLIER is not None:
        oVar_DATA = oVar_DATA.where(oVar_DATA >= dVar_MIN_OUTLIER)

    if dVar_MAX_OUTLIER is not None:
        oVar_DATA = oVar_DATA.where(oVar_DATA <= dVar_MAX_OUTLIER)

    return oVar_DATA
# -------------------------------------------------------------------------------------
