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
                           no_data_time='NAT', no_data_value='NA'):

    # --------------------------------------------------------------------------------------------------------------
    # compute today time(s)
    time_stamp_today = time_run.round('D')
    time_stamp_today_from = time_stamp_today.replace(hour=0, minute=0, second=0)
    time_stamp_today_to = time_stamp_today.replace(hour=23, minute=59, second=59)
    # compute tomorrow time(s)
    time_stamp_tomorrow = time_stamp_today + pd.Timedelta(days=1)
    time_stamp_tomorrow = time_stamp_tomorrow.round('D')
    time_stamp_tomorrow_from = time_stamp_tomorrow.replace(hour=0, minute=0, second=0)
    time_stamp_tomorrow_to = time_stamp_tomorrow.replace(hour=23, minute=59, second=59)
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
        html_handle.write('.white {background-color: rgba(255,255,255, 0.3);color: black;}\n')
        html_handle.write('.yellow {background-color: rgba(255,255,0,0.5); color: black;}\n')
        html_handle.write('.verde {background-color: rgba(0,255,0,0.5); color: black;}\n')
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
        html_handle.write('.ColumnWidth_Type6 {width:200px;}\n')
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
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b>Scenarios</b></th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b>Sections</b></th>\n')
        html_handle.write('</tr>\n')

        # iterate over run(s)
        for run_info_id, run_info_row in bulletin_dframe_info.iterrows():
            run_n = run_info_row['run_n']
            run_description = run_info_row['run_description']
            run_status_code = run_info_row['run_status_code']
            run_status_description = run_info_row['run_status_description']
            time_start = run_info_row['time_start']
            time_end = run_info_row['time_end']
            time_elapsed = run_info_row['time_elapsed']
            section_n = run_info_row['section']
            domain_name = run_info_row['domain_name']

            if time_start != no_data_time and time_end != no_data_time:
                td_color = 'cyan'
                td_time_start = time_start + ' ' + time_mode
                td_time_end = time_end + ' ' + time_mode
                td_time_elapsed = time_elapsed
            elif time_start != no_data_time and time_end == no_data_time:
                td_color = 'gray'
                td_time_start = time_start + ' ' + time_mode
                td_time_end = no_data_time
                td_time_elapsed = no_data_time
            elif time_start == no_data_time and time_end == no_data_time:
                td_color = 'red'
                td_time_start = no_data_time
                td_time_end = no_data_time
                td_time_elapsed = no_data_time
            else:
                td_color = 'black'
                td_time_start = 'UNKNOWN'
                td_time_end = 'UNKNOWN'
                td_time_elapsed = 'UNKNOWN'

            html_handle.write('<tr>\n')
            html_handle.write('<td class="' + td_color + ' ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                              run_description + '</b></td>\n')
            html_handle.write('<td class="' + td_color + ' ColumnWidth_Type3 ColumnStyle_Center">' +
                              run_status_description + '</td>\n')
            html_handle.write('<td class="' + td_color + ' ColumnWidth_Type1 ColumnStyle_Center">' +
                              td_time_start + ' </td>\n')
            html_handle.write('<td class="' + td_color + ' ColumnWidth_Type1 ColumnStyle_Center">' +
                              td_time_end + ' </td>\n')
            html_handle.write('<td class="' + td_color + ' ColumnWidth_Type1 ColumnStyle_Center">' +
                              td_time_elapsed + ' </td>\n')
            html_handle.write('<td class="' + td_color + ' ColumnWidth_Type5 ColumnStyle_Center">' +
                              run_n + '</td>\n')
            html_handle.write('<td class="' + td_color + ' ColumnWidth_Type5 ColumnStyle_Center">' +
                              section_n + '</td>\n')
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
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b> Run Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Threshold [m^3/s]</b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Discharge [m^3/s] </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Time </b> </th>\n')
        html_handle.write('</tr>\n')

        # data part
        run_select_summary = bulletin_dframe_thr.loc[bulletin_dframe_thr['data_type'] == 'alert'] # yellow
        run_section_list = sorted(list(set(bulletin_dframe_thr['section_name'])))
        # iterate over section list
        if run_section_list:
            for run_section_name in run_section_list:

                # select today datasets
                run_section_today = run_select_summary.loc[
                    (run_select_summary['section_time'] >= time_stamp_today_from) &
                    (run_select_summary['section_time'] <= time_stamp_today_to)]

                run_data_today = run_section_today.loc[bulletin_dframe_thr['section_name'] == run_section_name]
                run_shape_today = str(run_data_today.shape[0])

                # check data availability
                html_handle.write('<tr>\n')
                if not run_data_today.empty:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + run_shape_today + '" class="yellow ColumnWidth_Type1 ColumnStyle_Left"><b> ' +
                        run_section_name + '</b> </td>\n')
                    # iterate over data
                    for run_id, run_data in run_data_today.iterrows():

                        # get data
                        run_description = run_data['data_description']
                        run_name = run_data['reference_run_name']
                        run_tag = run_data['reference_run_tag']
                        run_section_thr = str(run_data['section_thr'])
                        run_section_data = str(run_data['section_data'])
                        run_section_time = str(run_data['section_time'])

                        # write data to html
                        html_handle.write('<td class="yellow ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                          run_tag + '</b></td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type2 ColumnStyle_Left">' +
                                          run_name + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center">' +
                                          run_section_thr + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center">' +
                                          run_section_data + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type1 ColumnStyle_Center">' +
                                          run_section_time + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                else:
                    # write section info
                    html_handle.write(
                        '<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # write no data to html
                    html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                      no_data_value + '</b> </td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left">' +
                                      no_data_value + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center">' +
                                      no_data_value + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center">' +
                                      no_data_time + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center">' +
                                      no_data_time + '</td>\n')

                    # close section
                    html_handle.write('</tr>\n')

        else:
            # write section info
            html_handle.write('<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>-</b></td>\n')
            # write null to html
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"><b> - </b></td>\n')
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center"> - </td>\n')

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
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b> Run Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Threshold [m^3/s]</b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Discharge [m^3/s] </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Time </b> </th>\n')
        html_handle.write('</tr>\n')

        # data part
        run_select_summary = bulletin_dframe_thr.loc[bulletin_dframe_thr['data_type'] == 'alert'] # yellow
        # iterate over section list
        if run_section_list:
            for run_section_name in run_section_list:

                # select tomorrow datasets
                run_section_tomorrow = run_select_summary.loc[
                    (run_select_summary['section_time'] >= time_stamp_tomorrow_from) &
                    (run_select_summary['section_time'] <= time_stamp_tomorrow_to)]

                run_data_tomorrow = run_section_tomorrow.loc[bulletin_dframe_thr['section_name'] == run_section_name]
                run_shape_tomorrow = str(run_data_tomorrow.shape[0])

                # check data availability
                html_handle.write('<tr>\n')
                if not run_data_tomorrow.empty:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + run_shape_tomorrow + '" class="yellow ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over data
                    for run_id, run_data in run_data_tomorrow.iterrows():

                        # get data
                        run_description = run_data['data_description']
                        run_name = run_data['reference_run_name']
                        run_tag = run_data['reference_run_tag']
                        run_section_thr = str(run_data['section_thr'])
                        run_section_data = str(run_data['section_data'])
                        run_section_time = str(run_data['section_time'])

                        # write data to html
                        html_handle.write('<td class="yellow ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                          run_tag + '</b></td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type2 ColumnStyle_Left">' +
                                          run_name + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center">' +
                                          run_section_thr + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type5 ColumnStyle_Center">' +
                                          run_section_data + '</td>\n')
                        html_handle.write('<td class="yellow ColumnWidth_Type1 ColumnStyle_Center">' +
                                          run_section_time + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                else:
                    # write section info
                    html_handle.write(
                        '<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # write no data to html
                    html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                      no_data_value + '</b> </td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left">' +
                                      no_data_value + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center">' +
                                      no_data_value + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center">' +
                                      no_data_time + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center">' +
                                      no_data_time + '</td>\n')

                    # close section
                    html_handle.write('</tr>\n')

        else:
            # write section info
            html_handle.write('<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>-</b></td>\n')
            # write null to html
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"><b> - </b></td>\n')
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center"> - </td>\n')

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
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b> Run Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Threshold [m^3/s]</b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Discharge [m^3/s] </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Time </b> </th>\n')
        html_handle.write('</tr>\n')

        # data part
        run_select_summary = bulletin_dframe_thr.loc[bulletin_dframe_thr['data_type'] == 'alarm'] # red
        run_section_list = sorted(list(set(bulletin_dframe_thr['section_name'])))
        # iterate over section list
        if run_section_list:
            for run_section_name in run_section_list:

                # select today datasets
                run_section_today = run_select_summary.loc[
                    (run_select_summary['section_time'] >= time_stamp_today_from) &
                    (run_select_summary['section_time'] <= time_stamp_today_to)]

                run_data_today = run_section_today.loc[bulletin_dframe_thr['section_name'] == run_section_name]
                run_shape_today = str(run_data_today.shape[0])

                # check data availability
                html_handle.write('<tr>\n')
                if not run_data_today.empty:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + run_shape_today + '" class="red ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over data
                    for run_id, run_data in run_data_today.iterrows():

                        # get data
                        run_description = run_data['data_description']
                        run_name = run_data['reference_run_name']
                        run_tag = run_data['reference_run_tag']
                        run_section_thr = str(run_data['section_thr'])
                        run_section_data = str(run_data['section_data'])
                        run_section_time = str(run_data['section_time'])

                        # write data to html
                        html_handle.write('<td class="red ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                          run_tag + '</b></td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type2 ColumnStyle_Left">' +
                                          run_name + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center">' +
                                          run_section_thr + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center">' +
                                          run_section_data + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type1 ColumnStyle_Center">' +
                                          run_section_time + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                else:
                    # write section info
                    html_handle.write(
                        '<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # write no data to html
                    html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                      no_data_value + '</b> </td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left">' +
                                      no_data_value + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center">' +
                                      no_data_value + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center">' +
                                      no_data_time + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center">' +
                                      no_data_time + '</td>\n')

                    # close section
                    html_handle.write('</tr>\n')

        else:
            # write section info
            html_handle.write('<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>-</b></td>\n')
            # write null to html
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"><b> - </b></td>\n')
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center"> - </td>\n')

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
        html_handle.write('<th class="blue ColumnWidth_Type2 ColumnStyle_Center"><b> Run Name </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Threshold [m^3/s]</b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type5 ColumnStyle_Center"><b> Discharge [m^3/s] </b> </th>\n')
        html_handle.write('<th class="blue ColumnWidth_Type1 ColumnStyle_Center"><b> Time </b> </th>\n')
        html_handle.write('</tr>\n')

        # data part
        run_select_summary = bulletin_dframe_thr.loc[bulletin_dframe_thr['data_type'] == 'alarm'] # red
        # iterate over section list
        if run_section_list:
            for run_section_name in run_section_list:

                # select today datasets
                run_section_tomorrow = run_select_summary.loc[
                    (run_select_summary['section_time'] >= time_stamp_tomorrow_from) &
                    (run_select_summary['section_time'] <= time_stamp_tomorrow_to)]

                run_data_tomorrow = run_section_tomorrow.loc[bulletin_dframe_thr['section_name'] == run_section_name]
                run_shape_tomorrow = str(run_data_tomorrow.shape[0])

                # check data availability
                html_handle.write('<tr>\n')
                if not run_data_tomorrow.empty:
                    # write section info
                    html_handle.write(
                        '<td rowspan="' + run_shape_tomorrow + '" class="red ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # iterate over section data
                    for run_id, run_data in run_data_tomorrow.iterrows():

                        # get data
                        run_description = run_data['data_description']
                        run_name = run_data['reference_run_name']
                        run_tag = run_data['reference_run_tag']
                        run_section_thr = str(run_data['section_thr'])
                        run_section_data = str(run_data['section_data'])
                        run_section_time = str(run_data['section_time'])

                        # write data to html
                        html_handle.write('<td class="red ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                          run_tag + '</b></td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type2 ColumnStyle_Left">' +
                                          run_name + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center">' +
                                          run_section_thr + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type5 ColumnStyle_Center">' +
                                          run_section_data + '</td>\n')
                        html_handle.write('<td class="red ColumnWidth_Type1 ColumnStyle_Center">' +
                                          run_section_time + '</td>\n')

                        # close section
                        html_handle.write('</tr>\n')

                else:
                    # write section info
                    html_handle.write(
                        '<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>' +
                        run_section_name + '</b></td>\n')
                    # write no data to html
                    html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"><b>' +
                                      no_data_value + '</b> </td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left">' +
                                      no_data_value + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center">' +
                                      no_data_value + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center">' +
                                      no_data_time + '</td>\n')
                    html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center">' +
                                      no_data_time + '</td>\n')

                    # close section
                    html_handle.write('</tr>\n')

        else:
            # write section info
            html_handle.write('<td rowspan="1" class="white ColumnWidth_Type1 ColumnStyle_Left"><b>-</b></td>\n')
            # write null to html
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"><b> - </b></td>\n')
            html_handle.write('<td class="white ColumnWidth_Type2 ColumnStyle_Left"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type5 ColumnStyle_Center"> - </td>\n')
            html_handle.write('<td class="white ColumnWidth_Type1 ColumnStyle_Center"> - </td>\n')

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
