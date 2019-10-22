"""
Class Features

Name:          drv_data_io_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190219'
Version:       '2.1.0'
"""

######################################################################################
# Library
import logging
import numpy as np
from os.path import isfile, join
from copy import deepcopy

from src.common.time.lib_time import computeTimeCorrivation
from src.common.utils.lib_utils_op_dict import removeDictKey
from src.common.utils.lib_utils_apps_geo import defineGeoGrid, defineGeoCorner, readGeoHeader, correctGeoHeader
from src.common.utils.lib_utils_op_system import createFolderByFile

from src.common.driver.dataset.drv_data_io_type import Drv_Data_IO

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

from src.hat.dataset.generic.lib_generic_io_utils import createVar2D, mergeVar2D
from src.hat.dataset.generic.lib_generic_io_method import writeFileNC4

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
######################################################################################

# -------------------------------------------------------------------------------------
# Define valid values
oVarData_Valid = ['Terrain', 'Channel_Network']
# Define geographical variable(s)
oGeoData_Valid = dict(a2dGeoData=None, a2dGeoX=None, a2dGeoY=None, a1dGeoBox=None,
                      a1oGeoHeader=None, a1iGeoIndexNaN=None, a1iGeoIndexFinite=None,
                      iRows=None, iCols=None, dGeoXMin=None, dGeoXMax=None, dGeoYMin=None, dGeoYMax=None,
                      dNoData=None, dGeoXStep=None, dGeoYStep=None, a2bGeoDataFinite=None, a2bGeoDataNaN=None,
                      iGeoTc=None, a2dGeoCNET=None)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class Data object
class DataObj(object):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class DataGeo
class DataGeo:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, **kwargs):

        # Define class object
        self.oVarData = self.__checkVar(kwargs['vars'])
        self.oFileData = [kwargs['file_terrain'], kwargs['file_channel_network']]
        self.sFileAncillary = kwargs['file_ancillary']

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get geographical Data
    def getDataGeo(self):

        # -------------------------------------------------------------------------------------
        # Info start
        oLogStream.info(' ---> Get geographical data ... ')

        # Define dictionary of geographical file(s)
        oVarData = self.oVarData
        oFileData = self.oFileData
        sFileAncillary = self.sFileAncillary

        # Method to check class input
        oFileExpected = self.__checkFile(oVarData, oFileData)

        # Method to read filename(s) and collect geographical data
        oGeoData = self.__readGrid(oVarData, oFileData, oFileExpected)
        # Method to dump data in a netcdf file
        self.__saveGeoInfo(sFileAncillary, oGeoData)

        # Method to select output Data
        oData = self.__selectInfo(oGeoData)

        # Info end
        oLogStream.info(' ---> Get geographical data ... OK')

        # Return variable(s)
        return oData
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to create geographical ancillary file
    @staticmethod
    def __saveGeoInfo(sFileAncillary, oGeoData):

        # -------------------------------------------------------------------------------------
        # Define attribute(s)
        oGeoAttrs = removeDictKey(deepcopy(oGeoData),
                                  ['a2dGeoData', 'a2dGeoX', 'a2dGeoY',
                                   'a1dGeoBox', 'a1oGeoHeader', 'a1iGeoIndexNaN', 'a1iGeoIndexFinite',
                                   'a2bGeoDataFinite', 'a2bGeoDataNaN', 'a2dGeoCNET'])
        # Define encoding
        oGeoEncoding = {'Terrain': {'_FillValue': -9999.0},
                        'Channel_Network': {'_FillValue': -9999.0}}
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Create data array for terrain
        oVarTerrain = createVar2D(oGeoData['a2dGeoData'], oGeoData['a2dGeoX'], oGeoData['a2dGeoY'],
                                  sVarName='Terrain', oVarAttributes=oGeoAttrs)
        # Create data array for channel network
        oVarCNET = createVar2D(oGeoData['a2dGeoCNET'], oGeoData['a2dGeoX'], oGeoData['a2dGeoY'],
                               sVarName='Channel_Network', oVarAttributes=oGeoAttrs)

        # Merge data arrays in a common dataset
        oVarDSet = mergeVar2D([oVarTerrain, oVarCNET])
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Save data in a netcdf file
        if not isfile(sFileAncillary):
            createFolderByFile(sFileAncillary)
            sVarMode = 'w'
        else:
            sVarMode = 'a'
        # Dump data to netcdf file
        writeFileNC4(sFileAncillary, oVarDSet, oVarAttr=oGeoEncoding, sVarGroup=None,
                     sVarMode=sVarMode, oVarEngine='h5netcdf', iVarCompression=9)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------
    # Method to select output Data
    @staticmethod
    def __selectInfo(oGeoData):
        oData = DataObj()
        for sVarName, oVarData in oGeoData.items():
            setattr(oData, sVarName, oVarData)
        return oData
    # -----------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Getting geographical information using an ascii grid file
    @staticmethod
    def __readGrid(oVarData, oFileData, oFileExpected):

        # -------------------------------------------------------------------------------------
        # Check data availability
        iRows = 0
        iCols = 0
        a2dGeoCNET = None
        if oVarData:

            # -------------------------------------------------------------------------------------
            # Iterate over variable(s)
            for sVarData, sFileData, bFileExpected in zip(oVarData, oFileData, oFileExpected):

                # -------------------------------------------------------------------------------------
                # Read ascii grid file
                if sVarData == 'Terrain':

                    # -------------------------------------------------------------------------------------
                    # Read terrain data
                    if bFileExpected is True:

                        # -------------------------------------------------------------------------------------
                        # Open ascii grid data
                        oFileDriver = Drv_Data_IO(sFileData, 'r').oFileWorkspace
                        oFileData = oFileDriver.oFileLibrary.openFile(join(oFileDriver.sFilePath, oFileDriver.sFileName),
                                                                      oFileDriver.sFileMode)
                        # Read ascii grid data
                        [a2dGeoData, a1oGeoHeader] = oFileDriver.oFileLibrary.readArcGrid(oFileData)
                        oFileDriver.oFileLibrary.closeFile(oFileData)

                        # Get information Data header
                        [iRows, iCols, dGeoXMin, dGeoYMin, dGeoXStep, dGeoYStep, dNoData] = readGeoHeader(a1oGeoHeader)

                        # Define Data, finite and nan value(s)
                        a2dGeoData = np.asarray(a2dGeoData, dtype=np.float32)
                        a2bGeoDataFinite = (a2dGeoData != dNoData)
                        a2bGeoDataNaN = (a2dGeoData == dNoData)
                        a1iGeoIndexNaN = np.where(a2bGeoDataFinite.ravel() == False)[0]
                        a1iGeoIndexFinite = np.where(a2bGeoDataFinite.ravel() == True)[0]

                        # Define Data using nan value(s)
                        a2dGeoData[a2bGeoDataNaN] = np.nan

                        # Define geographical corners
                        [dGeoXMin, dGeoXMax, dGeoYMin, dGeoYMax] = defineGeoCorner(dGeoXMin, dGeoYMin,
                                                                                   dGeoXStep, dGeoYStep, iCols, iRows)
                        # Define geographical grid
                        [a2dGeoX, a2dGeoY, a1dGeoBox] = defineGeoGrid(dGeoYMin, dGeoXMin, dGeoYMax, dGeoXMax,
                                                                      dGeoYStep, dGeoXStep)
                        # Correct GeoHeader key(s) --> lower characters
                        a1oGeoHeader = correctGeoHeader(a1oGeoHeader)

                        # Compute corrivation time (based on terrain data)
                        iGeoTc = computeTimeCorrivation(a2dGeoData, a2dGeoY, dGeoXStep, dGeoYStep)

                        # Flip variable(s) to manage orientation
                        a2dGeoData = np.flipud(a2dGeoData)
                        a2dGeoY = np.flipud(a2dGeoY)
                        a2bGeoDataFinite = np.flipud(a2bGeoDataFinite)
                        a2bGeoDataNaN = np.flipud(a2bGeoDataNaN)
                        # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Exit error for file not found
                        Exc.getExc(' =====> ERROR: terrain filename ' +
                                   sFileData + ' is not available. Check your settings!', 1, 1)
                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------

                elif sVarData == 'Channel_Network':

                    # -------------------------------------------------------------------------------------
                    # Read channel network  data
                    if bFileExpected is True:

                        # -------------------------------------------------------------------------------------
                        # Open ascii grid data
                        oFileDriver = Drv_Data_IO(sFileData, 'r').oFileWorkspace
                        oFileData = oFileDriver.oFileLibrary.openFile(join(oFileDriver.sFilePath, oFileDriver.sFileName),
                                                                      oFileDriver.sFileMode)
                        # Read ascii grid data
                        [a2dGeoCNET, a1oGeoHeader] = oFileDriver.oFileLibrary.readArcGrid(oFileData)
                        oFileDriver.oFileLibrary.closeFile(oFileData)
                        # Flip variable(s) to manage orientation
                        a2dGeoCNET = np.flipud(a2dGeoCNET)
                        # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Exit warning for file not found
                        a2dGeoCNET = None
                        Exc.getExc(' =====> WARNING: channel network filename ' +
                                   sFileData + ' is not available. Check your settings!', 2, 1)
                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
        else:
            # -------------------------------------------------------------------------------------
            # Exit for no data valid
            Exc.getExc(' =====> ERROR: all geographical data are null. Check your settings!', 1, 1)
            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Initialize variable for null dataset
        if a2dGeoCNET is None:
            a2dGeoCNET = np.zeros([iRows, iCols])
            a2dGeoCNET[:, :] = -9999.0

        # Store data in a common declared dictionary
        oGeoData = deepcopy(oGeoData_Valid)
        for sGeoVar in list(oGeoData.keys()):
            oGeoData[sGeoVar] = locals()[sGeoVar]

        # Return data
        return oGeoData
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to check variable name
    @staticmethod
    def __checkVar(oVarData_DEF):
        oVarData_CHECK = []
        for sVarData_DEF in oVarData_DEF:
            if sVarData_DEF in oVarData_Valid:
                oVarData_CHECK.append(sVarData_DEF)
            else:
                Exc.getExc(' =====> WARNING: geographical variable ' +
                           sVarData_DEF + ' is not a valid value. Check your settings!', 2, 1)
        return oVarData_CHECK
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to check class input
    @staticmethod
    def __checkFile(oVarData, oFileData):
        a1bFileData = []
        for sVarData, sFileData in zip(oVarData, oFileData):
            if isfile(sFileData):
                bFileData = True
            else:
                bFileData = False
                Exc.getExc(' =====> WARNING: geographical filename ' +
                           sFileData + ' is not available for defining variable ' +
                           sVarData + '. Check your settings!', 2, 1)
            a1bFileData.append(bFileData)
        return a1bFileData
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
