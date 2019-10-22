"""
Class Features

Name:          drv_configuration_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190124'
Version:       '2.5.0'
"""

#######################################################################################
# Library
import logging
import time
import pandas as pd

from src.common.default.lib_default_args import sTimeFormat, sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Log
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
class DataObject(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class Time
class DataTime:

    # -------------------------------------------------------------------------------------
    # Global Variable(s)
    oTimeNow = None
    oTimeArg = None
    oTimeRun = None
    oTimeFrom = None
    oTimeTo = None
    oTimeSteps = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, sTimeArg=time.strftime(sTimeFormat, time.gmtime()),
                 sTimeNow=None,
                 iTimePeriodPast=0, iTimePeriodFuture=0, sTimeFrequency='H', sTimeETA='H'):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.sTimeArg = sTimeArg
        self.sTimeNow = sTimeNow
        self.iTimePeriodPast = int(iTimePeriodPast)
        self.iTimePeriodFuture = int(iTimePeriodFuture)
        self.sTimeFrequency = sTimeFrequency
        self.sTimeETA = sTimeETA
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set times
    def getDataTime(self, bTimeReverse=False, bTimeRestart=True):

        # -------------------------------------------------------------------------------------
        # Info start
        oLogStream.info(' ---> Configure time ... ')

        # Get time now
        self.oTimeNow = self.__getTimeNow()
        # Get time argument
        self.oTimeArg = self.__getTimeArg()
        # Set time run
        self.oTimeRun = self.__setTimeRun(self.oTimeNow, self.oTimeArg)

        # Get initial time step (taking care restart time condition)
        self.oTimeFrom = self.__getTimeFrom(self.oTimeRun,
                                            iTimePeriod=self.iTimePeriodPast, sTimeFrequency=self.sTimeFrequency,
                                            bTimeRestart=bTimeRestart)
        # Get ending time step
        self.oTimeTo = self.__getTimeTo(self.oTimeRun, iTimePeriod=self.iTimePeriodFuture,
                                        sTimeFrequency=self.sTimeFrequency)

        # Compute period time steps
        self.oTimeSteps = self.__computeTimePeriod(self.oTimeFrom, self.oTimeTo,
                                                   sTimeETA=self.sTimeETA, bTimeReverse=bTimeReverse)

        # Info end
        oLogStream.info(' ---> Configure time ... OK')

        return DataObject(self.__dict__)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get time now
    def __getTimeNow(self):

        oLogStream.info(' ----> Configure time now  ... ')
        oTimeNow = None
        try:
            if self.sTimeNow is None:
                oLogStream.info(' -----> Time now is not set. Time will be taken using time library.')
                self.sTimeNow = time.strftime(sTimeFormat, time.gmtime())
            else:
                oLogStream.info(' -----> Time argument is set using script configuration file')

            oTimeNow = pd.to_datetime(self.sTimeNow, format=sTimeFormat)
            oTimeNow = oTimeNow.floor('min')
            oTimeNow = oTimeNow.replace(minute=0)

            self.sTimeNow = oTimeNow.strftime(sTimeFormat)

            oLogStream.info(' ----> Configure time now ... DONE [' + self.sTimeNow + ']')

        except BaseException:
            Exc.getExc(' =====> ERROR: time now definition failed! Check your data and settings!', 1, 1)

        return oTimeNow
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get time set in argument(s)
    def __getTimeArg(self):

        oLogStream.info(' ----> Configure time argument  ... ')
        oTimeArg = None
        try:
            if self.sTimeArg is None:
                oLogStream.info(' -----> Time argument is not set. Time will be taken using time library.')
                self.sTimeArg = time.strftime(sTimeFormat, time.gmtime())
            else:
                oLogStream.info(' -----> Time argument is set using script arg(s)')

            oTimeArg = pd.to_datetime(self.sTimeArg, format=sTimeFormat)
            oTimeArg = oTimeArg.floor('min')
            oTimeArg = oTimeArg.replace(minute=0)

            self.sTimeArg = oTimeArg.strftime(sTimeFormat)

            oLogStream.info(' ----> Configure time argument ... DONE [' + self.sTimeArg + ']')

        except BaseException:
            Exc.getExc(' =====> ERROR: time argument definition failed! Check your data and settings!', 1, 1)

        return oTimeArg

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set time run
    def __setTimeRun(self, oTimeNow, oTimeArg):

        oLogStream.info(' ----> Set time run  ... ')
        if oTimeArg is not None:
            oLogStream.info(' -----> Time argument is used as time run [' + self.sTimeArg + ']')
            oLogStream.info(' ----> Set time run  ... DONE')
            return oTimeArg
        else:
            oLogStream.info(' -----> Time now is used as time run [' + self.sTimeNow + ']')
            oLogStream.info(' ----> Set time run  ... DONE')
            return oTimeNow

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define time restart
    @staticmethod
    def __getTimeFrom(oTimeRun, iTimePeriod=0, sTimeFrequency='H', bTimeRestart=False):

        oTimeFrom = oTimeRun - pd.to_timedelta(iTimePeriod, unit=sTimeFrequency)

        if bTimeRestart is True:
            oTimeFrom = oTimeFrom.floor('D')

        # Pass to global variable(s)
        return oTimeFrom

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get time to
    @staticmethod
    def __getTimeTo(oTimeRun, iTimePeriod=0, sTimeFrequency='H'):

        oTimeTo = oTimeRun + pd.to_timedelta(iTimePeriod, unit=sTimeFrequency)
        return oTimeTo

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute period time steps
    @staticmethod
    def __computeTimePeriod(oTimeFrom, oTimeTo, sTimeETA, bTimeReverse=False):

        oTimeRange = pd.date_range(oTimeFrom, oTimeTo, freq=sTimeETA)
        oTimeRange = oTimeRange.floor(sTimeETA)

        if bTimeReverse:
            oTimeRange = oTimeRange.sort_values(return_indexer=False, ascending=False)

        return oTimeRange

# -------------------------------------------------------------------------------------
