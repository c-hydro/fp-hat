"""
Library Features:

Name:          lib_hmc_data_point
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190115'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import os
import tempfile
import shutil

import pandas as pd

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to get file point with 1d variable
def getVar1D(oFileName, oFileTime, oFileVarsSource=None, oFileVarsOutcome=None, oFileVarsDefault=None,
             oFileField='section', iFileCol=0, dFileNoData=-9999.0, dFileNaNData=-9998.0,
             sFolderTmp=None, sSuffixTmp='.txt'):

    if oFileVarsDefault is None:
        oFileVarsDefault = ['discharge']

    if oFileVarsSource is not None:
        oFileVarsSource_SELECTED = oFileVarsSource
    else:
        oFileVarsSource_SELECTED = oFileVarsDefault

    if oFileVarsOutcome is not None:
        oFileVarsOutcome_SELECTED = oFileVarsOutcome
    else:
        oFileVarsOutcome_SELECTED = oFileVarsDefault

    if isinstance(oFileName, str):
        oFileName = [oFileName]

    if isinstance(oFileField, str):
        oFileField = [oFileField]

    # Define list of list to consider ensemble result(s)
    if not all(isinstance(oElem, list) for oElem in oFileName):
        oFileName = [oFileName]

    a1oTS_DataFrame = None
    oFile_NAME_LIST = []
    for iFile_ID, (oFile_LIST, sFileVarsSource_SEL, sFileVarsOutcome_SEL) in enumerate(zip(
            oFileName, oFileVarsSource_SELECTED, oFileVarsOutcome_SELECTED)):

        a1oTS_TIME = []
        a2oTS_DATA = []
        for sFile_TIME, sFile_NAME in zip(oFileTime, oFile_LIST):
            if os.path.isfile(sFile_NAME):

                # Create temporary filename
                if sFolderTmp is not None:
                    oFile_NAME_TMP = tempfile.NamedTemporaryFile(dir=sFolderTmp, suffix=sSuffixTmp, delete=False)
                    sFile_NAME_TMP = oFile_NAME_TMP.name
                else:
                    oFile_NAME_TMP = tempfile.NamedTemporaryFile(suffix=sSuffixTmp, delete=False)
                    sFile_NAME_TMP = oFile_NAME_TMP.name

                # Copy file to temporary folder
                shutil.copy2(sFile_NAME, sFile_NAME_TMP)
                # Read point
                oFile_DATA = pd.read_table(sFile_NAME_TMP, header=None, lineterminator='\n', names=['data'])
                oFile_NAME_LIST.append(sFile_NAME_TMP)

                a1oFile_DATA = []
                for iI in range(0, oFile_DATA.shape[0]):
                    oRow_DATA = oFile_DATA['data'][iI]

                    if isinstance(oRow_DATA, str):
                        oRow_DATA = oRow_DATA.split()
                        if oRow_DATA.__len__() > 1:
                            dFile_DATA = float(oRow_DATA[iFileCol])
                        else:
                            try:
                                dFile_DATA = float(oRow_DATA[0])
                            except BaseException:
                                dFile_DATA = dFileNaNData
                                Exc.getExc(' =====> WARNING: undefined value in get 1D var! Check filename: ' +
                                           sFile_NAME + ' to control the retrieved value [' + str(oRow_DATA[0]) + ']!',
                                           2, 1)

                    else:
                        dFile_DATA = oRow_DATA

                    a1oFile_DATA.append(dFile_DATA)

                a2oTS_DATA.append(a1oFile_DATA)
                a1oTS_TIME.append(sFile_TIME)

            else:
                a1oFile_NULL = [dFileNoData] * oFileField.__len__()
                a2oTS_DATA.append(a1oFile_NULL)
                a1oTS_TIME.append(sFile_TIME)

        if a2oTS_DATA:
            iTS_N = a2oTS_DATA[0].__len__()
            iFIELD_N = oFileField.__len__()

            iTIME_N = a1oTS_TIME.__len__()

            if iFIELD_N != iTS_N:
                oFileField = ['point_{:}'] * iTS_N
                Exc.getExc(' =====> WARNING: declared name(s) for header are not equal to values in selected file!',
                           2, 1)

            oTS_Columns = [oFileField[iIdx].format(iIdx) for iIdx in range(0, iTS_N)]
            oTS_DataFrame = pd.DataFrame(a2oTS_DATA)
            oTS_DataFrame.columns = oTS_Columns

            # oTS_DataFrame['id'] = [iFile_ID + 1] * iTIME_N
            oTS_DataFrame['name'] = [sFileVarsOutcome_SEL] * iTIME_N
            oTS_DataFrame['time'] = pd.DatetimeIndex(pd.to_datetime(a1oTS_TIME))

            # oTS_DataFrame = oTS_DataFrame.set_index(['id', 'time'])
            oTS_DataFrame = oTS_DataFrame.set_index(['name', 'time'])

            if a1oTS_DataFrame is None:
                a1oTS_DataFrame = oTS_DataFrame.copy()
            else:
                a1oTS_DataFrame = pd.concat([a1oTS_DataFrame, oTS_DataFrame], axis=0)

        else:
            a1oTS_DataFrame = None

    return a1oTS_DataFrame, oFile_NAME_LIST

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Convert pandas dataframe to xarray dataset
def convertVarDFrame(oDataFrame):

    oDataset = oDataFrame.to_xarray()
    oDataset.coords['time'] = oDataset.coords['time'].astype('datetime64[ns]')

    return oDataset
# -------------------------------------------------------------------------------------


