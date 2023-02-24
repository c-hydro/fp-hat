"""
Library Features:

Name:          lib_bulletin_io_ascii
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210225'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to write bulletin warnings ascii file
def write_bulletin_warnings(time_run, time_exec, time_format='%Y-%m-%d %H:%M', time_mode='LOCAL',
                            file_name='bulletin_warnings.csv',
                            bulletin_dframe_today=None, bulletin_dframe_tomorrow=None,
                            sections_dframe=None,
                            section_header_list=None, section_name_tag='section_tag', section_data_nan='NA',
                            column_delimiter=',',
                            no_data_string='NA', no_data_time='NAT', no_data_value=-99, no_data_code=0):

    # define section header list
    if section_header_list is None:
        section_header_list = [
            'section_name', 'thr_alert', 'thr_alarm',
            'today_run', 'today_thr_code', 'today_thr_type', 'today_thr_value', 'today_thr_time',
            'tomorrow_run', 'tomorrow_thr_code', 'tomorrow_thr_type', 'tomorrow_thr_value', 'tomorrow_thr_time'
        ]

    if bulletin_dframe_today is None:
        log_stream.error(' ===> Bulletin dataframe for today is defined by NoneType')
        raise RuntimeError('DataFrame must be defined. NoneType is not supported by the algorithm')
    if bulletin_dframe_tomorrow is None:
        log_stream.error(' ===> Bulletin dataframe for tomorrow is defined by NoneType')
        raise RuntimeError('DataFrame must be defined. NoneType is not supported by the algorithm')

    # define section tag list
    section_tag_list = list(bulletin_dframe_today[section_name_tag])

    # iterate over sections
    section_collections = [column_delimiter.join(section_header_list)]
    for id_step, section_tag_step in enumerate(section_tag_list):

        # initialize section fields
        section_fields_list = []

        # extract section info
        section_info = sections_dframe.loc[sections_dframe[section_name_tag].str.lower() == section_tag_step.lower()]

        # extract section dataframe
        section_dframe_today = bulletin_dframe_today.loc[
            bulletin_dframe_today[section_name_tag].str.lower() == section_tag_step.lower()]
        section_dframe_tomorrow = bulletin_dframe_tomorrow.loc[
            bulletin_dframe_tomorrow[section_name_tag].str.lower() == section_tag_step.lower()]

        # organize static info
        section_fields_list.append(section_info['section_tag'].values[0])
        section_fields_list.append(section_info['section_discharge_thr_alert'].values[0])
        section_fields_list.append(section_info['section_discharge_thr_alarm'].values[0])

        # organize dynamic info today
        if not section_dframe_today.empty:
            section_fields_list.append(section_dframe_today['run_description'].values[0])
            section_fields_list.append(section_dframe_today['thr_code'].values[0])
            section_fields_list.append(section_dframe_today['thr_type'].values[0])
            section_fields_list.append(section_dframe_today['thr_value_data'].values[0])
            section_fields_list.append(section_dframe_today['thr_time'].values[0])
        else:
            section_fields_list.append(no_data_string)
            section_fields_list.append(no_data_code)
            section_fields_list.append(no_data_string)
            section_fields_list.append(no_data_value)
            section_fields_list.append(no_data_time)

        # organize dynamic info tomorrow
        if not section_dframe_tomorrow.empty:
            section_fields_list.append(section_dframe_tomorrow['run_description'].values[0])
            section_fields_list.append(section_dframe_tomorrow['thr_code'].values[0])
            section_fields_list.append(section_dframe_tomorrow['thr_type'].values[0])
            section_fields_list.append(section_dframe_tomorrow['thr_value_data'].values[0])
            section_fields_list.append(section_dframe_tomorrow['thr_time'].values[0])
        else:
            section_fields_list.append(no_data_string)
            section_fields_list.append(no_data_code)
            section_fields_list.append(no_data_string)
            section_fields_list.append(no_data_value)
            section_fields_list.append(no_data_time)

        # convert to str all listed values
        section_fields_filled = [section_data_nan if elem is None else str(elem) for elem in section_fields_list]
        # merge the string row in a common workspace
        section_collections.append(column_delimiter.join(section_fields_filled))

    # dump data to file
    with open(file_name, 'w') as file_handle:
        for section_row in section_collections:
            section_row = section_row + '\n'
            file_handle.write(section_row)

# -------------------------------------------------------------------------------------
