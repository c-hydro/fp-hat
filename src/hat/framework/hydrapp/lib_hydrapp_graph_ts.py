"""
Library Features:

Name:          lib_hydrapp_graph_ts
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190226'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os

import pandas as pd
import numpy as np

import matplotlib as mpl
import matplotlib.pylab as plt
from matplotlib.patches import Rectangle

from src.hat.framework.hydrapp.lib_hydrapp_graph_configuration import configGraphData_TS, \
    configGraphHeader_TS, configGraphTime_TS
from src.hat.framework.hydrapp.lib_hydrapp_graph_analysis import computeVarQuantile, computeVarPeaks, \
    filterVarOutlier, detectVarOutlier, filterVarLimit
from src.hat.framework.hydrapp.lib_hydrapp_graph_utils import setGraphRange_Rain, setGraphRange_Discharge
from src.hat.framework.hydrapp.lib_hydrapp_io_method import writeFileGraph_JSON

from src.common.utils.lib_utils_op_system import createFolderByFile

from src.common.default.lib_default_args import sLoggerName, sTimeFormat
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################

# -------------------------------------------------------------------------------------
# Colours
# '#000000' == BLACK
# '#D3D3D3' == LIGHT GRAY
# '#A9A9A9' == DARK GRAY
# '#008000' == GREEN
# '#FF0000' == RED
# '#FFA500' == ORANGE
# '#33A1C9' == BLUE PEACOCK
# '#236B8E' == BLUE STEAL
# '#0000FF' == BLUE
# '#DA70D6' == ORCHID
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to plot time-series observed data
def plotTS_OBS(sFileName, oTimeRun,
               oRain_OBS, oRain_Accumulated_OBS, oSoilMoisture_OBS,
               oDischarge_OBS=None, oDischarge_MOD_OBS=None,
               sTypeRun='OBS_WeatherStations', iFigDPI=120):

    # -------------------------------------------------------------------------------------
    # Check function
    try:
        # -------------------------------------------------------------------------------------
        # Get data values and metadata
        oRain_OBS_VAL, oRain_OBS_META = configGraphData_TS(oRain_OBS)
        oRain_ACC_OBS_VAL, oRain_ACC_OBS_META = configGraphData_TS(oRain_Accumulated_OBS)

        oDischarge_OBS_VAL, oDischarge_OBS_META = configGraphData_TS(oDischarge_OBS)
        oDischarge_MOD_OBS_VAL, oDischarge_MOD_OBS_META = configGraphData_TS(oDischarge_MOD_OBS)

        oSoilMoisture_OBS_VAL, oSoilMoisture_OBS_META = configGraphData_TS(oSoilMoisture_OBS)

        # Get time information
        [oVarTick_TimePeriod, oVarTick_TimeIdx, oVarTick_TimeLabels] = configGraphTime_TS(oRain_OBS_VAL)
        sTimeRun = oTimeRun.strftime(sTimeFormat)

        # Get header information
        oVarHeader = configGraphHeader_TS(oRain_OBS_META)

        # Set graph range (rain and discharge)
        dRain_MIN_GRAPH, dRain_MAX_GRAPH = setGraphRange_Rain(oRain_OBS_META)
        dDischarge_MIN_GRAPH, dDischarge_MAX_GRAPH = setGraphRange_Discharge(oDischarge_MOD_OBS_META)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Open figure
        fig = plt.figure(figsize=(17, 11))
        fig.autofmt_xdate()

        # Subplot 1
        ax1 = plt.subplot(3, 1, 1)
        p11 = ax1.bar(oRain_OBS_VAL.index, oRain_OBS_VAL.values,
                      color='#33A1C9', alpha=1, width=0.025, align='edge')

        ax1.set_xticks(oVarTick_TimeIdx)
        ax1.set_xticklabels([])

        ax1.set_xlim(oVarTick_TimePeriod[0], oVarTick_TimePeriod[-1])
        ax1.set_ylabel('rain [mm]', color='#000000')
        ax1.set_ylim(dRain_MIN_GRAPH, dRain_MAX_GRAPH)
        ax1.grid(b=True)

        p13 = ax1.axvline(oTimeRun, color='#000000', linestyle='--', lw=2)


        ax3 = ax1.twinx()
        p31 = ax3.plot(oRain_ACC_OBS_VAL,
                       color='#33A1C9', linestyle='-', lw=1)

        ax3.set_ylabel('rain accumulated [mm]', color='#000000')
        ax3.set_ylim(0, 500)

        ax3.set_xticks(oVarTick_TimeIdx)
        ax3.set_xticklabels([])
        ax3.set_xlim(oVarTick_TimePeriod[0], oVarTick_TimePeriod[-1])

        # legend = ax1.legend(p11, [oRain_OBS_META['var_appearance']], frameon=False, loc=2)

        legend = ax1.legend(
            (p11[0], p31[0]),
            (oRain_OBS_META['var_appearance'], oRain_ACC_OBS_META['var_appearance'],),
            frameon=False, loc=2)

        ax1.add_artist(legend)

        ax1.set_title('Time Series \n Section: ' + oVarHeader['section_name'] +
                      ' == Basin: ' + oVarHeader['section_basin'] +
                      ' == Area [Km^2]: ' + oVarHeader['section_area'] + ' \n  TypeRun: ' + sTypeRun +
                      ' == Time_Run: ' + sTimeRun)

        # Subplot 2
        ax2 = plt.subplot(3, 1, (2, 3))

        p21 = ax2.plot(oDischarge_OBS_VAL,
                       color='#000000', linestyle='--', lw=1, marker='o', ms=4)
        p22 = ax2.plot(oDischarge_MOD_OBS_VAL,
                       color='#0000FF', linestyle='-', lw=1)

        ax2.set_xlabel('time [hour]', color='#000000')
        ax2.set_xlim(oVarTick_TimePeriod[0], oVarTick_TimePeriod[-1])
        ax2.set_ylabel('discharge [m^3/s]', color='#000000')
        ax2.set_ylim(dDischarge_MIN_GRAPH, dDischarge_MAX_GRAPH)

        ax2.grid(b=True)

        p27 = ax2.axvline(oTimeRun, color='#000000', linestyle='--', lw=2, label='time run')
        p28 = ax2.axhline(float(oVarHeader['section_q_thr1']), color='#FFA500', linestyle='--',
                          linewidth=2, label='discharge thr alarm')
        p29 = ax2.axhline(float(oVarHeader['section_q_thr2']), color='#FF0000', linestyle='--',
                          linewidth=2, label='discharge thr alert')

        ax2.set_xticks(oVarTick_TimeIdx)
        ax2.set_xticklabels(oVarTick_TimeLabels, rotation=45, fontsize=8)

        ax4 = ax2.twinx()
        p41 = ax4.plot(oSoilMoisture_OBS_VAL,
                       color='#DA70D6', linestyle='--', lw=2)

        ax4.set_ylabel('soil moisture [-]', color='#000000')
        ax4.set_ylim(0, 1)
        ax4.set_xticks(oVarTick_TimeIdx)
        ax4.set_xticklabels(oVarTick_TimeLabels, rotation=45, fontsize=8)

        legend1 = ax2.legend(
            (p21[0], p22[0], p41[0]),
            (oDischarge_OBS_META['var_appearance'],
             oDischarge_MOD_OBS_META['var_appearance'],
             oSoilMoisture_OBS_META['var_appearance']),
            frameon=False, ncol=2, loc=0)
        legend2 = ax2.legend(
            (p28, p29),
            ('discharge thr alarm', 'discharge thr alert'),
            frameon=False, ncol=4, loc=9, bbox_to_anchor=(0.5, -0.2))

        ax2.add_artist(legend1)
        ax2.add_artist(legend2)

        # plt.show()
        if not os.path.exists(sFileName):
            createFolderByFile(sFileName)
        fig.savefig(sFileName, dpi=iFigDPI)

        plt.close()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Write ancillary file in json format (to configure png attributes)
        if os.path.exists(sFileName):
            sFileRoot = os.path.splitext(sFileName)[0]
            writeFileGraph_JSON(sFileRoot + '.json', oDischarge_MOD_OBS_META)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Exit with success
        oGraphStatus = True
        # -------------------------------------------------------------------------------------

    except BaseException:

        # -------------------------------------------------------------------------------------
        # Exit with warning
        Exc.getExc(' =====> WARNING: graph ' + sTypeRun + ' in ' + sFileName +
                   ' failed! Error(s) occurred in plot generation! ', 2, 1)
        oGraphStatus = False
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return code
    return oGraphStatus
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to plot time-series NWP probabilistic data
def plotTS_NWP_Probabilistic(sFileName, oTimeRun,
                             oRain_OBS, oRain_NWP_DET, oRain_NWP_PROB,
                             oDischarge_MOD_NWP_DET, oDischarge_MOD_NWP_PROB,
                             oRain_Accumulated_OBS, oRain_Accumulated_NWP_DET,
                             oSoilMoisture_OBS,
                             oDischarge_OBS=None, oDischarge_MOD_OBS=None,
                             sTypeRun='NWP_Probabilistic', iFigDPI=120, bOutlierDetection=False):

    # -------------------------------------------------------------------------------------
    # Check function
    try:

        # -------------------------------------------------------------------------------------
        # Get data values and metadata
        oRain_OBS_VAL, oRain_OBS_META = configGraphData_TS(oRain_OBS)
        oRain_NWP_DET_VAL, oRain_NWP_DET_META = configGraphData_TS(oRain_NWP_DET)
        oRain_NWP_PROB_VAL, oRain_NWP_PROB_META = configGraphData_TS(oRain_NWP_PROB)

        oRain_ACC_OBS_VAL, oRain_ACC_OBS_META = configGraphData_TS(oRain_Accumulated_OBS)
        oRain_ACC_NWP_DET_VAL, oRain_ACC_NWP_DET_META = configGraphData_TS(oRain_Accumulated_NWP_DET)

        oDischarge_OBS_VAL, oDischarge_OBS_META = configGraphData_TS(oDischarge_OBS)
        oDischarge_MOD_OBS_VAL, oDischarge_MOD_OBS_META = configGraphData_TS(oDischarge_MOD_OBS)
        oDischarge_MOD_NWP_DET_VAL, oDischarge_MOD_NWP_DET_META = configGraphData_TS(oDischarge_MOD_NWP_DET)
        oDischarge_MOD_NWP_PROB_VAL, oDischarge_MOD_NWP_PROB_META = configGraphData_TS(oDischarge_MOD_NWP_PROB)

        oSoilMoisture_OBS_VAL, oSoilMoisture_OBS_META = configGraphData_TS(oSoilMoisture_OBS)

        oDischarge_MOD_OBS_VAL = filterVarLimit(oDischarge_MOD_OBS_VAL,
                                                oDischarge_MOD_OBS_META, dVar_MAX_OUTLIER=10000)
        oDischarge_MOD_NWP_DET_VAL = filterVarLimit(oDischarge_MOD_NWP_DET_VAL,
                                                    oDischarge_MOD_NWP_DET_META, dVar_MAX_OUTLIER=10000)
        oDischarge_MOD_NWP_PROB_VAL = filterVarLimit(oDischarge_MOD_NWP_PROB_VAL,
                                                     oDischarge_MOD_NWP_PROB_META, dVar_MAX_OUTLIER=10000)

        if hasattr(oDischarge_MOD_NWP_PROB_VAL, 'min'):
            del oDischarge_MOD_NWP_PROB_VAL.min
        if hasattr(oDischarge_MOD_NWP_PROB_VAL, 'max'):
            del oDischarge_MOD_NWP_PROB_VAL.max

        if bOutlierDetection:
            oDischarge_MOD_NWP_PROB, bVarData_OUTLIER = detectVarOutlier(oDischarge_MOD_NWP_PROB_VAL)
            if bVarData_OUTLIER:
                oDischarge_MOD_NWP_PROB_FILTER = filterVarOutlier(oDischarge_MOD_NWP_PROB)
            else:
                oDischarge_MOD_NWP_PROB_FILTER = oDischarge_MOD_NWP_PROB
        else:
            oDischarge_MOD_NWP_PROB_FILTER = oDischarge_MOD_NWP_PROB_VAL
            oDischarge_MOD_NWP_PROB_FILTER.iloc[-1] = np.nan

        # Compute nwp probabilistic peak(s)
        oDischarge_MOD_NWP_PROB_PEAKS = computeVarPeaks(oDischarge_MOD_NWP_PROB_FILTER, dVar_PEAK_MIN=0)

        # Compute nwp probabilistic quantile(s)
        oDischarge_MOD_NWP_PROB = computeVarQuantile(
            oDischarge_MOD_NWP_PROB_FILTER, sVarData_QTL='qtls', oVarData_QTL=[0, 0.25, 0.5, 0.75, 1], iVarAxis=1)

        # Get time information
        [oVarTick_TimePeriod, oVarTick_TimeIdx, oVarTick_TimeLabels] = configGraphTime_TS(oRain_OBS_VAL)
        sTimeRun = oTimeRun.strftime(sTimeFormat)
        sTimeNWP = oDischarge_MOD_NWP_DET_META['time_dataset']

        # Get header information
        oVarHeader = configGraphHeader_TS(oRain_OBS_META)

        # Set graph range (rain and discharge)
        dRain_MIN_GRAPH, dRain_MAX_GRAPH = setGraphRange_Rain(oRain_OBS_META)
        dDischarge_MIN_GRAPH, dDischarge_MAX_GRAPH = setGraphRange_Discharge(
            oDischarge_MOD_OBS_META, dVar_MIN_OUTLIER=0, dVar_MAX_OUTLIER=10000)

        if sTimeNWP is None:
            sTimeNWP = "NA"
            oTimeNWP = None
        else:
            oTimeNWP = pd.Timestamp(sTimeNWP)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Open figure
        fig = plt.figure(figsize=(17, 11))
        fig.autofmt_xdate()

        mpl.rcParams['hatch.linewidth'] = 0.01
        mpl.rcParams['hatch.color'] = '#0000FF'

        # Subplot 1
        ax1 = plt.subplot(3, 1, 1)
        p11 = ax1.bar(oRain_OBS_VAL.index, oRain_OBS_VAL.values,
                      color='#33A1C9', alpha=1, width=0.025, align='edge')
        p12 = ax1.bar(oRain_NWP_DET_VAL.index, oRain_NWP_DET_VAL.values,
                      edgecolor='#0000FF', color='None', alpha=1, width=0.025, align='edge') # hatch="/"

        ax1.set_xticks(oVarTick_TimeIdx)
        ax1.set_xticklabels([])

        ax1.set_xlim(oVarTick_TimePeriod[0], oVarTick_TimePeriod[-1])
        ax1.set_ylabel('rain [mm]', color='#000000')
        ax1.set_ylim(dRain_MIN_GRAPH, dRain_MAX_GRAPH)
        ax1.grid(b=True)

        p13 = ax1.axvline(oTimeRun, color='#000000', linestyle='--', lw=2)
        if oTimeNWP:
            p14 = ax1.axvline(oTimeNWP, color='#FF5733', linestyle='--', lw=2)

        ax1.set_title('Time Series \n Section: ' + oVarHeader['section_name'] +
                      ' == Basin: ' + oVarHeader['section_basin'] +
                      ' == Area [Km^2]: ' + oVarHeader['section_area'] + ' \n  TypeRun: ' + sTypeRun +
                      ' == Time_Run: ' + sTimeRun + ' Time_NWP: ' + sTimeNWP)

        ax3 = ax1.twinx()
        p31 = ax3.plot(oRain_ACC_OBS_VAL,
                       color='#33A1C9', linestyle='-', lw=1)
        p32 = ax3.plot(oRain_ACC_NWP_DET_VAL,
                       color='#0000FF', linestyle='-', lw=1)

        ax3.set_ylabel('rain accumulated [mm]', color='#000000')
        ax3.set_ylim(0, 500)

        ax3.set_xticks(oVarTick_TimeIdx)
        ax3.set_xticklabels([])
        ax3.set_xlim(oVarTick_TimePeriod[0], oVarTick_TimePeriod[-1])

        legend = ax1.legend(
            (p11[0], p12[0], p31[0], p32[0]),
            (oRain_OBS_META['var_appearance'],
             oRain_NWP_DET_META['var_appearance'],
             oRain_ACC_OBS_META['var_appearance'],
             oRain_ACC_NWP_DET_META['var_appearance'],
             ),
            frameon=False, loc=2)

        ax1.add_artist(legend)

        # Subplot 2
        ax2 = plt.subplot(3, 1, (2, 3))

        p21 = ax2.plot(oDischarge_OBS_VAL,
                       color='#000000', linestyle='--', lw=1, marker='o', ms=4)
        p22 = ax2.plot(oDischarge_MOD_OBS_VAL,
                       color='#0000FF', linestyle='-', lw=1)
        p23 = ax2.plot(oDischarge_MOD_NWP_DET_VAL,
                       color='#008000', linestyle='-', lw=1)

        ax2.fill_between(oDischarge_MOD_NWP_PROB.index,
                         oDischarge_MOD_NWP_PROB['qtls0.0'].values, oDischarge_MOD_NWP_PROB['qtls0.25'].values,
                         where=oDischarge_MOD_NWP_PROB['qtls0.25'] > oDischarge_MOD_NWP_PROB['qtls0.0'],
                         facecolor='#D3D3D3', alpha=10, interpolate=False)
        p24 = Rectangle((0, 0), 1, 1, fc='#D3D3D3')
        ax2.fill_between(oDischarge_MOD_NWP_PROB.index,
                         oDischarge_MOD_NWP_PROB['qtls0.25'].values, oDischarge_MOD_NWP_PROB['qtls0.75'].values,
                         where=oDischarge_MOD_NWP_PROB['qtls0.75'] >= oDischarge_MOD_NWP_PROB['qtls0.25'],
                         facecolor='#A9A9A9', alpha=10, interpolate=False)
        p25 = Rectangle((0, 0), 1, 1, fc='#A9A9A9')
        ax2.fill_between(oDischarge_MOD_NWP_PROB.index,
                         oDischarge_MOD_NWP_PROB['qtls0.75'].values, oDischarge_MOD_NWP_PROB['qtls1.0'].values,
                         where=oDischarge_MOD_NWP_PROB['qtls1.0'] >= oDischarge_MOD_NWP_PROB['qtls0.75'],
                         facecolor='#D3D3D3', alpha=10, interpolate=False)
        p26 = Rectangle((0, 0), 1, 1, fc='#D3D3D3')

        p27 = ax2.plot(pd.DatetimeIndex(oDischarge_MOD_NWP_PROB_PEAKS.time), oDischarge_MOD_NWP_PROB_PEAKS.peak,
                       color='#0000FF', linestyle='-', lw=0, marker='*', ms=4)
        p28 = Rectangle((0, 0), 1, 1, fc='#0000FF')

        ax2.set_xlabel('time [hour]', color='#000000')
        ax2.set_xlim(oVarTick_TimePeriod[0], oVarTick_TimePeriod[-1])
        ax2.set_ylabel('discharge [m^3/s]', color='#000000')
        ax2.set_ylim(dDischarge_MIN_GRAPH, dDischarge_MAX_GRAPH)

        ax2.grid(b=True)

        p29 = ax2.axvline(oTimeRun, color='#000000', linestyle='--', lw=2, label='time run')

        p210 = ax2.axhline(float(oVarHeader['section_q_thr1']), color='#FFA500', linestyle='--',
                           linewidth=2, label='discharge thr alarm')
        p211 = ax2.axhline(float(oVarHeader['section_q_thr2']), color='#FF0000', linestyle='--',
                           linewidth=2, label='discharge thr alert')

        if oTimeNWP:
            p212 = ax2.axvline(oTimeNWP, color='#FF5733', linestyle='--', lw=2, label='time nwp')

        ax2.set_xticks(oVarTick_TimeIdx)
        ax2.set_xticklabels(oVarTick_TimeLabels, rotation=45, fontsize=8)

        ax4 = ax2.twinx()
        p41 = ax4.plot(oSoilMoisture_OBS_VAL,
                       color='#DA70D6', linestyle='--', lw=2)

        ax4.set_ylabel('soil moisture [-]', color='#000000')
        ax4.set_ylim(0, 1)
        ax4.set_xticks(oVarTick_TimeIdx)
        ax4.set_xticklabels(oVarTick_TimeLabels, rotation=45, fontsize=8)

        legend1 = ax2.legend(
            (p21[0], p22[0], p23[0], p41[0]),
            (oDischarge_OBS_META['var_appearance'],
             oDischarge_MOD_OBS_META['var_appearance'],
             oDischarge_MOD_NWP_DET_META['var_appearance'],
             oSoilMoisture_OBS_META['var_appearance'],
             ),
            frameon=False, ncol=2, loc=0)
        legend2 = ax2.legend(
            (p24, p25, p210, p211),
            ('< 25% -- 75% >', '25% -- 75%', 'discharge thr alarm', 'discharge thr alert'),
            frameon=False, ncol=4, loc=9, bbox_to_anchor=(0.5, -0.2))

        ax2.add_artist(legend1)
        ax2.add_artist(legend2)

        # plt.show()
        if not os.path.exists(sFileName):
            createFolderByFile(sFileName)
        fig.savefig(sFileName, dpi=iFigDPI)

        plt.close()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Write ancillary file in json format (to configure png attributes)
        if os.path.exists(sFileName):
            sFileRoot = os.path.splitext(sFileName)[0]
            writeFileGraph_JSON(sFileRoot + '.json', oDischarge_MOD_NWP_PROB_META)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Exit with success
        oGraphStatus = True
        # -------------------------------------------------------------------------------------

    except BaseException:

        # -------------------------------------------------------------------------------------
        # Exit with warning
        Exc.getExc(' =====> WARNING: graph ' + sTypeRun + ' in ' + sFileName +
                   ' failed! Error(s) occurred in plot generation! ', 2, 1)
        oGraphStatus = False
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return code
    return oGraphStatus
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


