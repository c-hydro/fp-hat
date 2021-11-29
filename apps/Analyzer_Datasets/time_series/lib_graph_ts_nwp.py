"""
Library Features:

Name:          lib_graph_ts_nwp
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210113'
Version:       '1.0.0'
"""
#######################################################################################
# Libraries
import logging
import os
import pandas as pd

import matplotlib.pylab as plt
from matplotlib.patches import Rectangle

from lib_utils_system import make_folder

from copy import deepcopy

from lib_graph_ts_utils import configure_ts_axes, configure_ts_attrs, \
    compute_ts_peaks, compute_ts_quantile, compute_ts_ensemble_avg

from lib_info_args import logger_name, time_format_algorithm

# Logging
logging.getLogger("matplotlib").setLevel(logging.WARNING)
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to plot discharge time-series for nwp probabilistic comparison mode
def plot_ts_discharge_nwp_probabilistic_comparison(
        file_name,
        file_attributes_ground_network,
        file_attributes_nwp_deterministic_01, file_attributes_nwp_deterministic_02,
        file_attributes_nwp_probabilistic_01, file_attributes_nwp_probabilistic_02,
        df_rain_ground_network,
        df_rain_nwp_deterministic_01, df_rain_nwp_deterministic_02,
        df_rain_nwp_probabilistic_01, df_rain_nwp_probabilistic_02,
        df_discharge_simulated_ground_network,
        df_discharge_simulated_nwp_deterministic_01, df_discharge_simulated_nwp_deterministic_02,
        df_discharge_simulated_nwp_probabilistic_01, df_discharge_simulated_nwp_probabilistic_02,
        df_soil_moisture_ground_network,
        df_soil_moisture_nwp_deterministic_01, df_soil_moisture_nwp_deterministic_02,
        df_soil_moisture_nwp_probabilistic_01, df_soil_moisture_nwp_probabilistic_02,
        df_discharge_observed=None,
        value_min_discharge=0, value_max_discharge=100,
        value_min_rain_avg=0, value_max_rain_avg=20,
        value_min_rain_accumulated=0, value_max_rain_accumulated=100,
        value_min_soil_moisture=0, value_max_soil_moisture=1,
        tag_type_run=None,
        tag_time_name='time', tag_time_units='[hour]',
        tag_discharge_generic_name='Discharge',
        tag_discharge_sim_name_ground_network='Discharge Simulated Ground Network',
        tag_discharge_sim_name_nwp_01='Discharge Simulated NWP Probabilistic M1',
        tag_discharge_sim_name_nwp_02='Discharge Simulated NWP Probabilistic M2',
        tag_discharge_obs_name='Discharge Observed', tag_discharge_units='[m^3/s]',
        tag_rain_avg_generic_name='Rain Avg',
        tag_rain_avg_name_ground_network='Rain Avg Ground Network',
        tag_rain_avg_name_nwp_01='Rain Avg NWP M1',
        tag_rain_avg_name_nwp_02='Rain Avg NWP M2',
        tag_rain_accumulated_generic_name='Rain Accumulated',
        tag_rain_accumulated_name_ground_network='Rain Accumulated Ground Network',
        tag_rain_accumulated_name_nwp_01='Rain Accumulated NWP M1',
        tag_rain_accumulated_name_nwp_02='Rain Accumulated NWP M2',
        tag_rain_units='[mm]',
        tag_soil_moisture_generic_name='Soil Moisture Avg',
        tag_soil_moisture_name_nwp_01='Soil Moisture Avg M1',
        tag_soil_moisture_name_nwp_02='Soil Moisture Avg M2',
        tag_soil_moisture_units='[-]',
        tag_discharge_thr_alarm='discharge thr alarm', tag_discharge_thr_alert='discharge thr alert',
        tag_sep=' ',
        label_title_time_run_nwp_01='Time_Run_NWP_M1', label_title_time_run_nwp_02='Time_Run_NWP_M2',
        fig_dpi=120):

    # Configure ts attributes
    attrs_ts_ground_network = configure_ts_attrs(file_attributes_ground_network)
    attrs_ts_nwp_prob_01 = configure_ts_attrs(file_attributes_nwp_probabilistic_01)
    attrs_ts_nwp_prob_02 = configure_ts_attrs(file_attributes_nwp_probabilistic_02)

    # Configure ts time axes
    [tick_time_period, tick_time_idx, tick_time_labels] = configure_ts_axes(df_soil_moisture_ground_network)

    # Axis labels
    label_time = tag_sep.join([tag_time_name, tag_time_units])
    label_discharge_generic = tag_sep.join([tag_discharge_generic_name, tag_discharge_units])
    label_discharge_sim_ground_network = tag_sep.join([tag_discharge_sim_name_ground_network, tag_discharge_units])
    label_discharge_sim_nwp_01 = tag_sep.join([tag_discharge_sim_name_nwp_01, tag_discharge_units])
    label_discharge_sim_nwp_02 = tag_sep.join([tag_discharge_sim_name_nwp_02, tag_discharge_units])
    label_discharge_obs = tag_sep.join([tag_discharge_obs_name, tag_discharge_units])
    label_rain_avg = tag_sep.join([tag_rain_avg_generic_name, tag_rain_units])
    label_rain_accumulated = tag_sep.join([tag_rain_accumulated_generic_name, tag_rain_units])
    label_soil_moisture = tag_sep.join([tag_soil_moisture_generic_name, tag_soil_moisture_units])

    time_run_ground_network = attrs_ts_ground_network['time_run'].strftime(format=time_format_algorithm)
    time_run_nwp_prob_01 = attrs_ts_nwp_prob_01['time_run'].strftime(format=time_format_algorithm)
    time_run_nwp_prob_02 = attrs_ts_nwp_prob_02['time_run'].strftime(format=time_format_algorithm)

    time_restart = attrs_ts_ground_network['time_restart'].strftime(format=time_format_algorithm)
    time_start = attrs_ts_ground_network['time_start'].strftime(format=time_format_algorithm)
    section_drained_area = str(attrs_ts_ground_network['section_drained_area'])
    section_name = attrs_ts_ground_network['section_name']
    section_domain = attrs_ts_ground_network['section_domain']

    if tag_type_run is None:
        tag_type_run = 'nwp probabilistic comparison'

    # Compute nwp probabilistic peak(s)
    df_discharge_simulated_peaks_probabilistic_01 = compute_ts_peaks(
        df_discharge_simulated_nwp_probabilistic_01, peak_value_min=0, peak_timestr_min=time_run_ground_network)
    # Compute nwp probabilistic discharge quantile(s)
    df_discharge_simulated_nwp_probabilistic_01 = compute_ts_quantile(
        df_discharge_simulated_nwp_probabilistic_01,
        variable_qtls_name='qtls', variable_qtls_list=[0, 0.25, 0.5, 0.75, 1], variable_qtls_axis=1)
    df_discharge_simulated_peaks_probabilistic_02 = compute_ts_peaks(
        df_discharge_simulated_nwp_probabilistic_02, peak_value_min=0, peak_timestr_min=time_run_ground_network)
    # Compute nwp probabilistic discharge quantile(s)
    df_discharge_simulated_nwp_probabilistic_02 = compute_ts_quantile(
        df_discharge_simulated_nwp_probabilistic_02,
        variable_qtls_name='qtls', variable_qtls_list=[0, 0.25, 0.5, 0.75, 1], variable_qtls_axis=1)

    # Compute nwp probabilistic rain quantile(s)
    df_rain_nwp_probabilistic_01 = compute_ts_quantile(
        df_rain_nwp_probabilistic_01,
        variable_qtls_name='qtls', variable_qtls_list=[0, 0.25, 0.5, 0.75, 1], variable_qtls_axis=1)
    df_rain_nwp_probabilistic_02 = compute_ts_quantile(
        df_rain_nwp_probabilistic_02,
        variable_qtls_name='qtls', variable_qtls_list=[0, 0.25, 0.5, 0.75, 1], variable_qtls_axis=1)

    # Compute nwp probabilistic soil moisture average
    df_soil_moisture_avg_probabilistic_01 = compute_ts_ensemble_avg(
        df_soil_moisture_nwp_probabilistic_01, variable_axis=1)
    df_soil_moisture_avg_probabilistic_02 = compute_ts_ensemble_avg(
        df_soil_moisture_nwp_probabilistic_02, variable_axis=1)
    
    if df_discharge_observed is None:
        df_values = deepcopy(df_discharge_simulated_ground_network.values)
        df_index = deepcopy(df_discharge_simulated_ground_network.index)
        df_values[:, 0] = -9996.0
        df_discharge_observed = pd.DataFrame(data=df_values, index=df_index)

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

    p11 = ax1.bar(df_rain_ground_network.index, df_rain_ground_network.values[:, 0],
                  color='#33A1C9', alpha=1, width=0.025, align='edge',
                  fill=False, edgecolor='#33A1C9')
    p12 = ax1.bar(df_rain_nwp_deterministic_01.index, df_rain_nwp_deterministic_01.values[:, 0],
                  color='#0000FF', alpha=1, width=0.025, align='edge',
                  fill=False, edgecolor='#0000FF')
    p13 = ax1.bar(df_rain_nwp_deterministic_02.index, df_rain_nwp_deterministic_02.values[:, 0],
                  color='#003666', alpha=1, width=0.025, align='edge',
                  fill=False, edgecolor='#003666')

    p14 = ax1.axvline(attrs_ts_ground_network['time_run'], color='#000000', linestyle='--', lw=2)
    p15 = ax1.axvline(attrs_ts_nwp_prob_01['time_run'], color='#808080', linestyle='--', lw=2)
    p16 = ax1.axvline(attrs_ts_nwp_prob_02['time_run'], color='#808080', linestyle='--', lw=2)

    ax3 = ax1.twinx()
    ax3.set_ylabel(label_rain_accumulated, color='#000000')
    ax3.set_ylim(value_min_rain_accumulated, value_max_rain_accumulated)

    ax3.set_xticks(tick_time_idx)
    ax3.set_xticklabels([])
    ax3.set_xlim(tick_time_period[0], tick_time_period[-1])

    p31 = ax3.plot(df_rain_ground_network.index, df_rain_ground_network.cumsum().values[:, 0],
                   color='#33A1C9', linestyle='-', lw=1)
    p32 = ax3.plot(df_rain_nwp_deterministic_01.index, df_rain_nwp_deterministic_01.cumsum().values[:, 0],
                   color='#0000FF', linestyle='-', lw=1)
    p33 = ax3.plot(df_rain_nwp_deterministic_02.index, df_rain_nwp_deterministic_02.cumsum().values[:, 0],
                   color='#003666', linestyle='-', lw=1)

    legend = ax1.legend((p11[0], p12[0], p13[0], p31[0], p32[0], p33[0]),
                        (tag_rain_avg_name_ground_network,
                         tag_rain_avg_name_nwp_01, tag_rain_avg_name_nwp_02,
                         tag_rain_accumulated_name_ground_network,
                         tag_rain_accumulated_name_nwp_01, tag_rain_accumulated_name_nwp_02,),
                        frameon=False, loc=2)

    ax1.add_artist(legend)

    ax1.set_title('Time Series \n Section: ' + section_name +
                  ' == Basin: ' + section_domain +
                  ' == Area [Km^2]: ' + section_drained_area + ' \n  TypeRun: ' + tag_type_run + ' \n ' +
                  ' == Time_Run_OBS: ' + time_run_ground_network +
                  ' ' + label_title_time_run_nwp_01 + ': ' + time_run_nwp_prob_01 +
                  ' ' + label_title_time_run_nwp_02 + ': ' + time_run_nwp_prob_02 + '\n' +
                  ' == Time_Restart: ' + time_restart +
                  ' == Time_Start: ' + time_start)

    # Subplot 2 [DISCHARGE]
    ax2 = plt.subplot(3, 1, (2, 3))
    p21 = ax2.plot(df_discharge_observed.index, df_discharge_observed.values[:, 0],
                   color='#000000', linestyle='--', lw=1, marker='o', ms=4)

    p22 = ax2.plot(df_discharge_simulated_ground_network.index, df_discharge_simulated_ground_network.values[:, 0],
                   color='#0000FF', linestyle='-', lw=1)
    p23 = ax2.plot(df_discharge_simulated_nwp_deterministic_01.index, df_discharge_simulated_nwp_deterministic_01.values[:, 0],
                   color='#0F4610', linestyle='-', lw=1)
    p24 = ax2.plot(df_discharge_simulated_nwp_deterministic_02.index, df_discharge_simulated_nwp_deterministic_02.values[:, 0],
                   color='#9C4293', linestyle='-', lw=1)

    ax2.set_xlabel(label_time, color='#000000')
    ax2.set_xlim(tick_time_period[0], tick_time_period[-1])
    ax2.set_ylabel(label_discharge_generic, color='#000000')
    ax2.set_ylim(value_min_discharge, value_max_discharge)
    ax2.grid(b=True)

    # nwp 1
    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic_01.index,
        df_discharge_simulated_nwp_probabilistic_01['qtls0.0'].values,
        df_discharge_simulated_nwp_probabilistic_01['qtls0.25'].values,
        where=df_discharge_simulated_nwp_probabilistic_01['qtls0.25'] > df_discharge_simulated_nwp_probabilistic_01['qtls0.0'],
        facecolor='#D3D3D3', alpha=10, interpolate=False)
    p25 = Rectangle((0, 0), 1, 1, fc='#D3D3D3')

    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic_01.index,
        df_discharge_simulated_nwp_probabilistic_01['qtls0.25'].values,
        df_discharge_simulated_nwp_probabilistic_01['qtls0.75'].values,
        where=df_discharge_simulated_nwp_probabilistic_01['qtls0.75'] >= df_discharge_simulated_nwp_probabilistic_01['qtls0.25'],
        facecolor='#A9A9A9', alpha=10, interpolate=False)
    p26 = Rectangle((0, 0), 1, 1, fc='#A9A9A9')

    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic_01.index,
        df_discharge_simulated_nwp_probabilistic_01['qtls0.75'].values, df_discharge_simulated_nwp_probabilistic_01['qtls1.0'].values,
        where=df_discharge_simulated_nwp_probabilistic_01['qtls1.0'] >= df_discharge_simulated_nwp_probabilistic_01['qtls0.75'],
        facecolor='#D3D3D3', alpha=10, interpolate=False)
    p27 = Rectangle((0, 0), 1, 1, fc='#D3D3D3')

    p28 = ax2.plot(pd.DatetimeIndex(
        df_discharge_simulated_peaks_probabilistic_01.time),
        df_discharge_simulated_peaks_probabilistic_01.peak,
        color='#0000FF', linestyle='-', lw=0, marker='*', ms=4)
    p29 = Rectangle((0, 0), 1, 1, fc='#0000FF')

    # nwp 2
    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic_02.index,
        df_discharge_simulated_nwp_probabilistic_02['qtls0.0'].values,
        df_discharge_simulated_nwp_probabilistic_02['qtls0.25'].values,
        where=df_discharge_simulated_nwp_probabilistic_02['qtls0.25'] > df_discharge_simulated_nwp_probabilistic_02[
            'qtls0.0'],
        facecolor='#F7F8A4', alpha=10, interpolate=False)
    p210 = Rectangle((0, 0), 1, 1, fc='#F7F8A4')

    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic_02.index,
        df_discharge_simulated_nwp_probabilistic_02['qtls0.25'].values,
        df_discharge_simulated_nwp_probabilistic_02['qtls0.75'].values,
        where=df_discharge_simulated_nwp_probabilistic_02['qtls0.75'] >= df_discharge_simulated_nwp_probabilistic_02[
            'qtls0.25'],
        facecolor='#C6C80F', alpha=10, interpolate=False)
    p211 = Rectangle((0, 0), 1, 1, fc='#C6C80F')

    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic_02.index,
        df_discharge_simulated_nwp_probabilistic_02['qtls0.75'].values,
        df_discharge_simulated_nwp_probabilistic_02['qtls1.0'].values,
        where=df_discharge_simulated_nwp_probabilistic_02['qtls1.0'] >= df_discharge_simulated_nwp_probabilistic_02[
            'qtls0.75'],
        facecolor='#F7F8A4', alpha=10, interpolate=False)
    p212 = Rectangle((0, 0), 1, 1, fc='#F7F8A4')

    p213 = ax2.plot(pd.DatetimeIndex(
        df_discharge_simulated_peaks_probabilistic_02.time),
        df_discharge_simulated_peaks_probabilistic_02.peak,
        color='#9C4293', linestyle='-', lw=0, marker='*', ms=4)
    p214 = Rectangle((0, 0), 1, 1, fc='#9C4293')

    p215 = ax2.axvline(attrs_ts_ground_network['time_run'], color='#000000', linestyle='--', lw=2, label='time run obs')
    p216 = ax2.axvline(attrs_ts_nwp_prob_01['time_run'], color='#FF5733', linestyle='--', lw=2, label='time run nwp')
    p217 = ax2.axvline(attrs_ts_nwp_prob_02['time_run'], color='#FF8970', linestyle='--', lw=2, label='time run nwp')

    p218 = ax2.axhline(attrs_ts_ground_network['section_discharge_thr_alert'], color='#FFA500', linestyle='--',
                       linewidth=2, label=tag_discharge_thr_alert)
    p219 = ax2.axhline(attrs_ts_ground_network['section_discharge_thr_alarm'], color='#FF0000', linestyle='--',
                       linewidth=2, label=tag_discharge_thr_alarm)

    ax2.set_xticks(tick_time_idx)
    ax2.set_xticklabels(tick_time_labels, rotation=90, fontsize=8)

    ax4 = ax2.twinx()
    p41 = ax4.plot(df_soil_moisture_avg_probabilistic_01.index, df_soil_moisture_avg_probabilistic_01.values[:, 0],
                   color='#DA70D6', linestyle='--', lw=2)
    p42 = ax4.plot(df_soil_moisture_avg_probabilistic_02.index, df_soil_moisture_avg_probabilistic_02.values[:, 0],
                   color='#8C468A', linestyle='--', lw=2)

    ax4.set_ylabel(label_soil_moisture, color='#000000')
    ax4.set_ylim(value_min_soil_moisture, value_max_soil_moisture)

    ax4.set_xticks(tick_time_idx)
    ax4.set_xticklabels(tick_time_labels, rotation=90, fontsize=8)

    legend1 = ax2.legend((p21[0], p22[0], p23[0], p24[0], p41[0], p42[0]),
                         (tag_discharge_obs_name,
                          tag_discharge_sim_name_ground_network,
                          tag_discharge_sim_name_nwp_01, tag_discharge_sim_name_nwp_02,
                          tag_soil_moisture_name_nwp_01, tag_soil_moisture_name_nwp_02),
                         frameon=False, ncol=2, loc=0)
    legend2 = ax2.legend((p25, p26, p210, p211, p218, p219),
                         ('< 25% -- 75% > m1', '< 25% -- 75% > m2', '25% -- 75% m1', '25% -- 75% m2',
                          tag_discharge_thr_alert, tag_discharge_thr_alarm),
                         frameon=False, ncol=4, loc=9, bbox_to_anchor=(0.5, -0.2))

    ax2.add_artist(legend1)
    ax2.add_artist(legend2)

    file_path, file_folder = os.path.split(file_name)

    if not os.path.exists(file_path):
        make_folder(file_path)
    fig.savefig(file_name, dpi=fig_dpi)

    # plt.show()
    plt.close()

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to plot discharge time-series for nwp probabilistic mode
def plot_ts_discharge_nwp_probabilistic(
        file_name,
        file_attributes_ground_network,
        file_attributes_nwp_deterministic, file_attributes_nwp_probabilistic,
        df_rain_ground_network,
        df_rain_nwp_deterministic, df_rain_nwp_probabilistic,
        df_discharge_simulated_ground_network,
        df_discharge_simulated_nwp_deterministic, df_discharge_simulated_nwp_probabilistic,
        df_soil_moisture_ground_network,
        df_soil_moisture_nwp_deterministic, df_soil_moisture_nwp_probabilistic,
        df_discharge_observed=None,
        value_min_discharge=0, value_max_discharge=100,
        value_min_rain_avg=0, value_max_rain_avg=20,
        value_min_rain_accumulated=0, value_max_rain_accumulated=100,
        value_min_soil_moisture=0, value_max_soil_moisture=1,
        tag_time_name='time', tag_time_units='[hour]',
        tag_discharge_generic_name='Discharge',
        tag_discharge_sim_name_ground_network='Discharge Simulated Ground Network',
        tag_discharge_sim_name_nwp='Discharge Simulated NWP',
        tag_discharge_obs_name='Discharge Observed', tag_discharge_units='[m^3/s]',
        tag_rain_avg_name='Rain Avg', tag_rain_accumulated_name='Rain Accumulated', tag_rain_units='[mm]',
        tag_soil_moisture_name='Soil Moisture Avg', tag_soil_moisture_units='[-]',
        tag_discharge_thr_alarm='discharge thr alarm', tag_discharge_thr_alert='discharge thr alert',
        tag_sep=' ', fig_dpi=120):

    # Configure ts attributes
    attrs_ts_ground_network = configure_ts_attrs(file_attributes_ground_network)
    attrs_ts_nwp_det = configure_ts_attrs(file_attributes_nwp_deterministic)
    attrs_ts_nwp_prob = configure_ts_attrs(file_attributes_nwp_probabilistic)

    # Configure ts time axes
    [tick_time_period, tick_time_idx, tick_time_labels] = configure_ts_axes(df_soil_moisture_nwp_probabilistic)

    # Axis labels
    label_time = tag_sep.join([tag_time_name, tag_time_units])
    label_discharge_generic = tag_sep.join([tag_discharge_generic_name, tag_discharge_units])
    label_discharge_sim_ground_network = tag_sep.join([tag_discharge_sim_name_ground_network, tag_discharge_units])
    label_discharge_sim_nwp = tag_sep.join([tag_discharge_sim_name_nwp, tag_discharge_units])
    label_discharge_obs = tag_sep.join([tag_discharge_obs_name, tag_discharge_units])
    label_rain_avg = tag_sep.join([tag_rain_avg_name, tag_rain_units])
    label_rain_accumulated = tag_sep.join([tag_rain_accumulated_name, tag_rain_units])
    label_soil_moisture = tag_sep.join([tag_soil_moisture_name, tag_soil_moisture_units])

    time_run_ground_network = attrs_ts_ground_network['time_run'].strftime(format=time_format_algorithm)
    time_run_nwp_det = attrs_ts_nwp_det['time_run'].strftime(format=time_format_algorithm)
    time_run_nwp_prob = attrs_ts_nwp_prob['time_run'].strftime(format=time_format_algorithm)
    time_restart = attrs_ts_ground_network['time_restart'].strftime(format=time_format_algorithm)
    time_start = attrs_ts_ground_network['time_start'].strftime(format=time_format_algorithm)

    section_drained_area = str(attrs_ts_nwp_prob['section_drained_area'])

    # Compute nwp probabilistic peak(s)
    df_discharge_simulated_peaks_probabilistic = compute_ts_peaks(
        df_discharge_simulated_nwp_probabilistic, peak_value_min=0, peak_timestr_min=time_run_ground_network)

    # Compute nwp probabilistic discharge quantile(s)
    df_discharge_simulated_nwp_probabilistic = compute_ts_quantile(
        df_discharge_simulated_nwp_probabilistic,
        variable_qtls_name='qtls', variable_qtls_list=[0, 0.25, 0.5, 0.75, 1], variable_qtls_axis=1)
    # Compute nwp probabilistic rain quantile(s)
    df_rain_nwp_probabilistic = compute_ts_quantile(
        df_rain_nwp_probabilistic,
        variable_qtls_name='qtls', variable_qtls_list=[0, 0.25, 0.5, 0.75, 1], variable_qtls_axis=1)
    # Compute nwp probabilistic soil moisture average
    df_soil_moisture_avg_probabilistic = compute_ts_ensemble_avg(df_soil_moisture_nwp_probabilistic, variable_axis=1)

    if df_discharge_observed is None:
        df_values = deepcopy(df_discharge_simulated_ground_network.values)
        df_index = deepcopy(df_discharge_simulated_ground_network.index)
        df_values[:, 0] = -9996.0
        df_discharge_observed = pd.DataFrame(data=df_values, index=df_index)

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

    p11 = ax1.bar(df_rain_ground_network.index, df_rain_ground_network.values[:, 0],
                  color='#337ec9', alpha=1, width=0.025, align='edge')
    p12 = ax1.bar(df_rain_nwp_deterministic.index, df_rain_nwp_deterministic.values[:, 0],
                  color='#33A1C9', alpha=1, width=0.025, align='edge')
    p13 = ax1.axvline(attrs_ts_ground_network['time_run'], color='#000000', linestyle='--', lw=2)
    p14 = ax1.axvline(attrs_ts_nwp_prob['time_run'], color='#808080', linestyle='--', lw=2)

    ax3 = ax1.twinx()
    ax3.set_ylabel(label_rain_accumulated, color='#000000')
    ax3.set_ylim(value_min_rain_accumulated, value_max_rain_accumulated)

    ax3.set_xticks(tick_time_idx)
    ax3.set_xticklabels([])
    ax3.set_xlim(tick_time_period[0], tick_time_period[-1])

    p31 = ax3.plot(df_rain_nwp_deterministic.index, df_rain_nwp_deterministic.cumsum().values[:, 0],
                   color='#33A1C9', linestyle='-', lw=1)

    # legend = ax1.legend(p11, [oRain_OBS_META['var_appearance']], frameon=False, loc=2)

    legend = ax1.legend((p11[0], p31[0]),
                        (tag_rain_avg_name, tag_rain_accumulated_name,),
                        frameon=False, loc=2)

    ax1.add_artist(legend)

    ax1.set_title('Time Series \n Section: ' + attrs_ts_nwp_prob['section_name'] +
                  ' == Basin: ' + attrs_ts_nwp_prob['section_domain'] +
                  ' == Area [Km^2]: ' + section_drained_area + ' \n  TypeRun: ' + attrs_ts_nwp_prob['run_name'] +
                  ' == Time_Run_OBS: ' + time_run_ground_network + ' Time_Run_NWP: ' + time_run_nwp_prob + '\n' +
                  ' == Time_Restart: ' + time_restart +
                  ' == Time_Start: ' + time_start)

    # Subplot 2 [DISCHARGE]
    ax2 = plt.subplot(3, 1, (2, 3))
    p21 = ax2.plot(df_discharge_observed.index, df_discharge_observed.values[:, 0],
                   color='#000000', linestyle='--', lw=1, marker='o', ms=4)
    p22 = ax2.plot(df_discharge_simulated_ground_network.index, df_discharge_simulated_ground_network.values[:, 0],
                   color='#0000FF', linestyle='-', lw=1)
    p23 = ax2.plot(df_discharge_simulated_nwp_deterministic.index, df_discharge_simulated_nwp_deterministic.values[:, 0],
                   color='#0066ff', linestyle='-', lw=1)

    ax2.set_xlabel(label_time, color='#000000')
    ax2.set_xlim(tick_time_period[0], tick_time_period[-1])
    ax2.set_ylabel(label_discharge_generic, color='#000000')
    ax2.set_ylim(value_min_discharge, value_max_discharge)
    ax2.grid(b=True)

    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic.index,
        df_discharge_simulated_nwp_probabilistic['qtls0.0'].values,
        df_discharge_simulated_nwp_probabilistic['qtls0.25'].values,
        where=df_discharge_simulated_nwp_probabilistic['qtls0.25'] > df_discharge_simulated_nwp_probabilistic['qtls0.0'],
        facecolor='#D3D3D3', alpha=10, interpolate=False)
    p24 = Rectangle((0, 0), 1, 1, fc='#D3D3D3')

    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic.index,
        df_discharge_simulated_nwp_probabilistic['qtls0.25'].values,
        df_discharge_simulated_nwp_probabilistic['qtls0.75'].values,
        where=df_discharge_simulated_nwp_probabilistic['qtls0.75'] >= df_discharge_simulated_nwp_probabilistic['qtls0.25'],
        facecolor='#A9A9A9', alpha=10, interpolate=False)
    p25 = Rectangle((0, 0), 1, 1, fc='#A9A9A9')

    ax2.fill_between(
        df_discharge_simulated_nwp_probabilistic.index,
        df_discharge_simulated_nwp_probabilistic['qtls0.75'].values, df_discharge_simulated_nwp_probabilistic['qtls1.0'].values,
        where=df_discharge_simulated_nwp_probabilistic['qtls1.0'] >= df_discharge_simulated_nwp_probabilistic['qtls0.75'],
        facecolor='#D3D3D3', alpha=10, interpolate=False)
    p26 = Rectangle((0, 0), 1, 1, fc='#D3D3D3')

    p27 = ax2.plot(pd.DatetimeIndex(
        df_discharge_simulated_peaks_probabilistic.time),
        df_discharge_simulated_peaks_probabilistic.peak,
        color='#0000FF', linestyle='-', lw=0, marker='*', ms=4)
    p28 = Rectangle((0, 0), 1, 1, fc='#0000FF')

    p29 = ax2.axvline(attrs_ts_ground_network['time_run'], color='#000000', linestyle='--', lw=2, label='time run obs')
    p210 = ax2.axvline(attrs_ts_nwp_prob['time_run'], color='#808080', linestyle='--', lw=2, label='time run nwp')

    p211 = ax2.axhline(attrs_ts_ground_network['section_discharge_thr_alert'], color='#FFA500', linestyle='--',
                       linewidth=2, label=tag_discharge_thr_alert)
    p212 = ax2.axhline(attrs_ts_ground_network['section_discharge_thr_alarm'], color='#FF0000', linestyle='--',
                       linewidth=2, label=tag_discharge_thr_alarm)

    ax2.set_xticks(tick_time_idx)
    ax2.set_xticklabels(tick_time_labels, rotation=90, fontsize=8)

    ax4 = ax2.twinx()
    p41 = ax4.plot(df_soil_moisture_avg_probabilistic.index, df_soil_moisture_avg_probabilistic.values[:, 0],
                   color='#DA70D6', linestyle='--', lw=2)

    ax4.set_ylabel(label_soil_moisture, color='#000000')
    ax4.set_ylim(value_min_soil_moisture, value_max_soil_moisture)

    ax4.set_xticks(tick_time_idx)
    ax4.set_xticklabels(tick_time_labels, rotation=90, fontsize=8)

    legend1 = ax2.legend((p21[0], p22[0], p23[0], p41[0]),
                         (tag_discharge_obs_name,
                          tag_discharge_sim_name_ground_network, tag_discharge_sim_name_nwp,
                          tag_soil_moisture_name),
                         frameon=False, ncol=2, loc=0)
    legend2 = ax2.legend((p24, p25, p211, p212),
                         ('< 25% -- 75% >', '25% -- 75%', tag_discharge_thr_alert, tag_discharge_thr_alarm),
                         frameon=False, ncol=4, loc=9, bbox_to_anchor=(0.5, -0.2))

    ax2.add_artist(legend1)
    ax2.add_artist(legend2)

    file_path, file_folder = os.path.split(file_name)

    if not os.path.exists(file_path):
        make_folder(file_path)
    fig.savefig(file_name, dpi=fig_dpi)

    # plt.show()
    plt.close()

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to plot discharge time-series for nwp deterministic mode
def plot_ts_discharge_nwp_deterministic(
        file_name,
        file_attributes_ground_network, file_attributes_nwp,
        df_rain_ground_network, df_rain_nwp,
        df_discharge_simulated_ground_network, df_discharge_simulated_nwp,
        df_soil_moisture_ground_network, df_soil_moisture_nwp,
        df_discharge_observed=None,
        value_min_discharge=0, value_max_discharge=100,
        value_min_rain_avg=0, value_max_rain_avg=20,
        value_min_rain_accumulated=0, value_max_rain_accumulated=100,
        value_min_soil_moisture=0, value_max_soil_moisture=1,
        tag_time_name='time', tag_time_units='[hour]',
        tag_discharge_generic_name='Discharge',
        tag_discharge_sim_name='Discharge Simulated',
        tag_discharge_obs_name='Discharge Observed', tag_discharge_units='[m^3/s]',
        tag_rain_avg_name='Rain Avg', tag_rain_accumulated_name='Rain Accumulated', tag_rain_units='[mm]',
        tag_soil_moisture_name='Soil Moisture', tag_soil_moisture_units='[-]',
        tag_discharge_thr_alarm='discharge thr alarm', tag_discharge_thr_alert='discharge thr alert',
        tag_sep=' ', fig_dpi=120):

    # Configure ts attributes
    attrs_ts_ground_network = configure_ts_attrs(file_attributes_ground_network)
    attrs_ts_nwp = configure_ts_attrs(file_attributes_nwp)

    # Configure ts time axes
    [tick_time_period, tick_time_idx, tick_time_labels] = configure_ts_axes(df_soil_moisture_nwp)

    # Axis labels
    label_time = tag_sep.join([tag_time_name, tag_time_units])
    label_discharge_generic = tag_sep.join([tag_discharge_generic_name, tag_discharge_units])
    label_discharge_sim = tag_sep.join([tag_discharge_sim_name, tag_discharge_units])
    label_discharge_obs = tag_sep.join([tag_discharge_obs_name, tag_discharge_units])
    label_rain_avg = tag_sep.join([tag_rain_avg_name, tag_rain_units])
    label_rain_accumulated = tag_sep.join([tag_rain_accumulated_name, tag_rain_units])
    label_soil_moisture = tag_sep.join([tag_soil_moisture_name, tag_soil_moisture_units])

    time_run_ground_network = attrs_ts_ground_network['time_run'].strftime(format=time_format_algorithm)
    time_run_nwp = attrs_ts_nwp['time_run'].strftime(format=time_format_algorithm)
    time_restart = attrs_ts_ground_network['time_restart'].strftime(format=time_format_algorithm)
    time_start = attrs_ts_ground_network['time_start'].strftime(format=time_format_algorithm)

    section_drained_area = str(attrs_ts_ground_network['section_drained_area'])
    section_name = attrs_ts_ground_network['section_name']
    section_domain = attrs_ts_ground_network['section_domain']

    if df_discharge_observed is None:
        df_values = deepcopy(df_discharge_simulated_ground_network.values)
        df_index = deepcopy(df_discharge_simulated_ground_network.index)
        df_values[:, 0] = -9996.0
        df_discharge_observed = pd.DataFrame(data=df_values, index=df_index)

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

    p11 = ax1.bar(df_rain_nwp.index, df_rain_nwp.values[:, 0],
                  color='#33A1C9', alpha=1, width=0.025, align='edge')

    p13 = ax1.axvline(attrs_ts_ground_network['time_run'], color='#000000', linestyle='--', lw=2)
    p14 = ax1.axvline(attrs_ts_nwp['time_run'], color='#808080', linestyle='--', lw=2)

    ax3 = ax1.twinx()
    ax3.set_ylabel(label_rain_accumulated, color='#000000')
    ax3.set_ylim(value_min_rain_accumulated, value_max_rain_accumulated)

    ax3.set_xticks(tick_time_idx)
    ax3.set_xticklabels([])
    ax3.set_xlim(tick_time_period[0], tick_time_period[-1])

    p31 = ax3.plot(df_rain_nwp.index, df_rain_nwp.cumsum().values[:, 0],
                   color='#33A1C9', linestyle='-', lw=1)

    legend = ax1.legend((p11[0], p31[0]),
                        (tag_rain_avg_name, tag_rain_accumulated_name,),
                        frameon=False, loc=2)

    ax1.add_artist(legend)

    ax1.set_title('Time Series \n Section: ' + section_name +
                  ' == Basin: ' + section_domain +
                  ' == Area [Km^2]: ' + section_drained_area + ' \n  TypeRun: ' + attrs_ts_nwp['run_name'] +
                  ' == Time_Run_OBS: ' + time_run_ground_network + ' Time_Run_NWP: ' + time_run_nwp + '\n' +
                  ' == Time_Restart: ' + time_restart +
                  ' == Time_Start: ' + time_start)

    # Subplot 2 [DISCHARGE]
    ax2 = plt.subplot(3, 1, (2, 3))
    p21 = ax2.plot(df_discharge_observed.index, df_discharge_observed.values[:, 0],
                   color='#000000', linestyle='--', lw=1, marker='o', ms=4)
    p22 = ax2.plot(df_discharge_simulated_nwp.index, df_discharge_simulated_nwp.values[:, 0],
                   color='#0000FF', linestyle='-', lw=1)

    ax2.set_xlabel(label_time, color='#000000')
    ax2.set_xlim(tick_time_period[0], tick_time_period[-1])
    ax2.set_ylabel(label_discharge_generic, color='#000000')
    ax2.set_ylim(value_min_discharge, value_max_discharge)
    ax2.grid(b=True)

    p27 = ax2.axvline(attrs_ts_ground_network['time_run'], color='#000000', linestyle='--', lw=2, label='time run obs')
    p28 = ax2.axvline(attrs_ts_nwp['time_run'], color='#808080', linestyle='--', lw=2, label='time run nwp')

    p29 = ax2.axhline(attrs_ts_ground_network['section_discharge_thr_alert'], color='#FFA500', linestyle='--',
                      linewidth=2, label=tag_discharge_thr_alert)
    p210 = ax2.axhline(attrs_ts_ground_network['section_discharge_thr_alarm'], color='#FF0000', linestyle='--',
                       linewidth=2, label=tag_discharge_thr_alarm)

    ax2.set_xticks(tick_time_idx)
    ax2.set_xticklabels(tick_time_labels, rotation=90, fontsize=8)

    ax4 = ax2.twinx()
    p41 = ax4.plot(df_soil_moisture_nwp.index, df_soil_moisture_nwp.values[:, 0],
                   color='#DA70D6', linestyle='--', lw=2)

    ax4.set_ylabel(label_soil_moisture, color='#000000')
    ax4.set_ylim(value_min_soil_moisture, value_max_soil_moisture)

    ax4.set_xticks(tick_time_idx)
    ax4.set_xticklabels(tick_time_labels, rotation=90, fontsize=8)

    legend1 = ax2.legend((p21[0], p22[0], p41[0]),
                         (tag_discharge_obs_name, tag_discharge_sim_name, tag_soil_moisture_name),
                         frameon=False, ncol=2, loc=0)
    legend2 = ax2.legend((p29, p210),
                         (tag_discharge_thr_alert, tag_discharge_thr_alarm),
                         frameon=False, ncol=4, loc=9, bbox_to_anchor=(0.5, -0.2))

    ax2.add_artist(legend1)
    ax2.add_artist(legend2)

    file_path, file_folder = os.path.split(file_name)

    if not os.path.exists(file_path):
        make_folder(file_path)
    fig.savefig(file_name, dpi=fig_dpi)

    # plt.show()
    plt.close()

# -------------------------------------------------------------------------------------
