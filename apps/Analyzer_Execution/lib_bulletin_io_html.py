"""
Library Features:

Name:          lib_bulletin_io_html
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201202'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import numpy as np
import pandas as pd

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write the html bulletin summary
def write_bulletin_summary(time_run, time_exec, time_format='%Y-%m-%d %H:%M', time_mode='LOCAL',
                           file_name='bulletin_operational_chain.html',
                           bulletin_dframe_info=None, bulletin_dframe_thr=None,
                           tag_op_chain='Bulletin of Operational Chain',
                           no_data_time='NAT', no_data_value='NA', no_data_expected='-',
                           time_rounding_resolution='D', time_rounding_type='floor'):

    # --------------------------------------------------------------------------------------------------------------
    # compute today time(s)
    if time_rounding_type == 'floor':
        time_stamp_today = time_run.floor(time_rounding_resolution)
    elif time_rounding_type == 'ceil':
        time_stamp_today = time_run.ceil(time_rounding_resolution)
    elif time_rounding_type == 'round':
        time_stamp_today = time_run.round(time_rounding_resolution)
    else:
        log_stream.error(' ===> Time rounding type "' + time_rounding_type + '" is not supported')
        raise NotImplemented('Case not implemented yet')

    time_stamp_today_from = time_stamp_today.replace(hour=0, minute=0, second=0)
    time_stamp_today_to = time_stamp_today.replace(hour=23, minute=59, second=59)

    # compute tomorrow time(s)
    time_stamp_tomorrow = time_stamp_today + pd.Timedelta(days=1)
    time_stamp_tomorrow = time_stamp_tomorrow.round(time_rounding_resolution)
    time_stamp_tomorrow_from = time_stamp_tomorrow.replace(hour=0, minute=0, second=0)
    time_stamp_tomorrow_to = time_stamp_tomorrow.replace(hour=23, minute=59, second=59)
    # --------------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------------
    # select datasets into the maximum period (today and tomorrow
    if not bulletin_dframe_thr.empty:
        # filter by time(s)
        bulletin_dframe_thr = bulletin_dframe_thr.loc[
            (bulletin_dframe_thr['section_time'] >= time_stamp_today_from) &
            (bulletin_dframe_thr['section_time'] <= time_stamp_tomorrow_to)]
        # filter by view options
        bulletin_dframe_thr = bulletin_dframe_thr.loc[bulletin_dframe_thr['view_warnings']]

    run_section_list = sorted(list(set(bulletin_dframe_thr['section_name'])))
    run_section_counts = {}
    for run_section_step in run_section_list:
        tmp_dframe_thr = bulletin_dframe_thr.loc[bulletin_dframe_thr['section_name'] == run_section_step]
        run_section_n = tmp_dframe_thr.value_counts(['reference_time', 'data_code']).max()
        run_section_counts[run_section_step] = run_section_n
    # --------------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------------
    # open html file
    with open(file_name, "w") as html_handle:

        # --------------------------------------------------------------------------------------------------------------
        # write html structure
        html_handle.write('<!DOCTYPE html>\n')
        html_handle.write('<title>' + tag_op_chain + '</title>\n')

        # define html style(s)
        html_handle.write('<head>\n')
        html_handle.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n')
        html_handle.write('<style>\n')
        html_handle.write('table, th, td {border: 1px solid black; padding:3px; margin: 20px;}\n')
        html_handle.write('div {border: solid black 0px; padding: 0px; margin-bottom: 0px; margin-top: 0px;}\n')
        html_handle.write('h1 {margin: 0px; font-family: Times New Roman, Times, serif; font-size: 34px;}\n')
        html_handle.write('h2 {margin: 0px;font-family: Times New Roman, Times, serif; font-size: 26px;}\n')
        html_handle.write('p {margin: 1px; font-family: Times New Roman, Times, serif; font-size: 22px;}\n')
        html_handle.write('th {font-family: Times New Roman, Times, serif; font-size: 14px;}\n')
        html_handle.write('td {font-family: Times New Roman, Times, serif; font-size: 12px;}\n')
        html_handle.write('.red {background-color: rgba(255,0,0,0.5);color: black;}\n')
        html_handle.write('.orange {background-color: rgba(235,149,50,0.5);color: black;}\n')
        html_handle.write('.sky {background-color: rgba(0,206,241,0.5);color: black;}\n')
        html_handle.write('.white {background-color: rgba(255,255,255, 0.3);color: black;}\n')
        html_handle.write('.yellow {background-color: rgba(255,255,0,0.5); color: black;}\n')
        html_handle.write('.green {background-color: rgba(0,255,0,0.5); color: black;}\n')
        html_handle.write('.cyan {background-color: rgba(0,255,255,0.5); color: black;}\n')
        html_handle.write('.gray {background-color: rgba(128,128,128,0.5); color: black;}\n')
        html_handle.write('.blue {background-color: rgba(0,0,255,0.5); color: black;}\n')
        html_handle.write('.black {background-color: rgba(0,0,0,0.9); color: white;}\n')
        html_handle.write('.ColumnStyle_Center {text-align: center; vertical-align:middle;}\n')
        html_handle.write('.ColumnStyle_Left {text-align: left; vertical-align:middle;}\n')
        html_handle.write('.ColumnStyle_Right {text-align: right; vertical-align:middle;}\n')
        html_handle.write('.ColumnWidth_Type1 {width:140px;}\n')
        html_handle.write('.ColumnWidth_Type2 {width:160px;}\n')
        html_handle.write('.ColumnWidth_Type3 {width:175px;}\n')
        html_handle.write('.ColumnWidth_Type4 {width:200px;}\n')
        html_handle.write('.ColumnWidth_Type5 {width:60px;}\n')
        html_handle.write('.ColumnWidth_Type6 {width:250px;}\n')
        html_handle.write('.ColumnWidth_Type7 {width:150px;}\n')
        # html_handle.write('.RowHeight_Type {height: 3em; line-height: 2em; overflow: hidden;}\n')
        html_handle.write('.RowHeight_Type {height: 30px; line-height: 15px; overflow: hidden;}\n')
        html_handle.write('.td_custom {font-family: Times New Roman, Times, serif; font-size: 22px;}\n')
        html_handle.write('.tr_custom {font-family: Times New Roman, Times, serif; font-size: 22px;}\n')
        html_handle.write('.RowHover tr:hover {background-color: lightgrey !important;}\n')
        # html_handle.write('p:hover {background-color: red !important;}\n')
        # html_handle.write('.tbl tr:hover {background-color: coral;}\n')
        html_handle.write('</style>\n')
        html_handle.write('</head>\n')
        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------
        # generic title
        html_handle.write('<body>\n')
        html_handle.write('<div class="container">\n')
        html_handle.write('<h1>' + tag_op_chain + '</h1>\n')
        html_handle.write('</div>\n')

        html_handle.write('<br style="clear:both; bottom-margin:10px;"/>\n')
        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------
        # part 1 - reference time
        td_time_run = time_run.strftime(time_format) + ' ' + time_mode
        td_time_exec = time_exec.strftime(time_format) + ' ' + time_mode

        html_handle.write('<div class="container">\n')
        html_handle.write('<h2> Reference Time </h2>\n')
        html_handle.write('<section>\n')
        html_handle.write('<p>This part provides the bulletin times.</p>\n')
        html_handle.write('</section>\n')

        html_handle.write('<table class="RowHover" title="Reference Time">\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue ColumnStyle_Center td_custom"> Reference Time </th>\n')
        # html_handle.write('<th class="blue ColumnStyle_Center"><font size=3> Execution Time: </th>\n')
        html_handle.write('<th class="blue ColumnStyle_Center td_custom"> Execution Time </th>\n')
        html_handle.write('</tr>\n')
        html_handle.write('<tr>\n')
        html_handle.write('<td class="ColumnStyle_Center td_custom"><b>' + td_time_run + '</b></th>\n')
        html_handle.write('<td class="ColumnStyle_Center td_custom"><b>' + td_time_exec + '</b></th>\n')
        html_handle.write('</tr>\n')
        # close table
        html_handle.write('</table>\n')
        html_handle.write('</div>\n')

        html_handle.write('<br style="clear:both"/>\n')
        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------
        # part 2 - summary run info
        html_handle.write('<div class="container">\n')
        html_handle.write('<h2> Run Status </h2>\n')
        html_handle.write('<section>\n')
        html_handle.write('<p>This part provides the list of run status and execution.</p>\n')
        html_handle.write('</section>\n')

        html_handle.write('<table class="RowHover" title="Run Status">\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b>Run Description</th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type3 ColumnStyle_Center"><b>State</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b>TimeStart</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b>TimeEnd</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b>TimeElapsed</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b>Scenarios Completed</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b>Scenarios Expected</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b>Sections</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b>Domain</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b>Last Run</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type4 ColumnStyle_Center"><b>Period Run</b></th>\n')
        html_handle.write('</tr>\n')

        # iterate over run(s)
        for run_info_id, run_info_row in bulletin_dframe_info.iterrows():
            run_n = run_info_row['run_n']
            run_expected = run_info_row['run_expected']
            run_description = run_info_row['run_description']
            run_status_code = run_info_row['run_status_code']
            run_status_description = run_info_row['run_status_description']
            time_start = run_info_row['time_start']
            time_end = run_info_row['time_end']
            time_elapsed = run_info_row['time_elapsed']
            section_n = run_info_row['section']
            domain_name = run_info_row['domain_name']
            run_last = run_info_row['run_last']
            run_period = run_info_row['run_period']
            run_view_warnings = run_info_row['view_warnings']
            run_view_execution = run_info_row['view_execution']

            # check view execution option
            if run_view_execution:
                if time_start != no_data_time and time_end != no_data_time:
                    if int(run_n) == int(run_expected):
                        td_color_time = 'cyan'
                        td_time_start = time_start + ' ' + time_mode
                        td_time_end = time_end + ' ' + time_mode
                        td_time_elapsed = time_elapsed
                    else:
                        td_color_time = 'sky'
                        td_time_start = time_start + ' ' + time_mode
                        td_time_end = time_end + ' ' + time_mode
                        td_time_elapsed = time_elapsed
                elif time_start != no_data_time and time_end == no_data_time:
                    td_color_time = 'gray'
                    td_time_start = time_start + ' ' + time_mode
                    td_time_end = no_data_time
                    td_time_elapsed = no_data_time
                elif time_start == no_data_time and time_end == no_data_time:
                    td_color_time = 'red'
                    td_time_start = no_data_time
                    td_time_end = no_data_time
                    td_time_elapsed = no_data_time
                else:
                    td_color_time = 'black'
                    td_time_start = 'UNKNOWN'
                    td_time_end = 'UNKNOWN'
                    td_time_elapsed = 'UNKNOWN'

                if run_last != no_data_time:
                    td_color_run = 'green'
                    td_run_last = run_last + ' ' + time_mode
                else:
                    td_color_run = 'red'
                    td_run_last = no_data_time

                td_run_period = run_period + ' ' + time_mode

                html_handle.write('<tr>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                  run_description + '</b></td>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type3 ColumnStyle_Center">' +
                                  run_status_description + '</td>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type1 ColumnStyle_Center">' +
                                  td_time_start + ' </td>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type1 ColumnStyle_Center">' +
                                  td_time_end + ' </td>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type1 ColumnStyle_Center">' +
                                  td_time_elapsed + ' </td>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type5 ColumnStyle_Center">' +
                                  run_n + '</td>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type5 ColumnStyle_Center">' +
                                  run_expected + '</td>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type5 ColumnStyle_Center">' +
                                  section_n + '</td>\n')
                html_handle.write('<td class="' + td_color_time + ' ColumnWidth_Type5 ColumnStyle_Center">' +
                                  domain_name + '</td>\n')
                html_handle.write('<td class="' + td_color_run + ' ColumnWidth_Type1 ColumnStyle_Center">' +
                                  td_run_last + '</td>\n')
                html_handle.write('<td class="' + td_color_run + ' ColumnWidth_Type4 ColumnStyle_Center">' +
                                  td_run_period + '</td>\n')
                html_handle.write('</tr>\n')

        # close table
        html_handle.write('</table>\n')
        html_handle.write('</div>\n')

        html_handle.write('<br style="clear:both"/>\n')
        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------
        # part 3 - summary alert section info
        html_handle.write('<div class="container">\n')
        html_handle.write('<h2> Sections Status - Alert </h2>\n')
        html_handle.write('<p>This part provides the list of sections where the yellow threshold has been exceeded for today and/or tomorrow datasets.</p>\n')

        html_handle.write('<div class="row">\n')

        html_handle.write('<div class="column">\n')
        html_handle.write('<table class="RowHover" style="float:left; margin-right:10px;" title="Sections Status - Alert - Today">\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue colspan="1" ColumnStyle_Center"><b> Alert [yellow] </b> </th>\n')
        html_handle.write('<th class="blue colspan="1" ColumnStyle_Center"><b> ' + str(time_stamp_today) + '</b> </th>\n')
        html_handle.write('</tr>\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Section Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b> Run Description </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type7 ColumnStyle_Center"><b> Run Domain -- Run Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Threshold [m^3/s]</b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Discharge [m^3/s] </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Time </b> </th>\n')
        html_handle.write('</tr>\n')

        # data part
        run_select_summary = bulletin_dframe_thr.loc[bulletin_dframe_thr['data_warn_level'] == 'alert'] # yellow
        run_section_list = sorted(list(set(bulletin_dframe_thr['section_name'])))
        # iterate over section list
        if run_section_list:
            for run_section_name in run_section_list:

                # select today datasets
                run_section_today = run_select_summary.loc[
                    (run_select_summary['section_time'] >= time_stamp_today_from) &
                    (run_select_summary['section_time'] <= time_stamp_today_to)]

                run_shape_section = run_section_counts[run_section_name]

                run_data_today = run_section_today.loc[bulletin_dframe_thr['section_name'] == run_section_name]
                run_shape_today = run_data_today.shape[0]

                if run_shape_section == run_shape_today:
                    td_shape_today = str(run_shape_section)
                    td_shape_extra = 0
                elif run_shape_section > run_shape_today:
                    td_shape_today = str(run_shape_section)
                    td_shape_extra = run_shape_section - run_shape_today
                else:
                    td_shape_today = str(run_shape_section)
                    td_shape_extra = 0

                # check data availability
                html_handle.write('<tr>\n')
                if not run_data_today.empty:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + td_shape_today + '" class="yellow ColumnWidth_Type1 ColumnStyle_Left"><b> ' +
                        run_section_name + '</b> </td>\n')
                    # iterate over data
                    for run_id, run_data in run_data_today.iterrows():

                        # get data
                        run_warn_description = run_data['data_warn_description']
                        run_reference_description = run_data['reference_run_description']
                        run_name = run_data['reference_run_name']
                        run_tag = run_data['reference_run_tag']
                        run_section_thr = str(run_data['section_thr'])
                        run_section_data = str(run_data['section_data'])
                        run_section_time = str(run_data['section_time'])
                        run_domain_reference = str(run_data['domain_reference'])

                        # write data to html
                        html_handle.write('<td class="yellow ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          run_tag + '</b></td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          run_reference_description + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_thr + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_data + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_time + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                    # iterate over extra
                    for extra_id in range(0, td_shape_extra):
                        # write data to html
                        html_handle.write('<td class="yellow ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          no_data_expected + '</b></td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                else:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + td_shape_today + '" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over extra
                    for extra_id in range(0, td_shape_extra):
                        html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          no_data_expected + '</b> </td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

        else:

            # write section info
            html_handle.write('<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>-</b></td>\n')
            # write null to html
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                              no_data_expected + '</b></td>\n')
            html_handle.write('<td class="white ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')

            # close section
            html_handle.write('</tr>\n')

        # close table
        html_handle.write('</table>\n')
        html_handle.write('</div>\n')

        html_handle.write('<div class="column">\n')
        html_handle.write('<table style="float:left;" class="RowHover" title="Sections Status - Alert - Tomorrow">\n')

        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue colspan="1" ColumnStyle_Center"><b> Alert [yellow] </b> </th>\n')
        html_handle.write('<th class="blue colspan="1" ColumnStyle_Center"><b> ' + str(time_stamp_tomorrow) + '</b> </th>\n')
        html_handle.write('</tr>\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Section Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b> Run Description </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type7 ColumnStyle_Center"><b> Run Domain -- Run Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Threshold [m^3/s]</b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Discharge [m^3/s] </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Time </b> </th>\n')
        html_handle.write('</tr>\n')

        # data part
        run_select_summary = bulletin_dframe_thr.loc[bulletin_dframe_thr['data_warn_level'] == 'alert'] # yellow
        # iterate over section list
        if run_section_list:
            for run_section_name in run_section_list:

                # select tomorrow datasets
                run_section_tomorrow = run_select_summary.loc[
                    (run_select_summary['section_time'] >= time_stamp_tomorrow_from) &
                    (run_select_summary['section_time'] <= time_stamp_tomorrow_to)]

                run_shape_section = run_section_counts[run_section_name]

                run_data_tomorrow = run_section_tomorrow.loc[bulletin_dframe_thr['section_name'] == run_section_name]
                run_shape_tomorrow = run_data_tomorrow.shape[0]

                if run_shape_section == run_shape_tomorrow:
                    td_shape_tomorrow = str(run_shape_section)
                    td_shape_extra = 0
                elif run_shape_section > run_shape_tomorrow:
                    td_shape_tomorrow = str(run_shape_section)
                    td_shape_extra = run_shape_section - run_shape_tomorrow
                else:
                    td_shape_tomorrow = str(run_shape_section)
                    td_shape_extra = 0

                # check data availability
                html_handle.write('<tr>\n')
                if not run_data_tomorrow.empty:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + td_shape_tomorrow + '" class="yellow ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over data
                    for run_id, run_data in run_data_tomorrow.iterrows():

                        # get data
                        run_warn_description = run_data['data_warn_description']
                        run_reference_description = run_data['reference_run_description']
                        run_name = run_data['reference_run_name']
                        run_tag = run_data['reference_run_tag']
                        run_section_thr = str(run_data['section_thr'])
                        run_section_data = str(run_data['section_data'])
                        run_section_time = str(run_data['section_time'])
                        run_domain_reference = str(run_data['domain_reference'])

                        # write data to html
                        html_handle.write('<td class="yellow ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          run_tag + '</b></td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          run_reference_description + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_thr + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_data + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_time + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                    # iterate over extra
                    for extra_id in range(0, td_shape_extra):
                        # write data to html
                        html_handle.write('<td class="yellow ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          no_data_expected + '</b></td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                else:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + td_shape_tomorrow + '" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over extra
                    for extra_id in range(0, td_shape_extra):
                        html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          no_data_expected + '</b> </td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

        else:

            # write section info
            html_handle.write('<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>-</b></td>\n')
            # write null to html
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                              no_data_expected + '</b></td>\n')
            html_handle.write('<td class="white ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')

            # close section
            html_handle.write('</tr>\n')

        # close table
        html_handle.write('</table>\n')
        html_handle.write('</div>\n')

        html_handle.write('</div>\n')

        html_handle.write('<br style="clear:both"/>\n')
        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------
        # part 4 - summary alarm section info
        html_handle.write('<div class="container">\n')
        html_handle.write('<h2> Sections Status - Alarm </h2>\n')

        html_handle.write('<p>This part provides the list of sections where the red threshold has been exceeded for today and/or tomorrow datasets.</p>\n')

        html_handle.write('<div class="row">\n')
        html_handle.write('<div class="column">\n')

        html_handle.write('<table style="float:left; margin-right:10px;" class="RowHover" title="Section Status - Alarm - Today">\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue colspan="1" ColumnStyle_Center"><b> Alarm [red] </b> </th>\n')
        html_handle.write('<th class="blue colspan="1" ColumnStyle_Center"><b> ' + str(time_stamp_today) + '</b> </th>\n')
        html_handle.write('</tr>\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Section Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b> Run Description </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type7 ColumnStyle_Center"><b> Run Domain -- Run Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Threshold [m^3/s]</b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Discharge [m^3/s] </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Time </b> </th>\n')
        html_handle.write('</tr>\n')

        # data part
        run_select_summary = bulletin_dframe_thr.loc[bulletin_dframe_thr['data_warn_level'] == 'alarm'] # red
        run_section_list = sorted(list(set(bulletin_dframe_thr['section_name'])))
        # iterate over section list
        if run_section_list:
            for run_section_name in run_section_list:

                # select today datasets
                run_section_today = run_select_summary.loc[
                    (run_select_summary['section_time'] >= time_stamp_today_from) &
                    (run_select_summary['section_time'] <= time_stamp_today_to)]

                run_shape_section = run_section_counts[run_section_name]

                run_data_today = run_section_today.loc[bulletin_dframe_thr['section_name'] == run_section_name]
                run_shape_today = run_data_today.shape[0]

                if run_shape_section == run_shape_today:
                    td_shape_today = str(run_shape_section)
                    td_shape_extra = 0
                elif run_shape_section > run_shape_today:
                    td_shape_today = str(run_shape_section)
                    td_shape_extra = run_shape_section - run_shape_today
                else:
                    td_shape_today = str(run_shape_section)
                    td_shape_extra = 0

                # check data availability
                html_handle.write('<tr>\n')
                if not run_data_today.empty:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + td_shape_today + '" class="red ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over data
                    for run_id, run_data in run_data_today.iterrows():

                        # get data
                        run_warn_description = run_data['data_warn_description']
                        run_reference_description = run_data['reference_run_description']
                        run_name = run_data['reference_run_name']
                        run_tag = run_data['reference_run_tag']
                        run_section_thr = str(run_data['section_thr'])
                        run_section_data = str(run_data['section_data'])
                        run_section_time = str(run_data['section_time'])
                        run_domain_reference = str(run_data['domain_reference'])

                        # write data to html
                        html_handle.write('<td class="red ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          run_tag + '</b></td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          run_reference_description + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_thr + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_data + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_time + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                    # iterate over extra
                    for extra_id in range(0, td_shape_extra):
                        # write data to html
                        html_handle.write('<td class="red ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          no_data_expected + '</b></td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                else:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + td_shape_today + '" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over extra
                    for extra_id in range(0, td_shape_extra):
                        html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          no_data_expected + '</b> </td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

        else:
            # write section info
            html_handle.write('<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>-</b></td>\n')
            # write null to html
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                              no_data_expected + '</b></td>\n')
            html_handle.write('<td class="white ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')

            # close section
            html_handle.write('</tr>\n')

        # close table
        html_handle.write('</table>\n')
        html_handle.write('</div>\n')

        html_handle.write('<div class="column">\n')
        html_handle.write('<table style="float: left" class="RowHover" title="Section Status - Alarm - Tomorrow">\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue colspan="1" ColumnStyle_Center"><b> Alarm [red] </b> </th>\n')
        html_handle.write('<th class="blue colspan="1" ColumnStyle_Center"><b> ' + str(time_stamp_tomorrow) + '</b> </th>\n')
        html_handle.write('</tr>\n')
        html_handle.write('<tr>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Section Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b> Run Description </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type7 ColumnStyle_Center"><b> Run Domain -- Run Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Threshold [m^3/s]</b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Discharge [m^3/s] </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Time </b> </th>\n')
        html_handle.write('</tr>\n')

        # data part
        run_select_summary = bulletin_dframe_thr.loc[bulletin_dframe_thr['data_warn_level'] == 'alarm'] # red
        # iterate over section list
        if run_section_list:
            for run_section_name in run_section_list:

                # select today datasets
                run_section_tomorrow = run_select_summary.loc[
                    (run_select_summary['section_time'] >= time_stamp_tomorrow_from) &
                    (run_select_summary['section_time'] <= time_stamp_tomorrow_to)]

                run_shape_section = run_section_counts[run_section_name]

                run_data_tomorrow = run_section_tomorrow.loc[bulletin_dframe_thr['section_name'] == run_section_name]
                run_shape_tomorrow = run_data_tomorrow.shape[0]

                if run_shape_section == run_shape_tomorrow:
                    td_shape_tomorrow = str(run_shape_section)
                    td_shape_extra = 0
                elif run_shape_section > run_shape_tomorrow:
                    td_shape_tomorrow = str(run_shape_section)
                    td_shape_extra = run_shape_section - run_shape_tomorrow
                else:
                    td_shape_tomorrow = str(run_shape_section)
                    td_shape_extra = 0

                # check data availability
                html_handle.write('<tr>\n')
                if not run_data_tomorrow.empty:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + td_shape_tomorrow + '" class="red ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over section data
                    for run_id, run_data in run_data_tomorrow.iterrows():

                        # get data
                        run_warn_description = run_data['data_warn_description']
                        run_reference_description = run_data['reference_run_description']
                        run_name = run_data['reference_run_name']
                        run_tag = run_data['reference_run_tag']
                        run_section_thr = str(run_data['section_thr'])
                        run_section_data = str(run_data['section_data'])
                        run_section_time = str(run_data['section_time'])
                        run_domain_reference = str(run_data['domain_reference'])

                        # write data to html
                        html_handle.write('<td class="red ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          run_tag + '</b></td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          run_reference_description + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_thr + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_data + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          run_section_time + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                    # iterate over extra
                    for extra_id in range(0, td_shape_extra):
                        # write data to html
                        html_handle.write('<td class="red ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          no_data_expected + '</b></td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                else:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + td_shape_tomorrow + '" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over extra
                    for extra_id in range(0, td_shape_extra):
                        html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                                          no_data_expected + '</b> </td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')
                        html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                                          no_data_expected + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

        else:
            # write section info
            html_handle.write('<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>-</b></td>\n')
            # write null to html
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left RowHeight_Type"><b>' +
                              no_data_expected + '</b></td>\n')
            html_handle.write('<td class="white ColumnWidth_Type7 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')
            html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center RowHeight_Type">' +
                              no_data_expected + '</td>\n')

            # close section
            html_handle.write('</tr>\n')

        # close table
        html_handle.write('</table>\n')

        html_handle.write('</div>\n')
        html_handle.write('</div>\n')

        html_handle.write('</div>\n')

        html_handle.write('<br style="clear:both"/>\n')
        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------
        # close html
        html_handle.write('</body>\n')
        html_handle.write('</html>')
        # --------------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------------
    # debug
    '''
    import webbrowser
    webbrowser.open(html_name)
    print('')
    '''
    # --------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
