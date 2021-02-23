"""
Hydrological Analysis Tool - DataManager for Hydrological Model Continuum - Near Real Time

__date__ = '20210218'
__version__ = '1.2.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org)'
__library__ = 'hat'

General command line:
python3 HAT_DataManager_HMC_NRT.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"
Version(s) in changelog file
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import time
import argparse

# Partial library
from os.path import exists

from src.common.log.lib_logging import setLoggingFile
from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import removeDictKey
from src.common.utils.lib_utils_file_workspace import savePickle, restorePickle
from src.common.driver.configuration.drv_configuration_debug import Exc

from src.hat.driver.dataset.generic.drv_data_io_point import DataPoint
from src.hat.driver.dataset.generic.drv_data_io_geo import DataGeo
from src.hat.driver.configuration.drv_configuration_algorithm import DataAlgorithm
from src.hat.driver.configuration.drv_configuration_time import DataTime
from src.hat.driver.configuration.drv_configuration_tags import DataTags

from src.hat.driver.analysis.hmc.nrt.drv_datamanager_hmc_nrt import DataAnalysisCleaner, DataAnalysisTime, \
    DataAnalysisBuilder, DataAnalysisManagerTimeSeries, DataAnalysisManagerGridded, DataAnalysisFinalizer
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Version and algorithm information
    sProgramVersion = '1.2.0'
    sProjectName = 'HAT'
    sAlgType = 'DataManager'
    sAlgName = 'HMC NearRealTime'
    # Time algorithm information
    dStartTime = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get script argument(s)
    [sScriptName, sFileSetting, sTimeArg] = GetArgs()

    # Set algorithm configuration
    oDrv_Data_Settings = DataAlgorithm(sFileSetting)
    [oData_Settings, oData_Path, oData_Flags, oData_Mapping, oData_ColorMap] = oDrv_Data_Settings.getDataSettings()

    # Set logging file
    oLogStream = setLoggingFile(oData_Path['log'], bLoggerHistory=oData_Settings['data']['log']['history'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Start Program
    oLogStream.info('[' + sProjectName + ' ' + sAlgType + ' - ' + sAlgName + ' (Version ' + sProgramVersion + ')]')
    oLogStream.info('[' + sProjectName + '] Start Program ... ')

    # Clean static ancillary file(s) and folder(s)
    DataAnalysisCleaner(
        flag=[oData_Flags['cleaning_static_data']],
        file=[oData_Path['section_ancillary'],
              oData_Path['land_ancillary']
              ]
    ).cleanDataAnalysis()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get algorithm time
    oLogStream.info(' --> Set algorithm time ... ')
    oDrv_Time = DataTime(sTimeArg,
                         sTimeNow=oData_Settings['time']['time_now'],
                         iTimePeriodPast=oData_Settings['time']['time_period'],
                         sTimeFrequency=oData_Settings['time']['time_frequency'],
                         sTimeETA=oData_Settings['time']['time_eta'])
    oData_TimeRun = oDrv_Time.getDataTime(bTimeReverse=True, bTimeRestart=False)
    oLogStream.info(' --> Set algorithm time ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get geographical data
    oLogStream.info(' --> Set geographical data ... ')
    oDrv_Data_Geo = DataGeo(file_terrain=oData_Path['land_terrain'],
                            file_channel_network=oData_Path['land_channel_network'],
                            file_ancillary=oData_Path['land_ancillary'],
                            vars=['Terrain', 'Channel_Network']
                            )
    oData_Geo = oDrv_Data_Geo.getDataGeo()
    oLogStream.info(' --> Set geographical data ... DONE')

    # Get sections data
    oLogStream.info(' --> Set section data ... ')
    oDrv_Data_Section = DataPoint(file_shp=oData_Path['section_ref'],
                                  file_mask=oData_Path['section_mask'],
                                  file_terrain=oData_Path['section_dem'],
                                  file_ctime=oData_Path['section_ctime'],
                                  file_ancillary=oData_Path['section_ancillary'],
                                  fields=None,
                                  )
    oData_Section = oDrv_Data_Section.getDataPoint(oData_Geo)
    oLogStream.info(' --> Set section data ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time steps
    for oTimeRun_STEP in oData_TimeRun['oTimeSteps']:

        # -------------------------------------------------------------------------------------
        # Get data time
        oLogStream.info(' --> Get dynamic time ... ')
        oDrv_DataTime_Dynamic = DataAnalysisTime(
            time=oTimeRun_STEP,
            settings=oData_Settings)
        oData_TimePeriod = oDrv_DataTime_Dynamic.computeDataTime(oData_Geo)
        oLogStream.info(' --> Get dynamic time ... DONE')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Set data tags /$yyyy/$mm/$dd/
        oDrv_Data_Tags = DataTags(
            {'$yyyy': str(oTimeRun_STEP.year).zfill(4),
             '$mm': str(oTimeRun_STEP.month).zfill(2),
             '$dd': str(oTimeRun_STEP.day).zfill(2),
             '$HH': str(oTimeRun_STEP.hour).zfill(2),
             '$MM': str(oTimeRun_STEP.minute).zfill(2),
             '$RUNTIME': str(oTimeRun_STEP.year).zfill(4) + '/' +
                         str(oTimeRun_STEP.month).zfill(2) + '/' +
                         str(oTimeRun_STEP.day).zfill(2) + '/' + str(oTimeRun_STEP.hour).zfill(2),
             '$RUNDOMAIN': oData_Settings['algorithm']['ancillary']['run_domain'],
             '$RUNNAME': oData_Settings['algorithm']['ancillary']['run_name']})
        oData_Tags = oDrv_Data_Tags.setDataTags()
        # Info time
        oLogStream.info(' --> Set time step: ' + str(oTimeRun_STEP))

        # Clean buffer and product file(s) and folder(s)
        DataAnalysisCleaner(
            flag=[oData_Flags['cleaning_dynamic_data_source'],
                  oData_Flags['cleaning_dynamic_data_outcome_ts'],
                  oData_Flags['cleaning_dynamic_data_outcome_gridded'],
                  oData_Flags['cleaning_dynamic_data_product_ts'],
                  oData_Flags['cleaning_dynamic_data_product_gridded'],
                  ],
            file=[[defineString(oData_Path['file_buffer_source_info'], oData_Tags),
                   defineString(oData_Path['file_buffer_source_data'], oData_Tags)],
                  defineString(oData_Path['file_buffer_outcome_ts'], oData_Tags),
                  defineString(oData_Path['file_buffer_outcome_gridded'], oData_Tags),
                  defineString(oData_Path['file_product_ts'], oData_Tags),
                  defineString(oData_Path['file_product_gridded'], oData_Tags),
                  ]
        ).cleanDataAnalysis()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get data analysis
        oLogStream.info(' --> Get analysis data ... ')
        oDrv_DataBuilder_Dynamic = DataAnalysisBuilder(
            time_run=oTimeRun_STEP,
            time_period=oData_TimePeriod,
            settings=oData_Settings,
            file=oData_Path,
            mapping=oData_Mapping,
            tags=removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute']),
        )

        if not exists(defineString(oData_Path['file_buffer_source_info'], oData_Tags)):
            oData_Dynamic_Source = oDrv_DataBuilder_Dynamic.getDataAnalysis(oData_Geo, oData_Section)
            savePickle(defineString(oData_Path['file_buffer_source_info'], oData_Tags),
                       oData_Dynamic_Source)
            oLogStream.info(' --> Get dynamic data ... DONE')
        else:
            oData_Dynamic_Source = restorePickle(defineString(oData_Path['file_buffer_source_info'], oData_Tags))
            oLogStream.info(' --> Get dynamic data ... LOADED from buffer workspace saved file.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Compute time series data analysis
        oLogStream.info(' --> Compute dynamic time-series data... ')
        oDrv_DataManager_Dynamic_TS = DataAnalysisManagerTimeSeries(
            time_run=oTimeRun_STEP,
            time_period=oData_TimePeriod,
            settings=oData_Settings,
            file=oData_Path,
            mapping=oData_Mapping,
            tags=removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute']),
        )

        if not exists(defineString(oData_Path['file_buffer_outcome_ts'], oData_Tags)):
            oData_Dynamic_Outcome_TS = oDrv_DataManager_Dynamic_TS.computeDataAnalysis(
                oData_Dynamic_Source, oData_Section)
            savePickle(defineString(oData_Path['file_buffer_outcome_ts'], oData_Tags),
                       oData_Dynamic_Outcome_TS)
            oLogStream.info(' --> Compute dynamic time-series data ... DONE')
        else:
            oData_Dynamic_Outcome_TS = restorePickle(defineString(
                oData_Path['file_buffer_outcome_ts'], oData_Tags))
            oLogStream.info(' --> Compute dynamic time-series data ... LOADED from buffer workspace saved file.')

        # Compute gridded data analysis
        oLogStream.info(' --> Compute dynamic gridded data ... ')
        oDrv_DataManager_Dynamic_Gridded = DataAnalysisManagerGridded(
            time_run=oTimeRun_STEP,
            time_period=oData_TimePeriod,
            settings=oData_Settings,
            file=oData_Path,
            mapping=oData_Mapping,
            tags=removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute']),
        )

        if not exists(defineString(oData_Path['file_buffer_outcome_gridded'], oData_Tags)):
            oData_Dynamic_Outcome_Gridded = oDrv_DataManager_Dynamic_Gridded.computeDataAnalysis(
                oData_Dynamic_Source, oData_Geo)
            savePickle(defineString(oData_Path['file_buffer_outcome_gridded'], oData_Tags),
                       oData_Dynamic_Outcome_Gridded)
            oLogStream.info(' --> Compute dynamic gridded data ... DONE')
        else:
            oData_Dynamic_Outcome_Gridded = restorePickle(defineString(
                oData_Path['file_buffer_outcome_gridded'], oData_Tags))
            oLogStream.info(' --> Compute dynamic gridded data ... LOADED from buffer workspace saved file.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Save data dynamic
        oLogStream.info(' --> Save dynamic data ... ')
        oDrv_DataFinalizer_Dynamic = DataAnalysisFinalizer(
            time_run=oTimeRun_STEP,
            time_period=oData_TimePeriod,
            data_ts=oData_Dynamic_Outcome_TS,
            data_gridded=oData_Dynamic_Outcome_Gridded,
            settings=oData_Settings,
            file=oData_Path,
            mapping=oData_Mapping,
            tags=removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute']))
        if not (exists(defineString(oData_Path['file_product_ts'], oData_Tags))) or not (
                exists(defineString(oData_Path['file_product_gridded'], oData_Tags))):
            oDrv_DataFinalizer_Dynamic.saveDataAnalysis(oData_Dynamic_Source, oData_Section, oData_Geo)
            oLogStream.info(' --> Save dynamic data ... DONE')
        else:
            oLogStream.info(' --> Save dynamic data ... SKIPPED! Data previously saved.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Clean buffer file(s) and folder(s)
        DataAnalysisCleaner(
            flag=[oData_Flags['cleaning_dynamic_data_source'],
                  oData_Flags['cleaning_dynamic_data_outcome_ts'],
                  oData_Flags['cleaning_dynamic_data_outcome_gridded']
                  ],
            file=[[defineString(oData_Path['file_buffer_source_info'], oData_Tags),
                   defineString(oData_Path['file_buffer_source_data'], oData_Tags)],
                  defineString(oData_Path['file_buffer_outcome_ts'], oData_Tags),
                  defineString(oData_Path['file_buffer_outcome_gridded'], oData_Tags),
                  ]
        ).cleanDataAnalysis()
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Note about script parameter(s)
    oLogStream.info('NOTE - Algorithm parameter(s)')
    oLogStream.info('Script: ' + str(sScriptName))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # End Program
    dTimeElapsed = round(time.time() - dStartTime, 1)

    oLogStream.info('[' + sProjectName + ' ' + sAlgType + ' - ' + sAlgName + ' (Version ' + sProgramVersion + ')]')
    oLogStream.info('End Program - Time elapsed: ' + str(dTimeElapsed) + ' seconds')

    Exc.getExc('', 0, 0)
    # -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def GetArgs():
    oParser = argparse.ArgumentParser()
    oParser.add_argument('-settings_file', action="store", dest="sSettingFile")
    oParser.add_argument('-time', action="store", dest="sTimeArg")
    oParserValue = oParser.parse_args()

    sScriptName = oParser.prog

    if oParserValue.sSettingFile:
        sSettingsFile = oParserValue.sSettingFile
    else:
        sSettingsFile = 'configuration.json'

    if oParserValue.sTimeArg:
        sTimeArg = oParserValue.sTimeArg
    else:
        sTimeArg = ''

    return sScriptName, sSettingsFile, sTimeArg

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
