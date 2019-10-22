"""
Library Features:

Name:          lib_hmc_method_cmp_gridded
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190708'
Version:       '1.0.2'
"""

#######################################################################################
# Library
import logging
import warnings
import numpy as np
import pandas as pd
import xarray as xr

from src.hat.dataset.generic.lib_generic_io_utils import clipVarMD

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute gridded step data
def cmpVarStep(oVarData, oVarMask, oVarTime=None, sVarIdx='last', oVarAttributes=None):

    # Define mask
    oVarMask = np.where(np.isnan(oVarMask), -9999.0, oVarMask)

    # Insert mask in data workspace
    oVarMask = xr.DataArray(oVarMask, dims=['south_north', 'west_east'],
                            coords={'Longitude': (['south_north', 'west_east'], oVarData.Longitude),
                                    'Latitude': (['south_north', 'west_east'], oVarData.Latitude)})
    # oVarData.coords['Mask'] = (('south_north', 'west_east'), oVarMask)
    oVarData['Mask'] = oVarMask
    oVarData = oVarData.where(oVarData.Mask > 0)

    # Apply valid range to data array variable
    if oVarAttributes:
        if 'Valid_range' in oVarAttributes:
            oVarVR = oVarAttributes['Valid_range']
            oVarData = clipVarMD(oVarData, oVarVR)
            oVarData = oVarData.where(oVarData.Mask > 0)

    if isinstance(sVarIdx, list):
        sVarIdx = sVarIdx[0]

    if sVarIdx == 'first':
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            a1oVarIdx = np.where(oVarData.mean(dim=['south_north', 'west_east']).values >= 0)
        if a1oVarIdx[0].size > 0:
            iVarIdx = np.int32(np.min(a1oVarIdx))
            if isinstance(iVarIdx, np.int32):
                oVarIdx_SEL = [iVarIdx]
            else:
                oVarIdx_SEL = None
        else:
            oVarIdx_SEL = None

    elif sVarIdx == 'last':

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            a1oVarIdx = np.where(oVarData.mean(dim=['south_north', 'west_east']).values >= 0)
        if a1oVarIdx[0].size > 0:
            iVarIdx = np.int32(np.max(a1oVarIdx))
            if isinstance(iVarIdx, np.int32):
                oVarIdx_SEL = [iVarIdx]
            else:
                oVarIdx_SEL = None
        else:
            oVarIdx_SEL = None

    elif sVarIdx == 'all':
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            a1oVarIdx = np.where(oVarData.mean(dim=['south_north', 'west_east']).values >= 0)
        if a1oVarIdx[0].size > 0:
            if isinstance(a1oVarIdx, tuple):
                oVarIdx_SEL = list(a1oVarIdx[0])
            else:
                oVarIdx_SEL = None
        else:
            oVarIdx_SEL = None

    if oVarIdx_SEL is not None:
        oVarData_SEL = oVarData.isel(time=oVarIdx_SEL)
        oVarTime_SEL = oVarData_SEL.time.values
        # a1dVarData_TEST = list(oVarData.mean(dim=['south_north', 'west_east']).values)
        # dVarData_TEST = oVarData_SEL.mean(dim=['south_north', 'west_east']).values
    else:
        oVarData_SEL = None
        oVarTime_SEL = None

    # Add time coordinate(s) and dimension
    if oVarTime_SEL is not None:
        if 'time' not in oVarData_SEL.dims:
            oVarData_SEL = oVarData_SEL.assign_coords(time=pd.to_datetime(oVarTime_SEL))
            oVarData_SEL.coords['time'] = oVarData_SEL.coords['time'].astype('datetime64[ns]')
            # oVarData_SEL.coords['time'].attrs['calendar'] = 'gregorian'
            oVarData_SEL = oVarData_SEL.expand_dims(dim='time')
        else:
            oVarData_SEL = oVarData_SEL.assign_coords(time=pd.to_datetime(oVarTime_SEL))
            oVarData_SEL.coords['time'] = oVarData_SEL.coords['time'].astype('datetime64[ns]')
            # oVarData_SEL.coords['time'].attrs['calendar'] = 'gregorian'

    return oVarData_SEL
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute gridded accumulated data
def cmpVarAccumulated(oVarData, oVarMask, oVarTime=None, sVarDim='time', oVarAttributes=None):

    # Define mask
    oVarMask = np.where(np.isnan(oVarMask), -9999.0, oVarMask)

    # Insert mask in data workspace
    oVarMask = xr.DataArray(oVarMask, dims=['south_north', 'west_east'],
                            coords={'Longitude': (['south_north', 'west_east'], oVarData.Longitude),
                                    'Latitude': (['south_north', 'west_east'], oVarData.Latitude)})

    # oVarData.coords['Mask'] = (('south_north', 'west_east'), oVarMask)
    oVarData['Mask'] = oVarMask
    oVarData = oVarData.where(oVarData.Mask > 0)

    # Apply valid range to data array variable
    if oVarAttributes:
        if 'Valid_range' in oVarAttributes:
            oVarVR = oVarAttributes['Valid_range']
            oVarData = clipVarMD(oVarData, oVarVR)

    # Compute accumulated data
    oVarData_CMP = oVarData.sum(dim=sVarDim)
    oVarData_CMP = oVarData_CMP.where(oVarData.Mask > 0)

    # Add time coordinate(s) and dimension
    if oVarTime is not None:
        if 'time' not in oVarData_CMP.dims:
            oVarData_CMP = oVarData_CMP.assign_coords(time=pd.to_datetime(oVarTime))
            oVarData_CMP.coords['time'] = oVarData_CMP.coords['time'].astype('datetime64[ns]')
            #oVarData_CMP.coords['time'].attrs['calendar'] = 'gregorian'
            oVarData_CMP = oVarData_CMP.expand_dims(dim='time')

    return oVarData_CMP

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute gridded average data
def cmpVarMean(oVarData, oVarMask, oVarTime=None, sVarDim='time', oVarAttributes=None):

    # Define mask
    oVarMask = np.where(np.isnan(oVarMask), -9999.0, oVarMask)

    # Insert mask in data workspace
    oVarMask = xr.DataArray(oVarMask, dims=['south_north', 'west_east'],
                            coords={'Longitude': (['south_north', 'west_east'], oVarData.Longitude),
                                    'Latitude': (['south_north', 'west_east'], oVarData.Latitude)})
    # oVarData.coords['Mask'] = (('south_north', 'west_east'), oVarMask)
    oVarData['Mask'] = oVarMask
    oVarData = oVarData.where(oVarData.Mask > 0)

    # Apply valid range to data array variable
    if oVarAttributes:
        if 'Valid_range' in oVarAttributes:
            oVarVR = oVarAttributes['Valid_range']
            oVarData = clipVarMD(oVarData, oVarVR)

    # Compute accumulated data
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        oVarData_CMP = oVarData.mean(dim=sVarDim)
        oVarData_CMP = oVarData_CMP.where(oVarData.Mask > 0)

    # Add time coordinate(s) and dimension
    if oVarTime is not None:
        if 'time' not in oVarData_CMP.dims:
            oVarData_CMP = oVarData_CMP.assign_coords(time=pd.to_datetime(oVarTime))
            oVarData_CMP.coords['time'] = oVarData_CMP.coords['time'].astype('datetime64[ns]')
            # oVarData_CMP.coords['time'].attrs['calendar'] = 'gregorian'
            oVarData_CMP = oVarData_CMP.expand_dims(dim='time')

    return oVarData_CMP

# -------------------------------------------------------------------------------------
