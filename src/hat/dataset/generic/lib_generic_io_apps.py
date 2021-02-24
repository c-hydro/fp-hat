"""
Library Features:

Name:          lib_generic_io_apps
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190213'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os
import shutil
import mimetypes
import tempfile
import gzip
import re
import fnmatch

from itertools import repeat
from copy import deepcopy

from src.hat.dataset.generic.lib_generic_io_method import readFileNC4

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to find tag(s) using a generic pattern
def findVarTag(oVarList_FILTERED, sVarPattern='rain_$ensemble', oVarTags=None):

    if oVarTags is None:
        oVarTags = ['$period', '$ensemble']

    iVarTags_N = oVarTags.__len__()
    iVarPattern_N = sVarPattern.count('$')

    if iVarPattern_N > iVarTags_N:
        Exc.getExc(' =====> WARNING: in finding tag(s) value(s) the length of patterns with $'
                   ' are greater then the length of tags definition!', 2, 1)

    oVarID = []
    oVarTags_FILTERED = deepcopy(oVarTags)
    sVarEnsemble = deepcopy(sVarPattern)
    for sVarTag in oVarTags:
        if sVarTag in sVarEnsemble:
            oVarID.append(sVarEnsemble.index(sVarTag))
        else:
            oVarTags_FILTERED.remove(sVarTag)
    if oVarID:
        a1oVarTags_SORTED = sorted(zip(oVarID, oVarTags_FILTERED))
    else:
        a1oVarTags_SORTED = None

    if a1oVarTags_SORTED is not None:
        oTagsName_FILTERED = []
        for iVarID_SORTED, oVarTags_SORTED in enumerate(a1oVarTags_SORTED):
            if '$ensemble' in oVarTags_SORTED:
                iVarID_ENSEMBLE = iVarID_SORTED
            oTagsName_FILTERED.append(oVarTags_SORTED[1])
    else:
        oTagsName_FILTERED = None

    oTagsValue_FILTERED = []
    for sVarList_FILTERED in oVarList_FILTERED:
        oTagValue_FILTERED = re.findall(r'\d+', sVarList_FILTERED)
        if oTagValue_FILTERED:
            oTagsValue_FILTERED.append(oTagValue_FILTERED)

    if not oTagsValue_FILTERED:
        oTagsValue_FILTERED = None

    if oTagsName_FILTERED is not None:
        oTagsName_FILTERED = list(repeat(oTagsName_FILTERED, oTagsValue_FILTERED.__len__()))

    return oTagsName_FILTERED, oTagsValue_FILTERED
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create variable name using a generic pattern
def createVarName(sVarPattern, oTagsName=None, oTagsValue=None, bVarSort=True):

    if oTagsName is None:
        oTagsName = ['$ensemble']

    if oTagsValue is not None:
        a1oVarPattern_FILLED = []
        for oTagsName_STEP, oTagsValue_STEP in zip(oTagsName, oTagsValue):
            sVarPattern_FILLED = deepcopy(sVarPattern)
            for sTagsName_STEP, sTagsValue_STEP in zip(oTagsName_STEP, oTagsValue_STEP):
                sVarPattern_FILLED = sVarPattern_FILLED.replace(sTagsName_STEP, sTagsValue_STEP)
            a1oVarPattern_FILLED.append(sVarPattern_FILLED)
    else:
        a1oVarPattern_FILLED = [sVarPattern]

    if bVarSort:
        a1oVarPattern_FILLED.sort()

    return a1oVarPattern_FILLED
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to find variable name using a generic pattern
def findVarName(oVarList, sVarPattern='rain_$ensemble', oVarTags=None):

    if oVarTags is None:
        oVarTags = ['$period', '$ensemble']

    iVarTags_N = oVarTags.__len__()
    iVarPattern_N = sVarPattern.count('$')

    if iVarPattern_N > iVarTags_N:
        Exc.getExc(' =====> WARNING: in finding variable name(s) the length of patterns with $'
                   ' are greater then the length of tags definition!', 2, 1)

    sVarDefined = deepcopy(sVarPattern)
    for sVarTag in oVarTags:
        sVarDefined = sVarDefined.replace(sVarTag, '*')

    oVarList_FILTERED = fnmatch.filter(oVarList, sVarDefined)

    if isinstance(oVarList_FILTERED, str):
        oVarList_FILTERED = [oVarList_FILTERED]

    if oVarList_FILTERED.__len__() == 0:
        #Exc.getExc(' =====> ERROR: mismatch between group variable(s) and variable pattern! Check your settings!', 1, 1)
        oVarList_FILTERED = None

        Exc.getExc(' =====> WARNING: in finding variable name(s), method returns NONE for variable ' +
                   sVarPattern + ' !', 2, 1)

    return oVarList_FILTERED
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create ensemble variable(s)
def createVarEnsemble(oEnsembleName, sVarPattern='rain_$ensemble', sEnsemblePattern='$ensemble'):
    sVarBase, sVarRest = sVarPattern.split(sEnsemblePattern)
    oVarName_CREATE = []
    for sEnsembleName in oEnsembleName:
        sVarName_CREATE = sVarBase + sEnsembleName + sVarRest
        oVarName_CREATE.append(sVarName_CREATE.strip())
    return oVarName_CREATE
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get ensemble variable(s)
def getVarEnsemble(oVarName, sVarPattern="rain_$ensemble", sEnsemblePattern='$ensemble'):

    sVarBase, sVarRest = sVarPattern.split(sEnsemblePattern)
    oVarName_FIND = [sVar for sVar in oVarName if sVarBase in sVar]

    oEnsembleName_FIND = []
    for sVarFile_FIND in oVarName_FIND:
        sEnsembleName_FIND = re.findall(r'\d+', sVarFile_FIND)[0]
        oEnsembleName_FIND.append(sEnsembleName_FIND)

    return oVarName_FIND, oEnsembleName_FIND
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to wrap file reader (to manage zip or unzipped file)
def wrapFileReader(sVarFileName_IN, sVarFileGroup=None):

    if os.path.isfile(sVarFileName_IN):
        if mimetypes.guess_type(sVarFileName_IN)[1] == 'gzip':

            oVarFileName_UNZIP = gzip.open(sVarFileName_IN, 'rb')
            oVarFileName_TMP = tempfile.NamedTemporaryFile(delete=False)
            shutil.copyfileobj(oVarFileName_UNZIP, oVarFileName_TMP)
            oVarFileName_UNZIP.close()
            oVarFileName_TMP.close()
            sVarFileName_OUT = oVarFileName_TMP.name

        elif mimetypes.guess_type(sVarFileName_IN)[1] is None:

            sVarFileName_TMP = os.path.basename(sVarFileName_IN)
            sVarFolderName_TMP = tempfile.gettempdir()
            sVarFileName_TMP = os.path.join(sVarFolderName_TMP, sVarFileName_TMP)
            shutil.copy2(sVarFileName_IN, sVarFileName_TMP)
            sVarFileName_OUT = sVarFileName_TMP

        if os.path.isfile(sVarFileName_OUT):
            oVarFileData_OUT = readFileNC4(sVarFileName_OUT, oVarGroup=sVarFileGroup)
            oVarDSet_OUT = oVarFileData_OUT[sVarFileGroup]
        else:
            oVarDSet_OUT = None

        if os.path.exists(sVarFileName_OUT):
            os.remove(sVarFileName_OUT)
    else:
        oVarDSet_OUT = None

    return oVarDSet_OUT
# -------------------------------------------------------------------------------------
