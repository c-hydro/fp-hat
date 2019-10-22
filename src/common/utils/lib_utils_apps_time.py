"""
Library Features:

Name:          lib_utils_apps_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#################################################################################
# Library
import logging
import time
import datetime

from sys import version_info
from time import mktime
from numpy import abs

from fp.default.lib_default_args import sLoggerName
from fp.default.lib_default_args import sTimeFormat as sTimeFormat_Default

from fp.driver.configuration.drv_configuration_debug import Exc

# Log
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#################################################################################

# --------------------------------------------------------------------------------
# Dictionary of seconds for unit(s)
oSecondsUnits = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to check time reference
def checkTimeRef(sTime, oTimeMins=None, oTimeHours=None):
    oTime = datetime.datetime.strptime(sTime, sTimeFormat_Default)

    a1bTimeCheck = []
    if oTimeMins:
        oTimeCheck = [str(oTime.minute).zfill(2)]
        if oTimeCheck not in oTimeMins:
            a1bTimeCheck.append(False)
        else:
            a1bTimeCheck.append(True)

    if oTimeHours:
        oTimeCheck = [str(oTime.hour).zfill(2)]
        if oTimeCheck not in oTimeHours:
            a1bTimeCheck.append(False)
        else:
            a1bTimeCheck.append(True)

    if all(a1bTimeCheck) is True:
        bTimeCheck = True
    else:
        bTimeCheck = False

    return bTimeCheck
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to round time step to give delta of defined units (minutes, ...)
def roundTimeStep(sTime, sDeltaUnits='minutes', iDeltaValue=None):

    oTime = datetime.datetime.strptime(sTime, sTimeFormat_Default)
    if sDeltaUnits == 'minutes':
        oDeltaValue = datetime.timedelta(minutes=iDeltaValue)
    elif sDeltaUnits == 'hours':
        oDeltaValue = datetime.timedelta(minutes=iDeltaValue*60)
    else:
        oDeltaValue = None

    if iDeltaValue:
        if version_info >= (3, 0):
            oTime_Round = oTime + (datetime.datetime.min - oTime) % oDeltaValue
        elif version_info < (3, 0):

            if iDeltaValue < 0:
                sDeltaDirection = 'down'
            elif iDeltaValue > 0:
                sDeltaDirection = 'up'
            else:
                sDeltaDirection = None

            if sDeltaUnits == 'minutes':
                if sDeltaDirection:
                    oTime_Minute = (oTime.minute // abs(iDeltaValue) +
                                    (1 if sDeltaDirection == 'up' else 0)) * abs(iDeltaValue)
                    oTime_Round = oTime + datetime.timedelta(minutes=oTime_Minute - oTime.minute)
                else:
                    oTime_Round = oTime

            elif sDeltaUnits == 'hours':
                if sDeltaDirection:
                    oTime_Minute = (oTime.minute // abs(iDeltaValue * 60) +
                                    (1 if sDeltaDirection == 'up' else 0)) * abs(iDeltaValue * 60)
                    oTime_Round = oTime + datetime.timedelta(minutes=oTime_Minute - oTime.minute)
                else:
                    oTime_Round = oTime

    else:
        oTime_Round = None

    if oTime_Round:
        sTime_Round = oTime_Round.strftime(sTimeFormat_Default)
    else:
        sTime_Round = None

    return sTime_Round

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to find closest time (comparing with hours, minutes ...)
def findTimeClosest(sTime_Ref, oTime_HH=None):
    # Create datetime object
    oTime_Ref = datetime.datetime.strptime(sTime_Ref, sTimeFormat_Default)
    # Closest time using hours
    if oTime_HH is not None:
        a1oTime_Delta = []
        for sTime_HH_Step in oTime_HH:
            oTime_Step = oTime_Ref.replace(hour=int(sTime_HH_Step))
            oTime_Delta = oTime_Ref - oTime_Step
            if oTime_Delta > datetime.timedelta(seconds=1):
                a1oTime_Delta.append(oTime_Delta)

        oTime_Delta_Min = min(a1oTime_Delta)
        iTime_Delta_Index = a1oTime_Delta.index(oTime_Delta_Min)

        sTime_HH_Select = oTime_HH[iTime_Delta_Index]

        oTime_Select = oTime_Ref.replace(hour=int(sTime_HH_Select))
        sTime_Select = oTime_Select.strftime(sTimeFormat_Default)
        return sTime_Select
    else:
        Exc.getExc(' =====> WARNING: some arguments to find closest time are not defined! Check your data!', 2, 1)
        return sTime_Ref
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to check time format
def correctTimeLength(sTime):
    if len(sTime) == 12:

        sTimeUpd = sTime

    elif len(sTime) >= 8 and len(sTime) < 12:

        iTimeLength = len(sTime)

        iTimeLessDigits = 12 - iTimeLength
        sTimeLessFormat = '0' * iTimeLessDigits
        sTimeUpd = sTime + sTimeLessFormat

    elif len(sTime) > 12:
        Exc.getExc(' =====> ERROR: sTime has not allowed length (greater then 12 char). sTime cannot defined!', 1, 1)
    elif len(sTime) < 8:
        Exc.getExc(' =====> ERROR: sTime has not allowed length (less then 8 char). sTime cannot defined!', 1, 1)

    sTimeUpdFormat = defineTimeFormat(sTimeUpd)

    # Check time format definition
    checkTimeFormat(sTimeUpd, sTimeUpdFormat)

    return sTimeUpd, sTimeUpdFormat
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to check time format for time string
def checkTimeFormat(sTime, sTimeFormat=sTimeFormat_Default):
    try:
        datetime.datetime.strptime(sTime, sTimeFormat)
    except BaseException:
        Exc.getExc(' =====> ERROR: sTime has not correct format. sTime cannot defined!', 1, 1)
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define time format
def defineTimeFormat(sTime):
    sTimeFormat = ''
    if sTime.__len__() == 12:
        sTimeFormat = '%Y%m%d%H%M'
    elif sTime.__len__() == 10:
        sTimeFormat = '%Y%m%d%H'
    elif sTime.__len__() == 8:
        sTimeFormat = '%Y%m%d'
    elif sTime.__len__() == 19:
        sTimeFormat = '%Y-%m-%d %H:%M:%S'
    else:
        Exc.getExc(' =====> ERROR: sTime has not allowed length. sTimeFormat cannot defined!', 1, 1)

    # Check time format
    try:
        datetime.datetime.strptime(sTime, sTimeFormat)
    except BaseException:
        Exc.getExc(' =====> ERROR: sTimeFormat is not correctly selected. sTimeFormat cannot defined!', 1, 1)

    return sTimeFormat
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to convert time format
def convertTimeFormat(sTime_IN, sTimeFormat_IN=None, sTimeFormat_OUT=None):

    # Select automatically time format (is not defined by args)
    if sTimeFormat_IN is None:
        sTimeFormat_IN = defineTimeFormat(sTime_IN)

    # Create datetime obj to convert time format
    oTime_IN = datetime.datetime.strptime(sTime_IN, sTimeFormat_IN)

    # Convert time string using a different time format
    if sTimeFormat_OUT is not None:
        sTime_OUT = oTime_IN.strftime(sTimeFormat_OUT)
    else:
        sTime_OUT = sTime_IN

    return sTime_OUT

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to convert local time to GMT time and viceversa (sTimeLocal  --> 'yyyymmddHHMM')
def convertTimeLOCxGMT(sTime_IN=None, iTimeDiff=0):
    if sTime_IN:
        sTimeFormat_IN = defineTimeFormat(sTime_IN)
        sTimeFormat_OUT = sTimeFormat_IN

        oTime_IN = datetime.datetime.strptime(sTime_IN, sTimeFormat_IN)
        oTime_IN = oTime_IN.replace(minute=0, second=0, microsecond=0)
        oTime_OUT = oTime_IN + datetime.timedelta(seconds=iTimeDiff * 3600)
        sTime_OUT = oTime_OUT.strftime(sTimeFormat_OUT)
    else:
        Exc.getExc(" =====> ERROR: sTime_IN not defined! sTime_OUT cannot calculated!", 1, 1)

    return sTime_OUT
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get local time
def getTimeLocal(sTimeFormat=sTimeFormat_Default):
    return time.strftime(sTimeFormat, time.localtime())  # ---> LOCAL TIME
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get GMT time
def getTimeGMT(sTimeFormat=sTimeFormat_Default):
    return time.strftime(sTimeFormat, time.gmtime())  # ---> GMT TIME
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define sTimeNow
def getTimeNow(sTimeNow='', sTimeRefType='local'):

    if sTimeNow is None:
        sTimeNow = ''

    if not sTimeNow == '':
        [sTimeNow, sTimeFormat] = correctTimeLength(sTimeNow)
    elif sTimeNow == '':

        if sTimeRefType == 'local':
            sTimeNow = getTimeLocal()
        elif sTimeRefType == 'GMT':
            sTimeNow = getTimeGMT()
        else:
            Exc.getExc(
                ' =====> WARNING: sTimeTypeRef is not defined correctly! sTimeNow initialized as local time!', 2, 1)
            sTimeNow = getTimeLocal()

        [sTimeNow, sTimeFormat] = correctTimeLength(sTimeNow)

    else:
        sTimeFormat = None
        Exc.getExc(' =====> ERROR: sTimeNow format is unknown. Please check your time string!', 1, 1)

    return sTimeNow, sTimeFormat
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define sTimeStep
def getTimeStep(sTimeIN=None, iTimeDelta=3600, iTimeStep=0):
    if sTimeIN:
        sTimeFormat = defineTimeFormat(sTimeIN)
        oTimeIN = datetime.datetime.strptime(sTimeIN, sTimeFormat)
        oTimeOUT = oTimeIN + datetime.timedelta(seconds=iTimeStep * iTimeDelta)
        sTimeOUT = oTimeOUT.strftime(sTimeFormat)
    else:
        sTimeOUT = None
        sTimeFormat = None
        Exc.getExc(" =====> ERROR: sTimeIN not defined! sTimeOUT cannot calculated!", 1, 1)

    return sTimeOUT, sTimeFormat
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define sTimeTo
def getTimeTo(sTimeFrom=None, iTimeDelta=3600, iTimeStep=0):
    if sTimeFrom:
        sTimeFormat = defineTimeFormat(sTimeFrom)
        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFormat)
        oTimeTo = oTimeFrom + datetime.timedelta(seconds=iTimeStep * iTimeDelta)
        sTimeTo = oTimeTo.strftime(sTimeFormat)
    else:
        sTimeTo = None
        sTimeFormat = None
        Exc.getExc(" =====> ERROR: sTimeFrom not defined! sTimeTo cannot calculated!", 1, 1)

    return sTimeTo, sTimeFormat
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define sTimeFrom
def getTimeFrom(sTimeTo=None, iTimeDelta=3600, iTimeStep=0):
    if sTimeTo:
        sTimeFormat = defineTimeFormat(sTimeTo)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeFormat)
        oTimeFrom = oTimeTo - datetime.timedelta(seconds=iTimeStep * iTimeDelta)
        sTimeFrom = oTimeFrom.strftime(sTimeFormat)
    else:
        sTimeFrom = None
        sTimeFormat = None
        Exc.getExc(" =====> ERROR: sTimeTo not defined! sTimeFrom cannot calculated!", 1, 1)

    return sTimeFrom, sTimeFormat
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define a1oTimeSteps (using sTimeFrom, sTimeTo, iTimeDelta, iTimeStep)
def getTimeSteps(sTimeFrom=None, sTimeTo=None, iTimeDelta=3600, iTimeStep=0):
    # Case sTimeFrom and sTimeTo to define a1oTimeSteps
    if sTimeFrom and sTimeTo and iTimeDelta:

        sTimeFromFormat = defineTimeFormat(sTimeFrom)
        sTimeToFormat = defineTimeFormat(sTimeTo)

        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFromFormat)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeToFormat)

    elif sTimeFrom and iTimeDelta and iTimeStep:

        [sTimeTo, sTimeToFormat] = getTimeTo(sTimeFrom, iTimeDelta, iTimeStep)
        sTimeFromFormat = defineTimeFormat(sTimeFrom)

        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFromFormat)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeToFormat)

    elif sTimeTo and iTimeDelta and iTimeStep:

        [sTimeFrom, sTimeFromFormat] = getTimeFrom(sTimeTo, iTimeDelta, iTimeStep)
        sTimeToFormat = defineTimeFormat(sTimeTo)

        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFromFormat)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeToFormat)

    else:

        sTimeFromFormat = defineTimeFormat(sTimeFrom)
        sTimeToFormat = defineTimeFormat(sTimeTo)
        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFromFormat)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeToFormat)

    # Define a1oTimeSteps
    oTimeStep = oTimeFrom
    iTimeDelta = datetime.timedelta(seconds=iTimeDelta)

    if oTimeFrom != oTimeTo:

        a1oTimeSteps = []
        while oTimeStep <= oTimeTo:
            a1oTimeSteps.append(oTimeStep.strftime(sTimeToFormat))
            oTimeStep += iTimeDelta

    else:
        a1oTimeSteps = [oTimeFrom.strftime(sTimeFromFormat)]

    return a1oTimeSteps

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to check max time interval
def checkTimeMaxInt(a1oTime_Max=None, a1oTime_Test=None):

    if a1oTime_Test:
        if a1oTime_Max:

            sTime_From_Max = a1oTime_Max[0]
            sFormat_From_Max = defineTimeFormat(sTime_From_Max)
            oTime_From_Max = datetime.datetime.strptime(sTime_From_Max, sFormat_From_Max)
            sTime_To_Max = a1oTime_Max[-1]
            sFormat_To_Max = defineTimeFormat(sTime_To_Max)
            oTime_To_Max = datetime.datetime.strptime(sTime_To_Max, sFormat_To_Max)
            sTime_From_Test = a1oTime_Test[0]
            sFormat_From_Test = defineTimeFormat(sTime_From_Test)
            oTime_From_Test = datetime.datetime.strptime(sTime_From_Test, sFormat_From_Test)
            sTime_To_Test = a1oTime_Test[-1]
            sFormat_To_Test = defineTimeFormat(sTime_To_Test)
            oTime_To_Test = datetime.datetime.strptime(sTime_To_Test, sFormat_To_Test)

            if oTime_From_Max >= oTime_From_Test:
                oTime_From_Upd = oTime_From_Max
                sTime_From_Upd = oTime_From_Upd.strftime(sFormat_From_Max)
            else:
                oTime_From_Upd = oTime_From_Test
                sTime_From_Upd = oTime_From_Upd.strftime(sFormat_From_Test)

            if oTime_To_Max >= oTime_To_Test:
                oTime_To_Upd = oTime_To_Max
                sTime_To_Upd = oTime_To_Upd.strftime(sFormat_To_Max)
            else:
                oTime_To_Upd = oTime_To_Test
                sTime_To_Upd = oTime_To_Upd.strftime(sFormat_From_Test)

        else:
            sTime_From_Upd = a1oTime_Test[0]
            sTime_To_Upd = a1oTime_Test[-1]
    else:
        sTime_From_Upd = None
        sTime_To_Upd = None

    return sTime_From_Upd, sTime_To_Upd

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to find difference between time and a list of times
def findTimeDiff(sTimeCheck, sTimeTest):

    sTimeCheckFormat = defineTimeFormat(sTimeCheck)
    oTimeCheck = datetime.datetime.strptime(sTimeCheck, sTimeCheckFormat)

    sTimeTestFormat = defineTimeFormat(sTimeTest)
    oTimeTest = datetime.datetime.strptime(sTimeTest, sTimeTestFormat)

    # Calculating elapsed time
    try:
        # Python >=2.7
        dDV = (oTimeCheck - oTimeTest).total_seconds()

    except BaseException:
        # Python 2.6
        dDV_END = mktime(oTimeTest.timetuple())
        dDV_START = mktime(oTimeCheck.timetuple())
        dDV = dDV_END - dDV_START

    return abs(dDV)
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to compute time delta
def computeTimeDelta(sTimeFrom, sTimeTo, iTimeStep=1):
    iTimeElapsed = findTimeDiff(sTimeFrom, sTimeTo)
    iTimeDelta = iTimeElapsed/iTimeStep
    return iTimeDelta

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to convert time frequency to seconds
def convertTimeFrequency(sTimeFreq):
    sTimeFreq = sTimeFreq.lower()

    if sTimeFreq in oSecondsUnits.keys():
        iTimeFreq = oSecondsUnits[sTimeFreq]
    else:
        iTimeFreq = None
    return iTimeFreq

# --------------------------------------------------------------------------------
