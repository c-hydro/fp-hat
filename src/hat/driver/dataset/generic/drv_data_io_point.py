"""
Class Features

Name:          drv_data_io_point
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190109'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import numpy as np
import pandas as pd

from os.path import isfile, join

from src.common.utils.lib_utils_apps_geo import defineGeoGrid, defineGeoCorner, readGeoHeader

from src.common.utils.lib_utils_apps_land import computeCellArea, computeDrainageArea

from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_system import createFolderByFile

from src.common.driver.dataset.drv_data_io_type import Drv_Data_IO

from src.common.driver.configuration.drv_configuration_debug import Exc
from src.common.default.lib_default_args import sLoggerName

from src.hat.dataset.generic.lib_generic_io_utils import createVar2D, mergeVar2D
from src.hat.dataset.generic.lib_generic_io_method import writeFileNC4, readFileNC4

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Class Data object
class DataObj(object):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class DataPoint
class DataPoint:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, **kwargs):

        # Pass variable to global class
        self.__sFileName_SHP = kwargs['file_shp']
        self.__sFileName_MASK = kwargs['file_mask']
        self.__sFileName_TERRAIN = kwargs['file_terrain']
        self.__sFileName_CTIME = kwargs['file_ctime']
        self.__sFileName_ANC = kwargs['file_ancillary']
        self.__oFileField = kwargs['fields']

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get point data
    def getDataPoint(self, oDataGeo):

        # -------------------------------------------------------------------------------------
        # Info start
        oLogStream.info(' ---> Get point data ... ')

        # Method to check class input
        bFileName = self.__checkInput()

        # Read points file
        if bFileName and isfile(self.__sFileName_SHP):
            oDataPoint_SOURCE = self.__readPointInfo()
        else:
            oDataPoint_SOURCE = None
            Exc.getExc(' =====> ERROR: filename is undefined! (' + self.__sFileName_SHP + ')', 1, 1)

        # Read mask file(s)
        oDataPoint_OUTCOME = self.__savePointInfo(oDataPoint_SOURCE, oDataGeo)

        # Info end
        oLogStream.info(' ---> Get point data ... OK')

        # Return variable(s)
        return oDataPoint_OUTCOME
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get point information using an shapefile
    def __readPointInfo(self):

        # Open shapefile data
        oFileDriver = Drv_Data_IO(self.__sFileName_SHP).oFileWorkspace
        oFileData = oFileDriver.oFileLibrary.openFile(join(oFileDriver.sFilePath, oFileDriver.sFileName))
        # Select shapefile data
        oFileDF = oFileDriver.oFileLibrary.getData(oFileData)

        return oFileDF
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Save point and spatial information
    def __savePointInfo(self, oDataPoint, oDataGeo):

        # -------------------------------------------------------------------------------------
        # Initialise section workspace
        oDataPoint['SEC_FILE_ANCILLARY'] = None
        oDataPoint['SEC_FILE_TERRAIN'] = None
        oDataPoint['SEC_FILE_CTIME'] = None
        oDataPoint['SEC_FILE_MASK'] = None
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over section(s)
        for iSectionID, oSectionPoint in enumerate(oDataPoint.iterrows()):

            # -------------------------------------------------------------------------------------
            # Define section info
            oSectionData = oSectionPoint[1]
            sSectionName = oSectionData['SEC_TAG']
            sSectionName = sSectionName.lower().replace(':', '')

            # Info start
            oLogStream.info(' ----> Save point info for section ' + sSectionName + ' ... ')
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Define filename(s)
            sFileName_MASK = defineString(self.__sFileName_MASK, {'$section': sSectionName})
            sFileName_TERRAIN = defineString(self.__sFileName_TERRAIN, {'$section': sSectionName})
            sFileName_CTIME = defineString(self.__sFileName_CTIME, {'$section': sSectionName})
            sFileName_ANC = defineString(self.__sFileName_ANC, {'$section': sSectionName})
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check ancillary section file availability
            if not isfile(sFileName_ANC):

                # -------------------------------------------------------------------------------------
                # Get mask information
                if isfile(sFileName_MASK):
                    # Open ascii grid data
                    oFileDriver = Drv_Data_IO(sFileName_MASK).oFileWorkspace
                    oFileData = oFileDriver.oFileLibrary.openFile(
                        join(oFileDriver.sFilePath, oFileDriver.sFileName), 'r')
                    # Read ascii grid data
                    [a2iVarMask, a1oHeaderMask] = oFileDriver.oFileLibrary.readArcGrid(oFileData)
                    a2iVarMask = np.flipud(a2iVarMask)
                else:
                    Exc.getExc(' =====> WARNING: file mask undefined (' + sFileName_MASK + ')', 2, 1)
                    a2iVarMask = None
                    a1oHeaderMask = None

                # Get terrain information
                if isfile(sFileName_TERRAIN):
                    # Open ascii grid data
                    oFileDriver = Drv_Data_IO(sFileName_TERRAIN).oFileWorkspace
                    oFileData = oFileDriver.oFileLibrary.openFile(
                        join(oFileDriver.sFilePath, oFileDriver.sFileName), 'r')
                    # Read ascii grid data
                    [a2dVarTerrain, a1oHeaderTerrain] = oFileDriver.oFileLibrary.readArcGrid(oFileData)
                    a2dVarTerrain = np.flipud(a2dVarTerrain)
                else:
                    Exc.getExc(' =====> WARNING: file terrain undefined (' + sFileName_TERRAIN + ')', 2, 1)
                    a2dVarTerrain = None
                    a1oHeaderTerrain = None

                # Get corrivation time information
                if isfile(sFileName_CTIME):
                    # Open ascii grid data
                    oFileDriver = Drv_Data_IO(sFileName_CTIME).oFileWorkspace
                    oFileData = oFileDriver.oFileLibrary.openFile(
                        join(oFileDriver.sFilePath, oFileDriver.sFileName), 'r')
                    # Read ascii grid data
                    [a2dVarCorrTime, a1oHeaderCorrTime] = oFileDriver.oFileLibrary.readArcGrid(oFileData)
                    a2dVarCorrTime = np.flipud(a2dVarCorrTime)
                else:
                    Exc.getExc(' =====> WARNING: file corrivation_time undefined (' + sFileName_CTIME + ')', 2, 1)
                    a2dVarCorrTime = None
                    a1oHeaderCorrTime = None
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Check mask, terrain and corrivation time information
                if (a2iVarMask is not None) and (a2dVarCorrTime is not None) and (a2dVarTerrain is not None):

                    # -------------------------------------------------------------------------------------
                    # Read geographical header
                    [iRows, iCols, dGeoXMin, dGeoYMin, dGeoXStep, dGeoYStep, dNoData] = readGeoHeader(a1oHeaderTerrain)
                    # Define geographical corners
                    [dGeoXMin, dGeoXMax, dGeoYMin, dGeoYMax] = defineGeoCorner(dGeoXMin, dGeoYMin,
                                                                               dGeoXStep, dGeoYStep, iCols, iRows)
                    # Define geographical grid
                    [a2dGeoX, a2dGeoY, a1dGeoBox] = defineGeoGrid(dGeoYMin, dGeoXMin, dGeoYMax, dGeoXMax,
                                                                  dGeoYStep, dGeoXStep)
                    # Compute section drainage area
                    a2dCellArea = computeCellArea(a2dGeoY, dGeoXStep, dGeoYStep)
                    dCellArea = np.nanmean(a2dCellArea)
                    dDrainageArea = computeDrainageArea(a2dVarTerrain, dCellArea)

                    # Add drainage area to attribute(s)
                    oSectionData['DrainageArea'] = dDrainageArea
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Define encoding
                    oGeoEncoding = {'Mask': {'_FillValue': a1oHeaderMask['NODATA_value']},
                                    'Terrain': {'_FillValue': a1oHeaderTerrain['NODATA_value']},
                                    'CorrTime': {'_FillValue': a1oHeaderCorrTime['NODATA_value']}}
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Create data array for mask
                    oVarMask = createVar2D(a2iVarMask, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                           sVarName='Mask')
                    # Create data array for terrain
                    oVarTerrain = createVar2D(a2dVarTerrain, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                              sVarName='Terrain')
                    # Create data array for channel network
                    oVarCorrTime = createVar2D(a2dVarCorrTime, oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                               sVarName='CorrTime')
                    # Merge data arrays in a common dataset
                    oVarDSet = mergeVar2D([oVarMask, oVarTerrain, oVarCorrTime])

                    # Add attribute to section dataset
                    for oSectionKey, oSectionValue in oSectionData.items():
                        if oSectionKey != 'geometry':
                            if oSectionValue is not None:
                                oVarDSet.attrs[oSectionKey] = oSectionValue
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Save data in a netcdf file
                    if not isfile(sFileName_ANC):
                        createFolderByFile(sFileName_ANC)
                        sVarMode = 'w'
                    else:
                        sVarMode = 'a'

                    # Dump data to netcdf file
                    writeFileNC4(sFileName_ANC, oVarDSet, oVarAttr=oGeoEncoding, sVarGroup=None,
                                 sVarMode=sVarMode, oVarEngine='h5netcdf', iVarCompression=9)

                    # Info end
                    oLogStream.info(' ----> Save point info for section ' + sSectionName + ' ... OK')
                    # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Info exit
                    Exc.getExc(' =====> WARNING: not enough information to save info section file', 2, 1)
                    oLogStream.info(' ----> Save point info for section ' + sSectionName + ' ... FAILED')
                    # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Info skip
                oLogStream.info(' ----> Save point info ... previously done. SKIPPED')

                # Get data processed previously to extract some information
                oFileHandle = readFileNC4(sFileName_ANC)
                if hasattr(oFileHandle, 'DrainageArea'):
                    dDrainageArea = getattr(oFileHandle, 'DrainageArea')
                else:
                    dDrainageArea = -9999.0
                    Exc.getExc(' =====> WARNING: drainage area value not available! Set to -9999.0', 2, 1)
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Update data point with defined filename
            oDataPoint.at[iSectionID, 'OUTLET_FILE_ANCILLARY'] = sFileName_ANC
            oDataPoint.at[iSectionID, 'OUTLET_FILE_TERRAIN'] = sFileName_TERRAIN
            oDataPoint.at[iSectionID, 'OUTLET_FILE_CTIME'] = sFileName_CTIME
            oDataPoint.at[iSectionID, 'OUTLET_FILE_MASK'] = sFileName_MASK
            oDataPoint.at[iSectionID, 'OUTLET_NAME'] = sSectionName
            oDataPoint.at[iSectionID, 'DrainageArea'] = dDrainageArea
            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Sort data point using BASIN and DrainageArea as pivot(s)
        oDataPoint_SORT = oDataPoint.sort_values(['BASIN', 'DrainageArea'])
        oDataPoint_SORT['HAT_ELEMENT'] = oDataPoint_SORT.groupby('BASIN')['BASIN'].transform('count')
        oDataPoint_SORT["HAT_ID_ROWS"] = oDataPoint_SORT['BASIN'].map(
            {iX: iI for iI, iX in enumerate(oDataPoint_SORT['BASIN'].unique())}) + 1
        oDataPoint_SORT["HAT_ID_COLS"] = oDataPoint_SORT.groupby("BASIN").cumcount() + 1
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return update points workspace
        return oDataPoint_SORT
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to check class input
    def __checkInput(self):
        if self.__sFileName_SHP is not None:
            bFileName = True
        else:
            bFileName = False
        return bFileName
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
