"""
Library Features:

Name:          lib_hydrapp_graph_configuration
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190226'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Definition of lookup table
oVarData_LookUp_TABLE_TS = {
    "oRain_OBS": ["rain_obs"],
    "oRain_NWP_DET": ["rain_nwp_deterministic"],
    "oRain_NWP_PROB": ["rain_nwp_probabilistic"],
    "oAirTemperature_OBS": ["air_temperature_obs"],
    "oDischarge_OBS": ["discharge_obs"],
    "oDischarge_MOD_OBS": ["discharge_model_obs"],
    "oDischarge_MOD_NWP_PROB": ["discharge_model_nwp_probabilistic"],
    "oDischarge_MOD_NWP_DET": ["discharge_model_nwp_deterministic"],
    "oDischarge_MOD_NWP_PROB_TYPE1": ["discharge_model_nwp_probabilistic_type1"],
    "oDischarge_MOD_NWP_PROB_TYPE2": ["discharge_model_nwp_probabilistic_type2"],
    "oDischarge_MOD_NWP_DET_TYPE1": ["discharge_model_nwp_deterministic_type1"],
    "oDischarge_MOD_NWP_DET_TYPE2": ["discharge_model_nwp_deterministic_type2"],
    "oSoilMoisture_OBS": ["sm_obs"],
    "oRain_Accumulated_OBS": ["rain_accumulated_obs"],
    "oRain_Accumulated_NWP_DET": ["rain_accumulated_nwp_deterministic"],
}
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to config fx argument(s)
def configVarArgs(oFxData):
    oFxArgs = {}
    for sVarData_LookUp_KEY, oVarData_LookUp_VALUE in oVarData_LookUp_TABLE_TS.items():

        for sVarData_LookUp_VALUE in oVarData_LookUp_VALUE:
            if sVarData_LookUp_VALUE in oFxData.keys():
                oVarData = oFxData[sVarData_LookUp_VALUE]
                oFxArgs[sVarData_LookUp_KEY] = oVarData
                break
    return oFxArgs
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to config data time-series time(s)
def configGraphTime_TS(oDataValue, sTimeFormat='%m-%d %H'):

    oTickTimePeriod = list(oDataValue.index)
    oTickIdx = oDataValue.index
    oTickLabels = [sTickLabel.strftime(sTimeFormat) for sTickLabel in oDataValue.index]

    return oTickTimePeriod, oTickIdx, oTickLabels
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to config data time-series value(s)
def configGraphData_TS(oDataObj=None):

    if oDataObj is not None:
        oDataName = list(oDataObj.columns)

        if hasattr(oDataObj, '_metadata'):
            oDataMeta = getattr(oDataObj, '_metadata')
        else:
            oDataMeta = None
        if oDataName.__len__() == 1:
            for sDataName in oDataName:
                oDataValue = oDataObj[sDataName]
        else:
            oDataValue = oDataObj

        oDataAttrs = {}
        if oDataMeta is not None:
            for sDataMeta in oDataMeta:
                if hasattr(oDataObj, sDataMeta):
                    oDataMeta = getattr(oDataObj, sDataMeta)
                    oDataAttrs[sDataMeta] = oDataMeta
        else:
            oDataAttrs = None
    else:
        oDataValue = None
        oDataAttrs = None
    return oDataValue, oDataAttrs
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to config data time-series header
def configGraphHeader_TS(oDataAttrs):

    oDataHeader = {}
    if "SEC_NAME" in oDataAttrs.keys():
        oDataHeader['section_name'] = oDataAttrs['SEC_NAME']
    if "BASIN" in oDataAttrs.keys():
        oDataHeader['section_basin'] = oDataAttrs['BASIN']
    if "AREA" in oDataAttrs.keys():
        oDataHeader['section_area'] = str(oDataAttrs['AREA'])
    if "Q_THR1" in oDataAttrs.keys():
        oDataHeader['section_q_thr1'] = str(oDataAttrs['Q_THR1'])
    if "Q_THR2" in oDataAttrs.keys():
        oDataHeader['section_q_thr2'] = str(oDataAttrs['Q_THR2'])

    return oDataHeader


# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to config data gridded value(s)
def configGraphData_Gridded(oDataObj=None):

    # Reduce data to 2d (check for time == 1)
    if (oDataObj.ndim == 3) and ('time' in list(oDataObj.coords)):
        if oDataObj['time'].size == 1:
            oVarObj = oDataObj[0, :, :]
        else:
            Exc.getExc(' =====> ERROR: time coordinate is greater then 1 step! Data array is not in 2d format', 1, 1)
    elif oDataObj.ndim == 2:
        oVarObj = oDataObj
    else:
        Exc.getExc(' =====> ERROR: data array is not in 2d format!', 1, 1)

    # Get variable name
    sVarName = oVarObj.name
    # Get variable data
    a2dVarData = oVarObj.values

    # Get longitude data
    if 'Longitude' in list(oVarObj.coords):
        a2dVarLons = oVarObj['Longitude'].values
    else:
        Exc.getExc(' =====> ERROR: longitude is not defined in data array in graph preparation!', 1, 1)
    # Get latitude data
    if 'Latitude' in list(oVarObj.coords):
        a2dVarLats = oVarObj['Latitude'].values
    else:
        Exc.getExc(' =====> ERROR: latitude is not defined in data array in graph preparation!', 1, 1)
    # Get attribute(s) data
    oVarAttrs = {}
    for sVarKey, oVarData in oDataObj.attrs.items():
        oVarAttrs[sVarKey] = oVarData

    return sVarName, a2dVarData, a2dVarLons, a2dVarLats, oVarAttrs
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to config data gridded header
def configGraphHeader_Gridded(oVarAttrs):

    oVarHeader = {}

    if "units" in oVarAttrs.keys():
        oVarHeader['map_units'] = oVarAttrs['units']
    if "time_run" in oVarAttrs.keys():
        oVarHeader['map_time_run'] = oVarAttrs['time_run']
    if "time_dataset" in oVarAttrs.keys():
        oVarHeader['map_time_dataset'] = oVarAttrs['time_dataset']
    if "Valid_min" in oVarAttrs.keys():
        oVarHeader['map_valid_min'] = str(oVarAttrs['Valid_min'])
    if "Valid_max" in oVarAttrs.keys():
        oVarHeader['map_valid_max'] = str(oVarAttrs['Valid_max'])
    if "Valid_range" in oVarAttrs.keys():
        oVarHeader['map_valid_range'] = str(oVarAttrs['Valid_range'])
    if "Missing_value" in oVarAttrs.keys():
        oVarHeader['map_missing_value'] = str(oVarAttrs['Missing_value'])

    return oVarHeader
# -------------------------------------------------------------------------------------
