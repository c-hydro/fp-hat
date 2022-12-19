"""
Library Features:

Name:          lib_graph_ts
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""
#######################################################################################
# Libraries
import logging
import os

import matplotlib.pylab as plt
import pandas as pd

from copy import deepcopy

from lib_utils_system import make_folder
from lib_graph_ts_utils import configure_ts_attrs, configure_ts_axes, get_ts_attrs, set_ax_limits_discharge

from lib_info_args import logger_name, time_format_algorithm

# Logging
logging.getLogger("matplotlib").setLevel(logging.WARNING)
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to plot discharge time-series for observed mode
def plot_ts_discharge_obs(
        file_name, file_attributes,
        df_rain,
        df_discharge_sim,
        df_soil_moisture,
        df_discharge_obs=None,
        value_min_discharge=0, value_max_discharge=100,
        value_min_rain_avg=0, value_max_rain_avg=20,
        value_min_rain_accumulated=0, value_max_rain_accumulated=100,
        value_min_soil_moisture=0, value_max_soil_moisture=1,
        tag_time_name='time', tag_time_units='[hour]', tag_time_type='UTC',
        tag_discharge_generic_name='Discharge',
        tag_discharge_sim_name='Discharge Simulated',
        tag_discharge_obs_name='Discharge Observed', tag_discharge_units='[m^3/s]',
        tag_rain_avg_name='Rain Avg', tag_rain_accumulated_name='Rain Accumulated', tag_rain_units='[mm]',
        tag_soil_moisture_name='Soil Moisture', tag_soil_moisture_units='[-]',
        tag_discharge_thr_alarm='discharge thr alarm', tag_discharge_thr_alert='discharge thr alert',
        tag_sep=' ', fig_dpi=120):

    # Configure ts attributes
    attrs_ts = configure_ts_attrs(file_attributes)
    # Configure ts time axes
    [tick_time_period, tick_time_idx, tick_time_labels] = configure_ts_axes(df_discharge_sim)

    # Axis labels
    label_time = tag_sep.join([tag_time_name, tag_time_units])
    label_discharge_generic = tag_sep.join([tag_discharge_generic_name, tag_discharge_units])
    label_discharge_sim = tag_sep.join([tag_discharge_sim_name, tag_discharge_units])
    label_discharge_obs = tag_sep.join([tag_discharge_obs_name, tag_discharge_units])
    label_rain_avg = tag_sep.join([tag_rain_avg_name, tag_rain_units])
    label_rain_accumulated = tag_sep.join([tag_rain_accumulated_name, tag_rain_units])
    label_soil_moisture = tag_sep.join([tag_soil_moisture_name, tag_soil_moisture_units])

    time_run = attrs_ts['time_run'].strftime(format=time_format_algorithm)
    time_restart = attrs_ts['time_restart'].strftime(format=time_format_algorithm)
    time_start = attrs_ts['time_start'].strftime(format=time_format_algorithm)

    section_name, section_domain, \
        section_discharge_thr_alert, section_discharge_thr_alarm, \
        section_drained_area = get_ts_attrs(attrs_ts)

    axs_min_discharge, axs_max_discharge = set_ax_limits_discharge(
        max_value_dyn=section_discharge_thr_alarm,
        min_value_default=value_min_discharge, max_value_default=value_max_discharge)

    if df_discharge_obs is None:
        df_values = deepcopy(df_discharge_sim.values)
        df_index = deepcopy(df_discharge_sim.index)
        df_values[:, 0] = -9996.0
        df_discharge_obs = pd.DataFrame(data=df_values, index=df_index)

    figure_title = 'Time Series \n Section: "' + section_name + '"' +  \
                   ' == Basin: "' + section_domain + '"' +  \
                   ' == Area [Km^2]: "' + str(section_drained_area) + '" \n  TypeRun: "' + attrs_ts['run_name'] + '"' + \
                   ' == Time_Run: "' + time_run + '" == Time_Restart_HMC: "' + time_restart + '"' + \
                   ' == Time_Start_HMC: "' + time_start + '" == Time Reference System: "' + tag_time_type + '"'

    # Open figure
    fig = plt.figure(figsize=(17, 11))
    fig.autofmt_xdate()

    # Subplot 1 [RAIN]
    ax1 = plt.subplot(3, 1, 1)
    ax1.set_xticks(tick_time_idx)
    ax1.set_xticklabels([])

    ax1.set_xlim(tick_time_period[0], tick_time_period[-1])
    ax1.set_ylabel(label_rain_avg, color='#000000')
    ax1.set_ylim(value_min_rain_avg, value_max_rain_avg)
    ax1.grid(b=True)

    p11 = ax1.bar(df_rain.index, df_rain.values[:, 0],
                  color='#33A1C9', alpha=1, width=0.025, align='edge')

    p13 = ax1.axvline(attrs_ts['time_run'], color='#000000', linestyle='--', lw=2)

    ax3 = ax1.twinx()
    ax3.set_ylabel(label_rain_accumulated, color='#000000')
    ax3.set_ylim(value_min_rain_accumulated, value_max_rain_accumulated)

    ax3.set_xticks(tick_time_idx)
    ax3.set_xticklabels([])
    ax3.set_xlim(tick_time_period[0], tick_time_period[-1])

    p31 = ax3.plot(df_rain.index, df_rain.cumsum().values[:, 0],
                   color='#33A1C9', linestyle='-', lw=1)

    # legend = ax1.legend(p11, [oRain_OBS_META['var_appearance']], frameon=False, loc=2)

    legend = ax1.legend((p11[0], p31[0]),
                        (tag_rain_avg_name, tag_rain_accumulated_name,),
                        frameon=False, loc=2)

    ax1.add_artist(legend)
    ax1.set_title(figure_title, size=12, color='black', weight='bold')

    # Subplot 2 [DISCHARGE]
    ax2 = plt.subplot(3, 1, (2, 3))
    p21 = ax2.plot(df_discharge_obs.index, df_discharge_obs.values[:, 0],
                   color='#000000', linestyle='--', lw=1, marker='o', ms=4)
    p22 = ax2.plot(df_discharge_sim.index, df_discharge_sim.values[:, 0],
                   color='#0000FF', linestyle='-', lw=1)

    ax2.set_xlabel(label_time, color='#000000')
    ax2.set_xlim(tick_time_period[0], tick_time_period[-1])
    ax2.set_ylabel(label_discharge_generic, color='#000000')
    ax2.set_ylim(axs_min_discharge, axs_max_discharge)
    ax2.grid(b=True)

    p27 = ax2.axvline(attrs_ts['time_run'], color='#000000', linestyle='--', lw=2, label='time run')

    p28, p29 = None, None
    if (section_discharge_thr_alert is not None) and (section_discharge_thr_alert >= 0):
        p28 = ax2.axhline(section_discharge_thr_alert, color='#FFA500', linestyle='--',
                          linewidth=2, label=tag_discharge_thr_alert)
    if (section_discharge_thr_alarm is not None) and (section_discharge_thr_alarm >= 0):
        p29 = ax2.axhline(section_discharge_thr_alarm, color='#FF0000', linestyle='--',
                          linewidth=2, label=tag_discharge_thr_alarm)


    ax2.set_xticks(tick_time_idx)
    ax2.set_xticklabels(tick_time_labels, rotation=90, fontsize=8)

    ax4 = ax2.twinx()
    p41 = ax4.plot(df_soil_moisture.index, df_soil_moisture.values[:, 0],
                   color='#DA70D6', linestyle='--', lw=2)

    ax4.set_ylabel(label_soil_moisture, color='#000000')
    ax4.set_ylim(value_min_soil_moisture, value_max_soil_moisture)

    ax4.set_xticks(tick_time_idx)
    ax4.set_xticklabels(tick_time_labels, rotation=90, fontsize=8)

    legend1 = ax2.legend((p21[0], p22[0], p41[0]),
                         (tag_discharge_obs_name, tag_discharge_sim_name, tag_soil_moisture_name),
                         frameon=False, ncol=2, loc=0)

    ax2.add_artist(legend1)
    if (p28 is not None) and (p29 is not None):
        legend2 = ax2.legend((p28, p29),
                             (tag_discharge_thr_alert, tag_discharge_thr_alarm),
                             frameon=False, ncol=4, loc=9, bbox_to_anchor=(0.5, -0.2))
        ax2.add_artist(legend2)

    file_path, file_folder = os.path.split(file_name)

    if not os.path.exists(file_path):
        make_folder(file_path)
    fig.savefig(file_name, dpi=fig_dpi)

    # plt.show()
    plt.close()

# -------------------------------------------------------------------------------------
