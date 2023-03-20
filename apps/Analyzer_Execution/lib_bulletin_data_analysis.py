"""
Library Features:

Name:          lib_bulletin_data_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201202'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import numpy as np
import pandas as pd

from lib_bulletin_data_utils import shrink_bulletin_attrs
from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to get bulletin field
def get_bulletin_field(field_name, field_info, field_value_null='NA', field_time_format='%Y-%m-%d %H:%M'):

    if field_name in list(field_info.keys()):
        field_value = field_info[field_name]
        if field_value is not None:
            if isinstance(field_value, pd.Timestamp):
                field_value = field_value.strftime(field_time_format)
            else:
                field_value = str(field_value)
        else:
            log_stream.warning(' ===> The variable "field_value" is defined by NoneType')
            field_value = field_value_null
    else:
        log_stream.warning(' ===> The variable "field_name" is not available in the "field_info" object')
        field_value = field_value_null

    if isinstance(field_value, list):
        if field_value.__len__() == 1:
            field_value = field_value[0]
        else:
            log_stream.error(' ===> The variable "field_value" should be in list format with length equal to 1')
            raise NotImplemented('Case not implemented yet')

    return field_value
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to create bulletin obj
def create_bulletin_obj(run_name_list, run_description_list, run_time_list,
                        thr_data_list, thr_time_list, thr_run_list, thr_type_list, thr_code_list,
                        thr_value_alert_list, thr_value_alarm_list, thr_section_list,
                        section_longitude_list, section_latitude_list, section_tag_list,
                        section_name_list, section_code_list, section_catchment_list,
                        section_description_list, domain_description_list):

    # define bulletin obj
    bulletin_obj = {
        'run_name': run_name_list, 'run_description': run_description_list,
        'run_time': run_time_list,

        'thr_type': thr_type_list, 'thr_code': thr_code_list,
        'thr_value_alert': thr_value_alert_list, 'thr_value_alarm': thr_value_alarm_list,
        'thr_value_data': thr_data_list, 'thr_time': thr_time_list, 'thr_run': thr_run_list,
        'thr_section': thr_section_list,

        'section_longitude': section_longitude_list, 'section_latitude': section_latitude_list,
        'section_tag': section_tag_list, 'section_name': section_name_list,
        'section_code': section_code_list, 'section_catchment': section_catchment_list,
        'section_description': domain_description_list, 'domain_description': section_description_list}

    # define summary dframe
    bulletin_dframe = pd.DataFrame(bulletin_obj)

    return bulletin_dframe
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to organize bulletin obj
def organize_bulletin_obj(section_dframe_generic, sep_root=';', sep_sub='::'):

    # check generic dataframe
    if not section_dframe_generic.empty:

        # select max threshold code
        section_dframe_finite = section_dframe_generic.dropna()
        if not section_dframe_finite.empty:

            thr_code_max = np.max(section_dframe_finite['thr_code'])

            section_dframe_max = section_dframe_finite.loc[
                section_dframe_finite['thr_code'] == thr_code_max]

            # organize fields with duplicates (for example the same maximum value)
            time_root_list, run_root_list = [], []
            for thr_time, thr_run in zip(section_dframe_max['thr_time'], section_dframe_max['thr_run']):
                time_sub_list, run_sub_list = [], []
                for time_sub, run_sub in zip(thr_time, thr_run):
                    time_str = time_sub.strftime('%Y-%m-%d %H:%M')
                    time_sub_list.append(time_str)
                    run_sub_list.append(run_sub)
                time_sub_str = sep_sub.join(time_sub_list)
                run_sub_str = sep_sub.join(run_sub_list)
                time_root_list.append(time_sub_str)
                run_root_list.append(run_sub_str)

            # multi-fields
            run_name_list = sep_root.join(list(section_dframe_max['run_name'].values))
            run_description_list = sep_root.join(list(section_dframe_max['run_description'].values))
            run_time_list = sep_root.join(list(section_dframe_max['run_time'].dt.strftime('%Y-%m-%d %H:%M')))
            thr_data_list = sep_root.join(list(section_dframe_max['thr_value_data'].astype(str)))
            thr_time_list = sep_root.join(time_root_list)
            thr_run_list = sep_root.join(run_root_list)
            thr_type = section_dframe_max['thr_type'].values[0]
            thr_code = section_dframe_max['thr_code'].values[0]
        else:
            run_name_list, run_description_list, run_time_list = 'NA', 'NA', 'NA'
            thr_data_list, thr_time_list, thr_run_list = 'NA', 'NA', 'NA'
            thr_type = section_dframe_generic['thr_type'].values[0]
            thr_code = section_dframe_generic['thr_code'].values[0]

        # single-field
        thr_value_alert = section_dframe_generic['thr_value_alert'].values[0]
        thr_value_alarm = section_dframe_generic['thr_value_alarm'].values[0]
        thr_section = section_dframe_generic['thr_section'].values[0]
        section_longitude = section_dframe_generic['section_longitude'].values[0]
        section_latitude = section_dframe_generic['section_latitude'].values[0]
        section_tag = section_dframe_generic['section_tag'].values[0]
        section_name = section_dframe_generic['section_name'].values[0]
        section_code = section_dframe_generic['section_code'].values[0]
        section_catchment = section_dframe_generic['section_catchment'].values[0]
        section_description = section_dframe_generic['section_description'].values[0]
        domain_description = section_dframe_generic['domain_description'].values[0]

    else:

        run_name_list, run_description_list, run_time_list = [], [], []
        thr_data_list, thr_time_list, thr_run_list, thr_type, thr_code = [], [], [], [], []
        thr_value_alert, thr_value_alarm, thr_section = np.nan, np.nan, np.nan
        section_longitude, section_latitude = np.nan, np.nan
        section_tag, section_name, section_code, section_catchment = '', '', '', ''
        section_description, domain_description = '', ''

        log_stream.warning(' ===> The threshold DataFrame is empty. All the datasets are not defined.')

    return run_name_list, run_description_list, run_time_list, thr_data_list, thr_time_list, thr_run_list, \
        thr_type, thr_code, \
        thr_value_alert, thr_value_alarm, thr_section, \
        section_longitude, section_latitude, section_tag, section_name, section_code, section_catchment, \
        section_description, domain_description
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to select bulletin obj
def select_bulletin_time(time_run, bulletin_dframe_generic, time_mode='today'):

    # --------------------------------------------------------------------------------------------------------------
    # compute dataframe according to time period
    if time_mode == 'today':
        time_stamp_base = time_run.round('D')
        time_stamp_from = time_stamp_base.replace(hour=0, minute=0, second=0)
        time_stamp_to = time_stamp_base.replace(hour=23, minute=59, second=59)
    elif time_mode == 'tomorrow':
        time_stamp_base = time_run.round('D') + pd.Timedelta(days=1)
        time_stamp_base = time_stamp_base.round('D')
        time_stamp_from = time_stamp_base.replace(hour=0, minute=0, second=0)
        time_stamp_to = time_stamp_base.replace(hour=23, minute=59, second=59)
    else:
        log_stream.error(' ===> The "time_mode" tag "' + time_mode + '" is not supported')
        raise NotImplementedError('Case not implemented yet')
    # --------------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------------
    # select dataframe according to the time period(s)
    if not bulletin_dframe_generic.empty:
        bulletin_dframe_select = bulletin_dframe_generic.loc[
            (bulletin_dframe_generic['run_time'] >= time_stamp_from) &
            (bulletin_dframe_generic['run_time'] <= time_stamp_to)]
    else:
        bulletin_dframe_select = pd.DataFrame()

    return bulletin_dframe_select
# --------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to organize bulletin thr using the thr max
def organize_bulletin_warnings_section(bulletin_dframe_generic, sections_dframe):

    # info start
    log_stream.info(' ------> Organize bulletin warnings sections ... ')

    # initialize variable(s)
    run_name_summary, run_description_summary, run_time_summary = [], [], []
    thr_data_summary, thr_time_summary, thr_run_summary = [], [], []
    thr_type_summary, thr_code_summary = [], []
    thr_value_alert_summary, thr_value_alarm_summary, thr_section_summary = [], [], []
    section_longitude_summary, section_latitude_summary = [], []
    section_tag_summary, section_name_summary, section_catchment_summary, section_code_summary = [], [], [], []
    section_description_summary, domain_description_summary = [], []

    # iterate over sections
    for id_row, section_row in sections_dframe.iterrows():

        # get section tag
        section_reference = section_row['section_tag']
        log_stream.info(' -------> Section "' + section_reference.lower() + ' ... ')

        # extract section dataframe
        section_dframe_generic = bulletin_dframe_generic.loc[
            bulletin_dframe_generic['section_tag'].str.lower() == section_reference.lower()]

        # organize section field
        run_name_list, run_description_list, run_time_list, thr_data_list, thr_time_list, thr_run_list, \
            thr_type, thr_code, \
            thr_value_alert, thr_value_alarm, thr_section, \
            section_longitude, section_latitude, section_tag, section_name, section_code, section_catchment, \
            section_description, domain_description = organize_bulletin_obj(section_dframe_generic)

        # concatenate data
        run_name_summary.append(run_name_list)
        run_description_summary.append(run_description_list)
        run_time_summary.append(run_time_list)
        thr_data_summary.append(thr_data_list)
        thr_time_summary.append(thr_time_list)
        thr_run_summary.append(thr_run_list)
        thr_type_summary.append(thr_type)
        thr_code_summary.append(thr_code)
        thr_value_alert_summary.append(thr_value_alert)
        thr_value_alarm_summary.append(thr_value_alarm)
        thr_section_summary.append(thr_section)
        section_longitude_summary.append(section_longitude)
        section_latitude_summary.append(section_latitude)
        section_tag_summary.append(section_tag)
        section_name_summary.append(section_name)
        section_code_summary.append(section_code)
        section_catchment_summary.append(section_catchment)
        section_description_summary.append(section_description)
        domain_description_summary.append(domain_description)

        log_stream.info(' -------> Section "' + section_reference.lower() + ' ... DONE')

    # create bulletin obj
    bulletin_dframe_maximum = create_bulletin_obj(
        run_name_summary, run_description_summary, run_time_summary,
        thr_data_summary, thr_time_summary, thr_run_summary, thr_type_summary, thr_code_summary,
        thr_value_alert_summary, thr_value_alarm_summary, thr_section_summary,
        section_longitude_summary, section_latitude_summary, section_tag_summary,
        section_name_summary, section_code_summary, section_catchment_summary,
        section_description_summary, domain_description_summary)

    # info end
    log_stream.info(' ------> Organize bulletin warnings sections ... DONE')

    return bulletin_dframe_maximum
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to organize bulletin threshold(s) generic
def organize_bulletin_warnings_generic(run_name_list, run_summary, section_collections, tag_summary_data='data'):

    # info start
    log_stream.info(' ------> Organize bulletin warnings generic ... ')

    # initialize variable(s)
    pnt_run_name_list, pnt_run_description_list = [], []
    pnt_run_id_list, pnt_run_time_list = [], []
    pnt_thr_type_list, pnt_thr_code_list = [], []
    pnt_thr_value_default_list, pnt_thr_alert_list, pnt_thr_alarm_list = [], [], []
    pnt_thr_value_data_list, pnt_thr_value_time_list, pnt_thr_value_run_list = [], [], []
    pnt_thr_section_list, pnt_description_list = [], []
    pnt_longitude_list, pnt_latitude_list = [], []
    pnt_section_code_list, pnt_section_name_list, pnt_section_catchment_list = [], [], []
    pnt_section_description_list, pnt_domain_description_list, pnt_section_tag_list = [], [], []

    # iterate over run name
    for run_id, run_name_step in enumerate(run_name_list):

        # info run start
        log_stream.info(' -------> Run "' + run_name_step + '" ... ')
        # get run data
        run_data = run_summary[run_name_step][tag_summary_data]
        # check data availability
        if run_data is not None:

            # iterate over time(s)
            for id_step, (time_step, data_step) in enumerate(run_data.items()):

                alert_value_list = data_step['alert_value']
                alert_time_list = data_step['alert_index']
                alert_run_list = data_step['alert_run']
                # alert_thr_list = data_step['alert_thr']
                alert_section_list = data_step['alert_section']
                alarm_value_list = data_step['alarm_value']
                alarm_time_list = data_step['alarm_index']
                alarm_run_list = data_step['alarm_run']
                # alarm_thr_list = data_step['alarm_thr']
                alarm_section_list = data_step['alarm_section']
                run_name_list = data_step['run_name']
                run_description_list = data_step['run_description']

                # iterate over alert section
                for pnt_id_step, pnt_name_step in enumerate(alert_section_list):

                    pnt_info_step = section_collections.loc[
                        section_collections['section_tag'].str.lower() == pnt_name_step.lower()]

                    pnt_longitude_step = pnt_info_step['longitude'].values[0]
                    pnt_latitude_step = pnt_info_step['latitude'].values[0]
                    pnt_thr_alert_step = pnt_info_step['section_discharge_thr_alert'].values[0]
                    pnt_thr_alarm_step = pnt_info_step['section_discharge_thr_alarm'].values[0]
                    pnt_section_tag_step = pnt_info_step['section_tag'].values[0]
                    pnt_section_code_step = pnt_info_step['section_code'].values[0]
                    pnt_section_name_step = pnt_info_step['section_name'].values[0]
                    pnt_section_catchment_step = pnt_info_step['section_catchment'].values[0]
                    pnt_section_description_step = pnt_info_step['section_description'].values[0]
                    pnt_domain_description_step = pnt_info_step['domain_description'].values[0]

                    pnt_run_name_list.append(run_name_list[pnt_id_step])
                    pnt_run_description_list.append(run_description_list[pnt_id_step])
                    pnt_run_id_list.append(id_step)
                    pnt_run_time_list.append(time_step)

                    pnt_longitude_list.append(pnt_longitude_step)
                    pnt_latitude_list.append(pnt_latitude_step)
                    pnt_thr_alert_list.append(pnt_thr_alert_step)
                    pnt_thr_alarm_list.append(pnt_thr_alarm_step)
                    pnt_section_tag_list.append(pnt_section_tag_step)
                    pnt_section_code_list.append(pnt_section_code_step)
                    pnt_section_name_list.append(pnt_section_name_step)
                    pnt_section_catchment_list.append(pnt_section_catchment_step)
                    pnt_section_description_list.append(pnt_section_description_step)
                    pnt_domain_description_list.append(pnt_domain_description_step)

                    check_value = alert_value_list[pnt_id_step]
                    if check_value is not None:
                        if np.isfinite(check_value):
                            pnt_thr_value_data_list.append(alert_value_list[pnt_id_step])
                            pnt_thr_value_time_list.append(alert_time_list[pnt_id_step])
                            pnt_thr_value_run_list.append(alert_run_list[pnt_id_step])
                            pnt_thr_section_list.append(alert_section_list[pnt_id_step])
                            pnt_thr_type_list.append('alert')
                            pnt_thr_code_list.append(1)
                        else:
                            pnt_thr_value_data_list.append(alert_value_list[pnt_id_step])
                            pnt_thr_value_time_list.append(alert_time_list[pnt_id_step])
                            pnt_thr_value_run_list.append(alert_run_list[pnt_id_step])
                            pnt_thr_section_list.append(alert_section_list[pnt_id_step])
                            pnt_thr_type_list.append(None)
                            pnt_thr_code_list.append(0)
                    else:
                        pnt_thr_value_data_list.append(alert_value_list[pnt_id_step])
                        pnt_thr_value_time_list.append(alert_time_list[pnt_id_step])
                        pnt_thr_value_run_list.append(alert_run_list[pnt_id_step])
                        pnt_thr_section_list.append(alert_section_list[pnt_id_step])
                        pnt_thr_type_list.append(None)
                        pnt_thr_code_list.append(0)

                # iterate over alarm section
                for pnt_id_step, pnt_name_step in enumerate(alarm_section_list):

                    pnt_info_step = section_collections.loc[
                        section_collections['section_tag'].str.lower() == pnt_name_step.lower()]

                    pnt_longitude_step = pnt_info_step['longitude'].values[0]
                    pnt_latitude_step = pnt_info_step['latitude'].values[0]
                    pnt_thr_alert_step = pnt_info_step['section_discharge_thr_alert'].values[0]
                    pnt_thr_alarm_step = pnt_info_step['section_discharge_thr_alarm'].values[0]
                    pnt_section_tag_step = pnt_info_step['section_tag'].values[0]
                    pnt_section_code_step = pnt_info_step['section_code'].values[0]
                    pnt_section_name_step = pnt_info_step['section_name'].values[0]
                    pnt_section_catchment_step = pnt_info_step['section_catchment'].values[0]
                    pnt_section_description_step = pnt_info_step['section_description'].values[0]
                    pnt_domain_description_step = pnt_info_step['domain_description'].values[0]

                    pnt_run_name_list.append(run_name_list[pnt_id_step])
                    pnt_run_description_list.append(run_description_list[pnt_id_step])
                    pnt_run_id_list.append(id_step)
                    pnt_run_time_list.append(time_step)

                    pnt_longitude_list.append(pnt_longitude_step)
                    pnt_latitude_list.append(pnt_latitude_step)
                    pnt_thr_alert_list.append(pnt_thr_alert_step)
                    pnt_thr_alarm_list.append(pnt_thr_alarm_step)
                    pnt_section_tag_list.append(pnt_section_tag_step)
                    pnt_section_code_list.append(pnt_section_code_step)
                    pnt_section_name_list.append(pnt_section_name_step)
                    pnt_section_catchment_list.append(pnt_section_catchment_step)
                    pnt_section_description_list.append(pnt_section_description_step)
                    pnt_domain_description_list.append(pnt_domain_description_step)

                    check_value = alarm_value_list[pnt_id_step]
                    if check_value is not None:
                        if np.isfinite(alarm_value_list[pnt_id_step]):
                            pnt_thr_value_data_list.append(alarm_value_list[pnt_id_step])
                            pnt_thr_value_time_list.append(alarm_time_list[pnt_id_step])
                            pnt_thr_value_run_list.append(alarm_run_list[pnt_id_step])
                            pnt_thr_section_list.append(alarm_section_list[pnt_id_step])
                            pnt_thr_type_list.append('alarm')
                            pnt_thr_code_list.append(2)
                        else:
                            pnt_thr_value_data_list.append(alarm_value_list[pnt_id_step])
                            pnt_thr_value_time_list.append(alarm_time_list[pnt_id_step])
                            pnt_thr_value_run_list.append(alarm_run_list[pnt_id_step])
                            pnt_thr_section_list.append(alarm_section_list[pnt_id_step])
                            pnt_thr_type_list.append(None)
                            pnt_thr_code_list.append(0)
                    else:
                        pnt_thr_value_data_list.append(alarm_value_list[pnt_id_step])
                        pnt_thr_value_time_list.append(alarm_time_list[pnt_id_step])
                        pnt_thr_value_run_list.append(alarm_run_list[pnt_id_step])
                        pnt_thr_section_list.append(alarm_section_list[pnt_id_step])
                        pnt_thr_type_list.append(None)
                        pnt_thr_code_list.append(0)

            # info run end
            log_stream.info(' -------> Run "' + run_name_step + '" ... DONE')
        else:
            # info run end
            log_stream.info(' -------> Run "' + run_name_step + '" ... SKIPPED. Datasets are not available')

    # define bulletin obj
    bulletin_dict = {
        'run_name': pnt_run_name_list, 'run_description': pnt_run_description_list,
        'run_id': pnt_run_id_list, 'run_time': pnt_run_time_list,

        'thr_type': pnt_thr_type_list, 'thr_code': pnt_thr_code_list,
        'thr_value_alert': pnt_thr_alert_list, 'thr_value_alarm': pnt_thr_alarm_list,
        'thr_value_data': pnt_thr_value_data_list, 'thr_time': pnt_thr_value_time_list,
        'thr_run': pnt_thr_value_run_list, 'thr_section': pnt_thr_section_list,

        'section_longitude': pnt_longitude_list, 'section_latitude': pnt_latitude_list,
        'section_tag': pnt_section_tag_list, 'section_name': pnt_section_name_list,
        'section_code': pnt_section_code_list, 'section_catchment': pnt_section_catchment_list,
        'section_description': pnt_section_description_list, 'domain_description': pnt_domain_description_list}

    # define summary dframe
    bulletin_dframe = pd.DataFrame(bulletin_dict)

    # info start
    log_stream.info(' ------> Organize bulletin warnings generic ... DONE')

    return bulletin_dframe

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to organize bulletin info
def organize_bulletin_info(run_name_list, run_summary,
                           tag_summary_data='data', tag_summary_info='info',
                           summary_no_data_run='NAT', summary_no_data_time='NAT',
                           summary_run_status_completed='COMPLETED', summary_run_code_completed=0,
                           summary_run_status_partial_completed='COMPLETED (partial ensembles)', summary_run_code_partial_completed=-1,
                           summary_run_status_running='RUNNING', summary_run_code_running=1,
                           summary_run_status_not_available='NOT AVAILABLE', summary_run_code_not_available=2,
                           summary_run_status_unknown='UNKNOWN', summary_run_code_unknown=-2,
                           summary_level_nothing_status='none', summary_level_nothing_code=0,
                           summary_level_alert_status='alert', summary_level_alert_code=1,
                           summary_level_alarm_status='alarm', summary_level_alarm_code=2):

    # info start
    log_stream.info(' -----> Organize bulletin info run ... ')

    # iterate over run name
    run_id_list, run_n_list, run_expected_list, run_description_list, run_type_list = [], [], [], [], []
    run_status_description_list, run_status_code_list = [], []
    time_start_list, time_end_list, time_elapsed_list = [], [], []
    section_n_list, domain_name_list = [], []
    for run_id_step, run_name_step in enumerate(run_name_list):

        # info start
        log_stream.info(' ------> Run "' + run_name_step + '" ... ')

        # get run info
        run_info_step = run_summary[run_name_step][tag_summary_info]

        # shrink bulletin attributes to unique element for each key
        run_info_step = shrink_bulletin_attrs(run_info_step)

        run_n_step = get_bulletin_field('run_n', run_info_step, field_value_null=summary_no_data_run)
        run_expected_step = get_bulletin_field('run_expected', run_info_step, field_value_null=summary_no_data_run)
        run_description_step = get_bulletin_field('run_description', run_info_step, field_value_null=summary_no_data_run)
        run_type_step = get_bulletin_field('run_type', run_info_step, field_value_null=summary_no_data_run)
        section_n_step = get_bulletin_field('section_n', run_info_step, field_value_null=summary_no_data_run)
        domain_name_step = get_bulletin_field('domain_name', run_info_step, field_value_null=summary_no_data_run)
        time_start_step = get_bulletin_field('run_start', run_info_step, field_value_null=summary_no_data_time)
        time_end_step = get_bulletin_field('run_end', run_info_step, field_value_null=summary_no_data_time)
        time_elapsed_step = get_bulletin_field('run_elapsed', run_info_step, field_value_null=summary_no_data_time)

        # check time
        if time_start_step != summary_no_data_time and time_end_step != summary_no_data_time:
            if int(run_n_step) == int(run_expected_step):
                run_status_description_step = summary_run_status_completed
                run_status_code_step = summary_run_code_completed
            else:
                run_status_description_step = summary_run_status_partial_completed
                run_status_code_step = summary_run_code_partial_completed
        elif time_start_step != summary_no_data_time and time_end_step == summary_no_data_time:
            run_status_description_step = summary_run_status_running
            run_status_code_step = summary_run_code_running
        elif time_start_step == summary_no_data_time and time_end_step == summary_no_data_time:
            run_status_description_step = summary_run_status_not_available
            run_status_code_step = summary_run_code_not_available
        else:
            run_status_description_step = summary_run_status_unknown
            run_status_code_step = summary_run_code_unknown

        run_id_list.append(run_id_step)
        run_n_list.append(run_n_step)
        run_expected_list.append(run_expected_step)
        run_description_list.append(run_description_step)
        run_status_description_list.append(run_status_description_step)
        run_status_code_list.append(run_status_code_step)
        run_type_list.append(run_type_step)
        section_n_list.append(section_n_step)
        domain_name_list.append(domain_name_step)
        time_start_list.append(time_start_step)
        time_end_list.append(time_end_step)
        time_elapsed_list.append(time_elapsed_step)

        # info start
        log_stream.info(' ------> Run "' + run_name_step + '" ... DONE')

    # define run info dframe
    run_info_dict = {
        'run_id': run_id_list, 'run_n': run_n_list, 'run_expected': run_expected_list,
        'run_description': run_description_list, 'run_type': run_type_list,
        'run_status_description': run_status_description_list, 'run_status_code': run_status_code_list,
        'time_start': time_start_list, 'time_end': time_end_list, 'time_elapsed': time_elapsed_list,
        'section': section_n_list, 'domain_name': domain_name_list}

    run_info_dframe = pd.DataFrame(run_info_dict)

    # info end
    log_stream.info(' -----> Organize bulletin info run ... DONE')

    # create link run description-type
    run_tag_map = dict(map(lambda i, j: (i, j), run_type_list, run_description_list))

    # info start
    log_stream.info(' -----> Organize bulletin info warning ... ')

    thr_run_name_ref, thr_run_tag_ref, thr_id_ref, thr_time_ref, thr_run_def, thr_default_ref = [], [], [], [], [], []
    thr_type_def, thr_code_def = [], []
    thr_value_def, thr_time_def, thr_section_def, thr_description_def = [], [], [], []
    # iterate over run name
    for run_id, run_name_step in enumerate(run_name_list):

        # info run start
        log_stream.info(' ------> Run "' + run_name_step + '" ... ')
        # get run data
        run_data = run_summary[run_name_step][tag_summary_data]

        if run_data is not None:

            for id_step, (time_step, data_step) in enumerate(run_data.items()):

                alert_value_raw = data_step['alert_value']
                alert_index_raw = data_step['alert_index']
                alert_run_raw = data_step['alert_run']
                alert_thr_raw = data_step['alert_thr']
                alert_section_raw = data_step['alert_section']
                alarm_value_raw = data_step['alarm_value']
                alarm_index_raw = data_step['alarm_index']
                alarm_run_raw = data_step['alarm_run']
                alarm_thr_raw = data_step['alarm_thr']
                alarm_section_raw = data_step['alarm_section']

                finite_idx = [i for i, n in enumerate(alert_value_raw) if n is not None and np.isfinite(n)]
                for idx in finite_idx:

                    thr_run_name_ref.append(run_name_step)

                    thr_run_tag = 'UNKNOWN'
                    if run_name_step in list(run_tag_map.keys()):
                        thr_run_tag = run_tag_map[run_name_step]
                    thr_run_tag_ref.append(thr_run_tag)

                    thr_id_ref.append(id_step)
                    thr_time_ref.append(time_step)

                    thr_default_ref.append(alert_thr_raw[idx])
                    thr_value_def.append(alert_value_raw[idx])

                    if isinstance(alert_index_raw[idx], list):
                        if alert_index_raw[idx].__len__() == 1:
                            alert_index_select = alert_index_raw[idx][0]
                        else:
                            alert_index_select = pd.DatetimeIndex(alert_index_raw[idx]).max()
                    else:
                        alert_index_select = alert_index_raw[idx]
                    thr_time_def.append(alert_index_select)

                    if isinstance(alert_run_raw[idx], list):
                        if alert_run_raw[idx].__len__() == 1:
                            alert_run_select = alert_run_raw[idx][0]
                        else:
                            alert_run_select = '::'.join(alert_run_raw[idx])
                    else:
                        alert_run_select = alert_run_raw[idx]
                    thr_run_def.append(alert_run_select)
                    thr_section_def.append(alert_section_raw[idx])
                    thr_type_def.append(summary_level_alert_status)
                    thr_code_def.append(summary_level_alert_code)

                    thr_description_string = ' :: '.join(
                        [alert_section_raw[idx], str(alert_index_raw[idx]), str(alert_value_raw[idx])])

                    thr_description_def.append(thr_description_string)

                finite_idx = [i for i, n in enumerate(alarm_value_raw) if n is not None and np.isfinite(n)]
                for idx in finite_idx:

                    thr_run_name_ref.append(run_name_step)
                    thr_run_tag = 'UNKNOWN'
                    if run_name_step in list(run_tag_map.keys()):
                        thr_run_tag = run_tag_map[run_name_step]
                    thr_run_tag_ref.append(thr_run_tag)

                    thr_id_ref.append(id_step)
                    thr_time_ref.append(time_step)

                    thr_default_ref.append(alarm_thr_raw[idx])
                    thr_value_def.append(alarm_value_raw[idx])

                    if isinstance(alarm_index_raw[idx], list):
                        if alarm_index_raw[idx].__len__() == 1:
                            alarm_index_select = alarm_index_raw[idx][0]
                        else:
                            alarm_index_select = pd.DatetimeIndex(alarm_index_raw[idx]).max()
                    else:
                        alarm_index_select = alarm_index_raw[idx]
                    thr_time_def.append(alarm_index_select)

                    if isinstance(alarm_run_raw[idx], list):
                        if alarm_run_raw[idx].__len__() == 1:
                            alarm_run_select = alarm_run_raw[idx][0]
                        else:
                            alarm_run_select = '::'.join(alarm_run_raw[idx])
                    else:
                        alarm_run_select = alarm_run_raw[idx]
                    thr_run_def.append(alarm_run_select)

                    thr_section_def.append(alarm_section_raw[idx])
                    thr_type_def.append(summary_level_alarm_status)
                    thr_code_def.append(summary_level_alarm_code)

                    thr_description_string = ' :: '.join(
                        [alarm_section_raw[idx], str(alarm_index_raw[idx]), str(alarm_value_raw[idx])])

                    thr_description_def.append(thr_description_string)

            # info run end
            log_stream.info(' ------> Run "' + run_name_step + '" ... DONE')
        else:
            # info run end
            log_stream.info(' ------> Run "' + run_name_step + '" ... SKIPPED. Datasets are not available')

    # define run thr dframe
    run_thr_dict = {
        'reference_run_name': thr_run_name_ref, 'reference_run_tag': thr_run_tag_ref,
        'reference_id': thr_id_ref, 'reference_time': thr_time_ref,
        'section_thr': thr_default_ref, 'section_data': thr_value_def,
        'section_time': thr_time_def, 'section_name': thr_section_def, 'section_run': thr_run_def,
        'data_type': thr_type_def, 'data_code': thr_code_def, 'data_description': thr_description_def}

    run_thr_dframe = pd.DataFrame(run_thr_dict)

    # info end
    log_stream.info(' -----> Organize bulletin info warning ... DONE')

    return run_info_dframe, run_thr_dframe
# -------------------------------------------------------------------------------------
