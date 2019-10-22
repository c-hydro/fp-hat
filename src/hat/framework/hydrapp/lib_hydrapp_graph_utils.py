"""
Library Features:

Name:          lib_hydrapp_graph_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190226'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging

import numpy as np
from math import ceil

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################

# -------------------------------------------------------------------------------------
# Default settings
dVarRain_DEFAULT_MIN = 0.0
dVarRain_DEFAULT_MAX = 5.0

dVarRain_RANGE_MIN = 0.0
dVarRain_RANGE_MAX = 1000.0
dVarRain_RANGE_DELTA = 5.0

dVarDischarge_DEFAULT_MIN = 0.0
dVarDischarge_DEFAULT_MAX = np.nan

dVarDischarge_RANGE_MIN = 0.0
dVarDischarge_RANGE_MAX = 5000.0
dVarDischarge_RANGE_DELTA = 5.0
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set graph range for rain variable
def setGraphRange_Rain(oVar_META):

    if 'min' in oVar_META:
        dVar_RUN_MIN = oVar_META['min']
    else:
        dVar_RUN_MIN = np.nan

    if 'max' in oVar_META:
        dVar_RUN_MAX = oVar_META['max']
    else:
        dVar_RUN_MAX = np.nan

    if 'Valid_min' in oVar_META:
        dVar_VALID_MIN = oVar_META['Valid_min']
    else:
        dVar_VALID_MIN = np.nan

    if 'Valid_max' in oVar_META:
        dVar_VALID_MAX = oVar_META['Valid_max']
    else:
        dVar_VALID_MAX = np.nan

    if 'Valid_range' in oVar_META:
        if oVar_META['Valid_range'] is not None:
            dVar_VALID_MIN = oVar_META['Valid_range'][0]
            dVar_VALID_MAX = oVar_META['Valid_range'][1]

    dGraph_RANGE_MIN = np.nanmin([dVarRain_DEFAULT_MIN, dVar_RUN_MIN, dVar_VALID_MIN])
    dGraph_RANGE_MAX = np.nanmax([dVarRain_DEFAULT_MAX, dVar_RUN_MAX, dVar_VALID_MAX])

    iVar_RANGE_SAMPLE = int((dVarRain_RANGE_MAX - dVarRain_RANGE_MIN) / dVarRain_RANGE_DELTA) + 1
    a1dVar_RANGE = np.linspace(dVarRain_RANGE_MIN, dVarRain_RANGE_MAX, iVar_RANGE_SAMPLE, endpoint=True)
    try:
        iGraph_IDX_MAX_LB = (np.abs(a1dVar_RANGE - dGraph_RANGE_MAX)).argmin()
    except Warning:
        iGraph_IDX_MAX_LB = 0
    try:
        iGraph_IDX_MAX_UB = (np.abs(a1dVar_RANGE - dGraph_RANGE_MAX)).argmin() + 1
    except Warning:
        iGraph_IDX_MAX_UB = a1dVar_RANGE.size

    if dGraph_RANGE_MAX <= a1dVar_RANGE[iGraph_IDX_MAX_LB]:
        dGraph_RANGE_MAX = a1dVar_RANGE[iGraph_IDX_MAX_LB]
    else:
        dGraph_RANGE_MAX = a1dVar_RANGE[iGraph_IDX_MAX_UB]

    return dGraph_RANGE_MIN, dGraph_RANGE_MAX
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set graph range for discharge variable
def setGraphRange_Discharge(oVar_META, dVar_NODATA=-9999.0, dVar_MIN_OUTLIER=None, dVar_MAX_OUTLIER=None):

    if 'min' in oVar_META:
        dVar_RUN_MIN = oVar_META['min']
        if dVar_MIN_OUTLIER is not None:
            if dVar_RUN_MIN < dVar_MIN_OUTLIER:
                dVar_RUN_MIN = np.nan
    else:
        dVar_RUN_MIN = np.nan

    if 'max' in oVar_META:
        dVar_RUN_MAX = oVar_META['max']
        if dVar_MAX_OUTLIER is not None:
            if dVar_RUN_MAX > dVar_MAX_OUTLIER:
                dVar_RUN_MAX = np.nan
    else:
        dVar_RUN_MAX = np.nan

    if 'Valid_min' in oVar_META:
        dVar_VALID_MIN = oVar_META['Valid_min']
    else:
        dVar_VALID_MIN = np.nan

    if 'Valid_max' in oVar_META:
        dVar_VALID_MAX = oVar_META['Valid_max']
    else:
        dVar_VALID_MAX = np.nan

    if 'Q_THR1' in oVar_META:
        dVar_THR1 = oVar_META['Q_THR1']
        if dVar_THR1 == dVar_NODATA:
            dVar_THR1 = np.nan
    else:
        dVar_THR1 = np.nan
    if 'Q_THR2' in oVar_META:
        dVar_THR2 = oVar_META['Q_THR2']
        if dVar_THR2 == dVar_NODATA:
            dVar_THR2 = np.nan
    else:
        dVar_THR2 = np.nan
    if 'Q_THR3' in oVar_META:
        dVar_THR3 = oVar_META['Q_THR3']
        if dVar_THR3 == dVar_NODATA:
            dVar_THR3 = np.nan
    else:
        dVar_THR3 = np.nan

    if np.isnan([dVar_THR1, dVar_THR2, dVar_THR3]).all():
        dGraph_THR_MAX_LB = np.nan
        Exc.getExc(' =====> WARNING: all discharge threshold(s) are null. ', 2, 1)
    else:
        dGraph_THR_MAX_LB = np.nanmax([dVar_THR1, dVar_THR2, dVar_THR3])
    if np.isnan(dGraph_THR_MAX_LB):
        dGraph_THR_MAX_UB = np.nan
    else:
        dGraph_THR_MAX_UB = dGraph_THR_MAX_LB + (dGraph_THR_MAX_LB/100) * 20

    if not np.isnan(dVar_VALID_MIN):
        if dVar_RUN_MIN < dVar_VALID_MIN:
            dVar_RUN_MIN = dVar_VALID_MIN
    if not np.isnan(dVar_VALID_MAX):
        if dVar_RUN_MAX > dVar_VALID_MAX:
            dVar_RUN_MAX = dVar_VALID_MAX

    dGraph_RANGE_MIN = np.nanmin([dVarDischarge_DEFAULT_MIN, dVar_RUN_MIN, dVar_VALID_MIN])

    if np.isnan([dVarDischarge_DEFAULT_MAX, dVar_RUN_MAX, dVar_VALID_MAX, dGraph_THR_MAX_UB]).all():
        dGraph_RANGE_MAX = dVarDischarge_RANGE_DELTA
        Exc.getExc(' =====> WARNING: all discharge values in searching graph maximum value are null. ', 2, 1)
    else:
        dGraph_RANGE_MAX = np.nanmax([dVarDischarge_DEFAULT_MAX, dVar_RUN_MAX, dVar_VALID_MAX, dGraph_THR_MAX_UB])
    dGraph_RANGE_MAX = ceil(dGraph_RANGE_MAX)

    if dVarDischarge_RANGE_DELTA > dGraph_RANGE_MAX:
        dGraph_RANGE_MAX = dVarDischarge_RANGE_DELTA

    iVar_RANGE_SAMPLE = int((dGraph_RANGE_MAX - dGraph_RANGE_MIN) / dVarDischarge_RANGE_DELTA) + 1
    a1dVar_RANGE = np.linspace(dGraph_RANGE_MIN, dGraph_RANGE_MAX, iVar_RANGE_SAMPLE, endpoint=True)

    dGraph_RANGE_MIN = np.nanmin([dGraph_RANGE_MIN, dVar_RUN_MIN, dVar_VALID_MIN])
    dGraph_RANGE_MAX = np.nanmax([dGraph_RANGE_MAX, dVar_RUN_MAX, dVar_VALID_MAX])

    try:
        iGraph_IDX_MAX_LB = (np.abs(a1dVar_RANGE - dGraph_RANGE_MAX)).argmin()
    except Warning:
        iGraph_IDX_MAX_LB = 0
    try:
        iGraph_IDX_MAX_UB = (np.abs(a1dVar_RANGE - dGraph_RANGE_MAX)).argmin() + 1
    except Warning:
        iGraph_IDX_MAX_UB = a1dVar_RANGE.size

    if dGraph_RANGE_MAX <= a1dVar_RANGE[iGraph_IDX_MAX_LB]:
        dGraph_RANGE_MAX = a1dVar_RANGE[iGraph_IDX_MAX_LB]
    else:
        dGraph_RANGE_MAX = a1dVar_RANGE[iGraph_IDX_MAX_UB] + (dGraph_RANGE_MAX/100) * 20

    dGraph_RANGE_MIN = ceil(dGraph_RANGE_MIN)
    dGraph_RANGE_MAX = ceil(dGraph_RANGE_MAX)

    return dGraph_RANGE_MIN, dGraph_RANGE_MAX
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set graph range for generic variable
def setGraphRange_Generic(oVar_META):

    if 'min' in oVar_META:
        dVar_RUN_MIN = oVar_META['min']
    else:
        dVar_RUN_MIN = np.nan

    if 'max' in oVar_META:
        dVar_RUN_MAX = oVar_META['max']
    else:
        dVar_RUN_MAX = np.nan

    if 'Valid_min' in oVar_META:
        dVar_VALID_MIN = oVar_META['Valid_min']
    else:
        dVar_VALID_MIN = dVar_RUN_MIN

    if 'Valid_max' in oVar_META:
        dVar_VALID_MAX = oVar_META['Valid_max']
    else:
        dVar_VALID_MAX = dVar_RUN_MAX

    if 'Valid_range' in oVar_META:
        dVar_VALID_MIN = oVar_META['Valid_range'][0]
        dVar_VALID_MAX = oVar_META['Valid_range'][1]

    dGraph_RANGE_MIN = dVar_VALID_MIN
    dGraph_RANGE_MAX = dVar_VALID_MAX

    return dGraph_RANGE_MIN, dGraph_RANGE_MAX
# -------------------------------------------------------------------------------------
