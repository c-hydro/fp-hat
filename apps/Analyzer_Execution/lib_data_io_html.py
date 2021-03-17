# -------------------------------------------------------------------------------------
# Libraries
import numpy as np
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to slice list every n elements
def slice_list(source, step):
    return [source[i::step] for i in range(step)]
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write an html summary file
def write_file_summary(time_run, time_exec, time_format='%Y-%m-%d %H:%M', time_mode='LOCAL',
                       html_name='run_analyzer.html', run_summary=None,
                       run_name=None, tag_summary_data='data', tag_summary_info='info',
                       tag_run_start='run_start', tag_run_end='run_end', tag_run_datasets='run_datasets',
                       tag_alarm_section='alarm_section',
                       tag_alarm_value='alarm_value',
                       tag_alarm_index='alarm_index',
                       tag_alert_section='alert_section',
                       tag_alert_value='alert_value',
                       tag_alert_index='alert_index'):

    if not isinstance(run_name, list):
        run_name = [run_name]

    with open(html_name, "w") as html_handle:

        html_handle.write('<html>\n')

        html_handle.write('<style>\n')
        html_handle.write('table, th, td {border: 1px solid black; padding:3px;}\n')
        html_handle.write('.rossa {background-color: rgba(255,0,0,0.5);color: black;;font-size:12;}\n')
        html_handle.write('.gialla {background-color: rgba(255,255,0,0.5);color: black;;font-size:12;}\n')
        html_handle.write('.verde {background-color: rgba(0,255,0,0.5);color: black;;font-size:12;}\n')
        html_handle.write('.azzurro {background-color: rgba(0,255,255,0.5);color: black;;font-size:12;}\n')
        html_handle.write('.grigio {background-color: rgba(128,128,128,0.5);color: black;;font-size:12;}\n')
        html_handle.write('.blu {background-color: rgba(0,0,255,0.5);color: black;font-size:18;}\n')
        html_handle.write('.nero {background-color: rgba(0,0,0,0.9);}\n')
        html_handle.write('.SectionWidth {width:200px;}\n')
        html_handle.write('.SectionWidth1 {width:20px;}\n')
        html_handle.write('.SectionWidth2 {width:10px;}\n')
        html_handle.write('.tbl tr:hover {background-color: lightgray;color: blue;}\n')
        html_handle.write('</style>\n')

        html_handle.write('<table><tr><td><font size=3> Execution Time: </font></td><td><font size=5><b>' +
                          time_exec.strftime(time_format) + ' ' + time_mode + '</b></font></td></tr>\n')

        html_handle.write('<table><tr><td><font size=3> Reference Time: </font></td><td><font size=5><b>' +
                          time_run.strftime(time_format) + ' ' + time_mode + ' </b></font></td></tr>\n')

        html_handle.write('<table class="tbl">\n')
        html_handle.write('<thead>\n')
        html_handle.write('<td class="blu" style="text-align:center; vertical-align:middle"><b>Run Configuration<br>Regione Marche</b></td>\n')
        html_handle.write('<td class="blu" style="text-align:center; vertical-align:middle"><b>State</b></td>\n')
        html_handle.write('<td class="blu" style="text-align:center; vertical-align:middle"><b>TimeStart</b></td>\n')
        html_handle.write('<td class="blu" style="text-align:center; vertical-align:middle"><b>TimeEnd</b></td>\n')
        html_handle.write('<td class="blu" style="text-align:center; vertical-align:middle"><b>TimeElapsed</b></td>\n')
        html_handle.write('<td class="blu" style="text-align:center; vertical-align:middle"><b>Scenarios</b></td>\n')
        html_handle.write('<td class="blu" style="text-align:center; vertical-align:middle"><b>Sections</b></td>\n')
        html_handle.write('<td class="nero SectionWidth2"></td>\n')
        html_handle.write('<td class="blu SectionWidth1" style="text-align:center; vertical-align:middle"><b> OGGI <br> gialla </b></td>\n')
        html_handle.write('<td class="blu SectionWidth" style="text-align:center; vertical-align:middle"><b> OGGI <br> gialla </b></td>\n')
        html_handle.write('<td class="blu SectionWidth1" style="text-align:center; vertical-align:middle"><b> DOMANI <br> gialla </b></td>\n')
        html_handle.write('<td class="blu SectionWidth" style="text-align:center; vertical-align:middle"><b> DOMANI <br> gialla </b></td>\n')
        html_handle.write('<td class="nero SectionWidth2" style="text-align:center; vertical-align:middle"></td>\n')
        html_handle.write('<td class="blu SectionWidth1" style="text-align:center; vertical-align:middle"><b> OGGI <br> rossa </b></td>\n')
        html_handle.write('<td class="blu SectionWidth" style="text-align:center; vertical-align:middle"><b> OGGI <br> rossa </b></td>\n')
        html_handle.write('<td class="blu SectionWidth1" style="text-align:center; vertical-align:middle"><b> DOMANI <br> rossa </b></td>\n')
        html_handle.write('<td class="blu SectionWidth" style="text-align:center; vertical-align:middle"><b> DOMANI <br> rossa </b></td>\n')
        html_handle.write('<td class="nero SectionWidth2" style="text-align:center; vertical-align:middle"></td>\n')
        html_handle.write('</thead>\n')
        html_handle.write('<tbody>\n')

        for run_name_step in run_name:

            run_data = run_summary[run_name_step][tag_summary_data]
            run_info = run_summary[run_name_step][tag_summary_info]

            if 'run_n' in list(run_info.keys()):
                run_n = str(run_info['run_n'])
            else:
                run_n = 'NA'
            if 'run_description' in list(run_info.keys()):
                run_description = str(run_info['run_description'])
            else:
                run_description = 'NA'
            if 'section_n' in list(run_info.keys()):
                section_n = str(run_info['section_n'])
            else:
                section_n = 'NA'

            html_handle.write('<tr>')

            if run_data is not None:

                time_stamp_start = run_info['run_start']
                if time_stamp_start is not None:
                    time_str_start = time_stamp_start.strftime(time_format)
                else:
                    time_str_start = 'NA'
                time_stamp_end = run_info['run_end']
                if time_stamp_end is not None:
                    time_str_end = time_stamp_end.strftime(time_format)
                else:
                    time_str_end = 'NA'
                time_stamp_elapsed = run_info['run_elapsed']
                if time_stamp_elapsed is not None:
                    time_str_elapsed = str(time_stamp_elapsed)
                else:
                    time_str_elapsed = 'NA'

                time_str_end = '2021-02-25 12:49'

                # CASE CONDITIONS
                if time_str_start != 'NA' and time_str_end != 'NA':

                    section_alert_collections = {}
                    section_alarm_collections = {}
                    for id_step, (time_step, data_step) in enumerate(run_data.items()):

                        alert_value_raw = data_step[tag_alert_value]
                        alert_index_raw = data_step[tag_alert_index]
                        alert_section_raw = data_step[tag_alert_section]
                        alarm_value_raw = data_step[tag_alarm_value]
                        alarm_index_raw = data_step[tag_alarm_index]
                        alarm_section_raw = data_step[tag_alarm_section]

                        alert_idx = [i for i, n in enumerate(alert_value_raw) if np.isfinite(n)]
                        alarm_idx = [i for i, n in enumerate(alarm_value_raw) if np.isfinite(n)]

                        alert_value_def = []
                        alert_index_def = []
                        alert_section_def = []
                        for idx in alert_idx:
                            alert_value_def.append(alert_value_raw[idx])
                            alert_index_def.append(alert_index_raw[idx])
                            alert_section_def.append(alert_section_raw[idx])
                        section_alert_collections[id_step] = {}
                        section_alert_collections[id_step][tag_alert_section] = {}
                        section_alert_collections[id_step][tag_alert_section] = alert_section_def
                        section_alert_collections[id_step][tag_alert_value] = {}
                        section_alert_collections[id_step][tag_alert_value] = alert_value_def
                        section_alert_collections[id_step][tag_alert_index] = {}
                        section_alert_collections[id_step][tag_alert_index] = alert_index_def

                        alarm_value_def = []
                        alarm_index_def = []
                        alarm_section_def = []
                        for idx in alarm_idx:
                            alarm_value_def.append(alarm_value_raw[idx])
                            alarm_index_def.append(alarm_index_raw[idx])
                            alarm_section_def.append(alarm_section_raw[idx])
                        section_alarm_collections[id_step] = {}
                        section_alarm_collections[id_step][tag_alarm_section] = {}
                        section_alarm_collections[id_step][tag_alarm_section] = alarm_section_def
                        section_alarm_collections[id_step][tag_alarm_value] = {}
                        section_alarm_collections[id_step][tag_alarm_value] = alarm_value_def
                        section_alarm_collections[id_step][tag_alarm_index] = {}
                        section_alarm_collections[id_step][tag_alarm_index] = alarm_index_def

                    if (alert_section_def.__len__() == 0) and (alarm_section_def.__len__() == 0):

                        html_handle.write('<td class=azzurro style="text-align:center; vertical-align:middle"><b>' + run_description + '</b></td>')
                        html_handle.write('<td class=azzurro style="text-align:center; vertical-align:middle"> COMPLETED  </td>')
                        html_handle.write('<td class=azzurro style="text-align:center; vertical-align:middle">' + time_str_start + ' ' + time_mode + ' </td>')
                        html_handle.write('<td class=azzurro style="text-align:center; vertical-align:middle">' + time_str_end + ' ' + time_mode + ' </td>')
                        html_handle.write('<td class=azzurro style="text-align:center; vertical-align:middle">' + time_str_elapsed + ' </td>')
                        html_handle.write('<td class=azzurro style="text-align:center; vertical-align:middle">' + run_n + '</td>')
                        html_handle.write('<td class=azzurro style="text-align:center; vertical-align:middle">' + section_n + '</td>')
                        html_handle.write('<td class=nero></td>')
                        html_handle.write('<td>-</td>')
                        html_handle.write('<td>-</td>')
                        html_handle.write('<td>-</td>')
                        html_handle.write('<td>-</td>')
                        html_handle.write('<td class=nero></td>')
                        html_handle.write('<td>-</td>')
                        html_handle.write('<td>-</td>')
                        html_handle.write('<td>-</td>')
                        html_handle.write('<td>-</td>')
                        html_handle.write('<td class=nero></td>')

                    else:

                        # CASE COMPLETED
                        html_handle.write('<td class=verde style="text-align:center; vertical-align:middle"><b>' + run_description + '</b></td>')
                        html_handle.write('<td class=verde style="text-align:center; vertical-align:middle"> COMPLETED </td>')
                        html_handle.write('<td class=verde style="text-align:center; vertical-align:middle">' + time_str_start + ' ' + time_mode + ' </td>')
                        html_handle.write('<td class=verde style="text-align:center; vertical-align:middle">' + time_str_end + ' ' + time_mode + ' </td>')
                        html_handle.write('<td class=verde style="text-align:center; vertical-align:middle">' + time_str_elapsed + ' </td>')
                        html_handle.write('<td style="text-align:center; vertical-align:middle">' + run_n + '</td>')
                        html_handle.write('<td style="text-align:center; vertical-align:middle">' + section_n + '</td>')
                        html_handle.write('<td class=nero></td>')

                        for id, data in section_alert_collections.items():
                            section_list = data[tag_alert_section]
                            idx_list = data[tag_alert_index]
                            value_list = data[tag_alert_value]
                            section_n_alert = str(section_list.__len__())

                            alert_group = ''
                            for section_step, idx_step, value_step in zip(section_list, idx_list, value_list):
                                alert_string = section_step + ' :: ' + str(idx_step.strftime('%H')) + ' :: ' + str(value_step)
                                alert_group += alert_string + '\n'
                            alert_group = alert_group.replace("\n", "<br />\n")

                            # section_groups = slice_list(section_list, 5)
                            # section_cell = '\n'.join(' '.join(sub) for sub in section_groups)

                            # alert today
                            if id == 0:
                                if section_list.__len__() > 0:
                                    html_handle.write('<td class=gialla style="text-align:center; vertical-align:middle">' + section_n_alert + '/' + section_n)
                                    html_handle.write('<td class=gialla width:200px>' + alert_group + '</td>')
                                else:
                                    html_handle.write('<td>-</td>')
                                    html_handle.write('<td>-</td>')

                            # alert tomorrow
                            if id == 1:
                                if section_list:
                                    html_handle.write('<td class=gialla style="text-align:center; vertical-align:middle">' + section_n_alert + '/' + section_n)
                                    html_handle.write('<td class=gialla width:200px>' + alert_group + '</td>')
                                else:
                                    html_handle.write('<td>-</td>')
                                    html_handle.write('<td>-</td>')
                                html_handle.write('<td class=nero></td>')

                        for id, data in section_alarm_collections.items():
                            section_list = data[tag_alarm_section]
                            idx_list = data[tag_alarm_index]
                            value_list = data[tag_alarm_value]
                            section_n_alert = str(section_list.__len__())

                            alarm_group = ''
                            for section_step, idx_step, value_step in zip(section_list, idx_list, value_list):
                                alarm_string = section_step + ' :: ' + str(idx_step.strftime('%H')) + ' :: ' + str(value_step)
                                alarm_group += alarm_string + '\n'
                            alert_group = alert_group.replace("\n", "<br />\n")

                            # alert today
                            if id == 0:
                                if section_list:
                                    html_handle.write('<td class=rossa style="text-align:center; vertical-align:middle">' + section_n_alert + '/' + section_n)
                                    html_handle.write('<td class=rossa>' + alarm_group + '</td>')
                                else:
                                    html_handle.write('<td>-</td>')
                                    html_handle.write('<td>-</td>')

                            # alert tomorrow
                            if id == 1:
                                if section_list:
                                    html_handle.write('<td class=rossa style="text-align:center; vertical-align:middle">' + section_n_alert + '/' + section_n)
                                    html_handle.write('<td class=rossa>' + alarm_group + '</td>')
                                else:
                                    html_handle.write('<td>-</td>')
                                    html_handle.write('<td>-</td>')
                                html_handle.write('<td class=nero></td>')

                elif time_str_start != 'NA' and time_str_end == 'NA':

                    # CASE RUNNING
                    html_handle.write('<td class=grigio style="text-align:center; vertical-align:middle"><b>' + run_description + '</b></td>')
                    html_handle.write('<td class=grigio style="text-align:center; vertical-align:middle"> RUNNING ... </td>')
                    html_handle.write('<td class=grigio style="text-align:center; vertical-align:middle">' + time_str_start + ' ' + time_mode + ' </td>')
                    html_handle.write('<td class=grigio style="text-align:center; vertical-align:middle"> NA </td>')
                    html_handle.write('<td class=grigio style="text-align:center; vertical-align:middle"> NA </td>')
                    html_handle.write('<td style="text-align:center; vertical-align:middle">' + run_n + '</td>')
                    html_handle.write('<td style="text-align:center; vertical-align:middle">' + section_n + '</td>')
                    html_handle.write('<td class=nero></td>')
                    html_handle.write('<td>-</td>')
                    html_handle.write('<td>-</td>')
                    html_handle.write('<td>-</td>')
                    html_handle.write('<td>-</td>')
                    html_handle.write('<td class=nero></td>')
                    html_handle.write('<td>-</td>')
                    html_handle.write('<td>-</td>')
                    html_handle.write('<td>-</td>')
                    html_handle.write('<td>-</td>')
                    html_handle.write('<td class=nero></td>')

            else:

                html_handle.write('<td class=rossa style="text-align:center; vertical-align:middle"><b>' + run_description + '</b></td>')
                html_handle.write('<td class=rossa style="text-align:center; vertical-align:middle"> RUN NOT AVAILABLE </td>')
                html_handle.write('<td class=rossa style="text-align:center; vertical-align:middle"> NA </td>')
                html_handle.write('<td class=rossa style="text-align:center; vertical-align:middle"> NA </td>')
                html_handle.write('<td class=rossa style="text-align:center; vertical-align:middle"> NA </td>')
                html_handle.write('<td style="text-align:center; vertical-align:middle"> NA </td>')
                html_handle.write('<td style="text-align:center; vertical-align:middle"> NA </td>')
                html_handle.write('<td class=nero></td>')
                html_handle.write('<td>-</td>')
                html_handle.write('<td>-</td>')
                html_handle.write('<td>-</td>')
                html_handle.write('<td>-</td>')
                html_handle.write('<td class=nero></td>')
                html_handle.write('<td>-</td>')
                html_handle.write('<td>-</td>')
                html_handle.write('<td>-</td>')
                html_handle.write('<td>-</td>')
                html_handle.write('<td class=nero></td>')

            html_handle.write('</tr>')

        html_handle.write('</tbody>')
        html_handle.write('</html>')

# -------------------------------------------------------------------------------------
