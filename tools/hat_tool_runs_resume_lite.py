"""
HAT Analysis Tool - Run recap and warning summary lite

__date__ = '20230831'
__version__ = '1.3.0'
__author__ =
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',

__library__ = 'HAT'

General command line:
python3 hyde_downloader_nwp_gfs_ftp.py -settings_file configuration.json -time YYYY-MM-DD HH:MM

Version(s):
20230831 (1.3.0) --> Add support for hystorical runs 
20221005 (1.2.0) --> Add support for conditional probabilistic runs
20210602 (1.1.0) --> Add support to netrc credential file
20210511 (1.0.0) --> Beta release for floodProofs-HSNFEWS Guyana
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import logging
from argparse import ArgumentParser
from datetime import datetime, timezone, timedelta
from copy import deepcopy
import pandas as pd
import geopandas as gpd
import pygsheets
import os
import time
import json
import numpy as np
import smtplib
import matplotlib.pyplot as plt
import xlsxwriter
from email.message import EmailMessage
import netrc
import pytz
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HAT ANALYSIS TOOL - RUN RECAP LITE'
alg_version = '1.3.0'
alg_release = '2023-08-31'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'


# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Script Main
def main():
    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_json(alg_settings)

    # Set algorithm logging
    os.makedirs(data_settings['data']['log']['folder'], exist_ok=True)
    set_logging(
        logger_file=os.path.join(data_settings['data']['log']['folder'], data_settings['data']['log']['filename']))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()

    time_run = datetime.strptime(alg_time, '%Y-%m-%d %H:%M')
    empty_template = data_settings["algorithm"]["template"]
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Load static data
    logging.info(" --> Open static section file ")

    logging.info(" ---> File type: " + data_settings["data"]["static"]["format"])
    section_df = read_section(section_path=data_settings["data"]["static"]["section_file"], fmt='shapefile')
    logging.info(" --> Open static section file... DONE ")
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Check meteo models availability
    logging.info(" --> Input data analysis... ")

    list_model_check = [i for i in data_settings["data"]["dynamic"]["models"].keys() if
                        data_settings["data"]["dynamic"]["models"][i]["actions"]["check"]]
    logging.info(" ---> Models to check: " + ','.join(list_model_check))

    models_check = {}
    for model in list_model_check:
        logging.info(" ----> Check model: " + data_settings["data"]["dynamic"]["models"][model]["full_name"])
        file_template = os.path.join(data_settings["data"]["dynamic"]["models"][model]["folder"],
                                     data_settings["data"]["dynamic"]["models"][model]["file_name"])
        if data_settings["data"]["dynamic"]["models"][model]["type"] == "realtime":
            if "hours_delay" in data_settings["data"]["dynamic"]["models"][model]:
                delay = data_settings["data"]["dynamic"]["models"][model]["hours_delay"]
            else:
                delay = 24
                logging.warning("WARNING! Delay not specified for " + model + "! Dealay set to 24 hours!")
            models_check[data_settings["data"]["dynamic"]["models"][model]["full_name"]] = check_last_realtime_model(file_template, empty_template, length_check=delay)
        elif data_settings["data"]["dynamic"]["models"][model]["type"] == "forecast":
            filled_template = fill_time_template(empty_template, time_run)
            file_now = file_template.format(**filled_template)
            try:
                eta = data_settings["data"]["dynamic"]["models"][model]["eta"]
                eta_value = datetime(time_run.year, time_run.month, time_run.day, int(eta.split(":")[0]), int(eta.split(":")[1]))
            except:
                eta_value = None

            models_check[data_settings["data"]["dynamic"]["models"][model]["full_name"]] = check_forecast_availability(file_now, eta_value)

    logging.info(" --> Input data analysis... DONE ")
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Check hydro model runs
    # Check the presence of conditioned probabilistic runs
    logging.info(" --> Check presence of conditional probabilistic runs to monitor... ")
    list_of_conditional_runs = [i for i in data_settings["data"]["dynamic"]["runs"].keys() if data_settings["data"]["dynamic"]["runs"][i]["actions"]["check"] and
                       data_settings["data"]["dynamic"]["runs"][i]["type"] == "probabilistic_conditional"]
    list_of_full_name_conditional_runs = [data_settings["data"]["dynamic"]["runs"][i]["full_name"] for i in
                                 data_settings["data"]["dynamic"]["runs"].keys() if data_settings["data"]["dynamic"]["runs"][i]["actions"]["check"] and
                                 data_settings["data"]["dynamic"]["runs"][i]["type"] == "probabilistic_conditional"]

    for run, run_full_name in zip(list_of_conditional_runs, list_of_full_name_conditional_runs):
        condition_active_file = data_settings["data"]["dynamic"]["runs"][run]["condition_active_file"].format(**filled_template)
        condition_notactive_file = data_settings["data"]["dynamic"]["runs"][run]["condition_notactive_file"].format(**filled_template)
        if check_conditional_probabilistic_runs(condition_active_file, condition_notactive_file) == "not active":
            data_settings["data"]["dynamic"]["runs"][run]["actions"]["check"] = False
        elif check_conditional_probabilistic_runs(condition_active_file, condition_notactive_file) == "unknown":
            logging.warning("WARNING! Status of conditional probabilistic run for domain " + run + " is not valid! No proper lock file found!")
    logging.info(" --> Check presence of conditional probabilistic runs to monitor... DONE!")

    # Check status of hydro models run
    list_runs_check = [i for i in data_settings["data"]["dynamic"]["runs"].keys() if
                       data_settings["data"]["dynamic"]["runs"][i]["actions"]["check"]]
    list_full_name_runs_check = [data_settings["data"]["dynamic"]["runs"][i]["full_name"] for i in data_settings["data"]["dynamic"]["runs"].keys() if
                       data_settings["data"]["dynamic"]["runs"][i]["actions"]["check"]]
    logging.info(" ---> Runs to check: " + ','.join(list_runs_check))

    runs_check = pd.DataFrame(index=list_full_name_runs_check, columns=['Run status', 'Time start','Time end','Expected end','Run check'])

    for run, run_full_name in zip(list_runs_check, list_full_name_runs_check):
        logging.info(" ----> Check run: " + run_full_name)

        if "historical" in data_settings["data"]["dynamic"]["runs"][run]["type"]:
            filled_template = fill_time_template(empty_template, time_run - timedelta(hours=int(data_settings["data"]["dynamic"]["runs"][run]["time_delay_h"])))
        else:
            filled_template = fill_time_template(empty_template, time_run)
        filled_template["run_name"] = run

        start_lock_file = data_settings["data"]["dynamic"]["runs"][run]["start_lock_file"].format(**filled_template)
        end_lock_file = data_settings["data"]["dynamic"]["runs"][run]["end_lock_file"].format(**filled_template)
        runs_check.loc[run_full_name]['Run status'], runs_check.loc[run_full_name]['Time start'], runs_check.loc[run_full_name]['Time end'], time_end_value = check_run_state(start_lock_file, end_lock_file)
        try:
            eta = data_settings["data"]["dynamic"]["runs"][run]["eta"]
            eta_value = datetime(time_run.year, time_run.month, time_run.day, int(eta.split(":")[0]), int(eta.split(":")[1]), tzinfo=pytz.UTC)
            runs_check.loc[run_full_name]['Expected end'] = eta_value.strftime("%Y-%m-%d %H:%M")
        except:
            if "historical" in data_settings["data"]["dynamic"]["runs"][run]["type"]:
                runs_check.loc[run_full_name]['Expected end'] = time_run.strftime("%Y-%m-%d %H:%M")
            else:
                eta_value = None
                runs_check.loc[run_full_name]['Expected end'] = 'UNKNOWN'

        runs_check.loc[run_full_name]['Run check'] = check_run_condition(time_end_value, eta_value)

    logging.info(" --> Model run analysis... DONE")
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Check sections warning
    if data_settings["algorithm"]["flags"]["check_warning"]:

        # Initialise data
        logging.info(" --> Compile warning report... ")
        list_runs_warning = [i for i in data_settings["data"]["dynamic"]["runs"].keys() if
                             data_settings["data"]["dynamic"]["runs"][i]["actions"]["warning"]]

        df_values = pd.DataFrame(index= section_df["BASIN"] + " " + section_df["SEC_NAME"], columns=list_runs_warning)
        df_level = pd.DataFrame(data='k', index= section_df["BASIN"] + " " + section_df["SEC_NAME"], columns=list_runs_warning)
        df_threshold = pd.DataFrame(index= section_df["BASIN"] + " " + section_df["SEC_NAME"],
                                    columns=["yellow_th", "orange_th"])

        if data_settings["data"]["dynamic"]["outcome"]["warning"]["exclude_obs"]:
            time_min = time_run
        else:
            time_min = datetime.datetime(1970, 8, 1, 0, 0)

        # Loop trough models and sections
        for run in list_runs_warning:
            logging.info(" ---> Analyse output of model " + data_settings["data"]["dynamic"]["runs"][run]["full_name"])
            df_made = False
            if "historical" in data_settings["data"]["dynamic"]["runs"][run]["type"]:
                filled_template = fill_time_template(empty_template, time_run - timedelta(
                    hours=int(data_settings["data"]["dynamic"]["runs"][run]["time_delay_h"])))
            else:
                filled_template = fill_time_template(empty_template, time_run)
            filled_template["run_name"] = run
            collection_path = data_settings["data"]["dynamic"]["runs"][run]["collection_path"].format(**filled_template)
            if os.path.isdir(collection_path):
                for section, basin in zip(section_df["SEC_NAME"].values, section_df["BASIN"].values):
                    filled_template["section_name"] = section
                    filled_template["section_basin"] = basin
                    run_results = os.path.join(collection_path,
                                               data_settings["data"]["dynamic"]["runs"][run]["collection_name"]).format(
                        **filled_template)
                    if os.path.isfile(run_results):
                        results = read_file_json(run_results)
                        yellow_th = float(results["section_discharge_thr_alert"])
                        if yellow_th == -9999:
                            yellow_th = 9999999
                        orange_th = float(results["section_discharge_thr_alarm"])
                        if orange_th == -9999:
                            orange_th = 9999999
                        try:
                            red_th = float(results["section_discharge_thr_emergency"])
                        except:
                            red_th = 9999999
                        if red_th == -9999:
                            red_th = 9999999
                        if df_threshold.loc[basin + ' ' + section]["yellow_th"] is np.nan:
                            df_threshold.loc[basin + ' ' + section]["yellow_th"] = yellow_th
                            df_threshold.loc[basin + ' ' + section]["orange_th"] = orange_th
                            df_threshold.loc[basin + ' ' + section]["red_th"] = red_th
                        if results['run_mode'] == 'deterministic':
                            if not df_made:
                                time_index = [datetime.strptime(i, "%Y-%m-%d %H:%M") for i in
                                              results["time_period"].split(",")]
                                df_out = pd.DataFrame(index=time_index, columns=['value'])
                                df_made = True
                            df_out['value'] = [float(i) for i in results["time_series_discharge_simulated"].split(',')]
                            max_value = max(df_out[time_min:]['value'])

                        elif results['run_mode'] == 'probabilistic_ensemble':
                            if not df_made:
                                time_index = [datetime.strptime(i, "%Y-%m-%d %H:%M") for i in results["time_period"].split(",")]
                                df_out = pd.DataFrame(index=time_index, columns=results["run_var"].split(','))
                                df_made = True
                            for ens in results["run_var"].split(','):
                                df_out[ens] = [float(i) for i in results['time_series_discharge_simulated_' + ens].split(',')]
                            max_value = max(df_out[time_min:].values.flatten())

                        assign_warning(max_value, red_th, orange_th, yellow_th, basin + ' ' + section, run, df_values, df_level)

                    else:
                        logging.warning(" ---> WARNING! Collection of section " + basin + ' ' + section + " not found!")
                        continue
                logging.info(" ---> Analysing output of model " + data_settings["data"]["dynamic"]["runs"][run][
                    "full_name"] + "...DONE")
            else:
                logging.warning(" ---> WARNING! Outputs of model " + data_settings["data"]["dynamic"]["runs"][run][
                    "full_name"] + " not found!")


        section_df["max_warning_lev"] = 'k'

        for basin,sect in zip(section_df["BASIN"], section_df["SEC_NAME"]):
            if any(df_level.loc[basin + ' ' + sect] == 'r'):
                section_df.loc[(section_df["BASIN"]==basin) & (section_df["SEC_NAME"]==sect),"max_warning_lev"] = 'r'
            elif any(df_level.loc[basin + ' ' + sect] == 'tab:orange'):
                section_df.loc[(section_df["BASIN"]==basin) & (section_df["SEC_NAME"]==sect),"max_warning_lev"] = 'tab:orange'
            elif any(df_level.loc[basin + ' ' + sect] == 'y'):
                section_df.loc[(section_df["BASIN"]==basin) & (section_df["SEC_NAME"]==sect),"max_warning_lev"] = 'y'
            elif all(df_level.loc[basin + ' ' + sect] == 'k'):
                section_df.loc[(section_df["BASIN"]==basin) & (section_df["SEC_NAME"]==sect),"max_warning_lev"] = 'k'
            else:
                section_df.loc[(section_df["BASIN"]==basin) & (section_df["SEC_NAME"]==sect),"max_warning_lev"] = 'g'

        df_values = df_values.dropna(axis=0, how='all').dropna(axis=1, how='all')
        df_level = df_level.loc[df_values.index][df_values.columns]

        warning_report = os.path.join(data_settings["data"]["dynamic"]["outcome"]["warning"]["folder"], data_settings["data"]["dynamic"]["outcome"]["warning"]["file_name"]).format(**filled_template)
        warning_figure = os.path.join(data_settings["data"]["dynamic"]["outcome"]["warning"]["folder"], "warning_figure_" + time_run.strftime("%Y%m%d%H") + '.png').format(**filled_template)
        os.makedirs(data_settings["data"]["dynamic"]["outcome"]["warning"]["folder"].format(**filled_template), exist_ok=True)

        admin_border = gpd.read_file(data_settings["data"]["static"]["admin_border"])
        river_network = gpd.read_file(data_settings["data"]["static"]["river_network"])
        plt.figure()
        base = admin_border.plot(color='white', edgecolor='black', zorder=0)
        river_network.plot(ax=base,edgecolor='blue', linewidth=0.2, zorder=1)
        for color in np.unique(section_df['max_warning_lev']):
            section_df.loc[section_df['max_warning_lev']==color].plot(ax=base, color=color, markersize=5, zorder=2)
        plt.title(" Multimodel worst warning level\n Run H" + time_run.strftime("%Y-%m-%d %H"))
        plt.savefig(warning_figure, dpi=300)

        with pd.ExcelWriter(warning_report, engine='xlsxwriter') as writer:
            logging.info(" ---> Write warning report")
            df_values.style.apply(lambda x: df_level.applymap(apply_color), axis=None).to_excel(writer)

            worksheet = writer.sheets['Sheet1']
            worksheet.insert_image('F1', warning_figure)

        logging.info(" --> Compile warning report...DONE ")

    else:
        warning_report = None

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Check reporting
    logging.info(" --> Write check report... ")

    logging.info(" ---> Write check report file... ")
    report_folder_now = data_settings["data"]["dynamic"]["outcome"]["check"]["folder"].format(**filled_template)
    report_file_now = data_settings["data"]["dynamic"]["outcome"]["check"]["file_name"].format(**filled_template)
    os.makedirs(report_folder_now, exist_ok=True)
    write_report(report_folder_now, report_file_now, models_check, runs_check,
                 data_settings["algorithm"]["general"]["operational_chain_name"], time_run)
    logging.info(" ---> Write check report file... DONE")

    if data_settings["algorithm"]["flags"]["public_check_spreadsheet"]:
        logging.info(" --> Update web check page... ")
        public_online_gdrive(data_settings["data"]["dynamic"]["outcome"]["check"]["url"],
                            data_settings["data"]["dynamic"]["outcome"]["check"]["api_key"],
                             models_check, runs_check, time_run)
        logging.info(" --> Update web check page... DONE")

    if data_settings["algorithm"]["flags"]["send_email"]:
        logging.info(" --> Send email... ")
        email_settings=data_settings["data"]["dynamic"]["outcome"]["email"]
        if not all([email_settings['user'], email_settings['pwd']]):
            netrc_handle = netrc.netrc()
            try:
                email_settings['user'], _, email_settings['pwd'] = netrc_handle.authenticators(email_settings['smtp_server'])
            except:
                logging.error(' --> Valid netrc authentication file not found in home directory! Generate it or provide user and password in the settings!')
                raise FileNotFoundError('Verify that your .netrc file exists in the home directory and that it includes proper smtp credentials!')
        with open(os.path.join(report_folder_now, report_file_now)) as file:
            text_mail = file.read()
        send_email(email_settings, text_mail, data_settings["algorithm"]["flags"]["send_warning_report"], warning_report)
        logging.info(" --> Send email... DONE")
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    time_elapsed = round(time.time() - start_time, 1)

    logging.info(' ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> TIME ELAPSED: ' + str(time_elapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function to assign color to DataFrame cells
def apply_color(x):
    if x == 'y':
        return 'background-color: yellow'
    elif x == 'tab:orange':
        return 'background-color: #FFA500'
    elif x=='r':
        return 'background-color: red'
    else:
        return 'background-color: white'

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function for assigning warning levels according to thresholds
def assign_warning(max_value, red_th, orange_th, yellow_th, section, run, df_values, df_level):
    if max_value == 0:
        df_values.loc[section, run] = np.nan
        df_level.loc[section, run] = 'g'
    elif max_value >= red_th:
        df_values.loc[section, run] = max_value
        df_level.loc[section, run] = 'r'
    elif max_value > orange_th:
        df_values.loc[section, run] = max_value
        df_level.loc[section, run] = 'tab:orange'
    elif max_value > yellow_th:
        df_values.loc[section, run] = max_value
        df_level.loc[section, run] = 'y'
    elif max_value > 0:
        df_values.loc[section, run] = np.nan
        df_level.loc[section, run] = 'g'
    else:
        df_values.loc[section, run] = np.nan
        df_level.loc[section, run] = 'k'

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function for sending email
def send_email(mail_dict, text_mail, attach_warning, warning_report):
    msg = EmailMessage()

    if attach_warning == True:
        msg.set_content(text_mail + '\n Please, find attached the warnings summary.' + mail_dict["other_infos"])
    else:
        msg.set_content(text_mail + mail_dict["other_infos"])

    msg.set_content(text_mail + mail_dict["other_infos"])
    msg['Subject'] = mail_dict['subject']
    msg['To'] = mail_dict['recipient']
    msg['From'] = mail_dict['sender']

    if attach_warning == True:
        with open(warning_report, 'rb') as fh:
            attachment = fh.read()
            msg.add_related(attachment, maintype='application', subtype='xlsx', filename=os.path.basename(warning_report))

    session = smtplib.SMTP(mail_dict['smtp_server'], mail_dict['smtp_port'])
    session.ehlo()
    session.starttls()
    session.login(mail_dict['user'], mail_dict['pwd'])
    session.send_message(msg)
    session.quit()

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function to write a recup report
def write_report(out_folder, out_name, models_check, runs_check, op_chain_name, time_run):
    with open(os.path.join(out_folder, out_name), 'w') as report_file:
        report_file.write('============================================================\n')
        report_file.write(op_chain_name + ' RECAP - Time: ' + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M") + "\n")
        report_file.write('Model reference time: ' + time_run.strftime("%Y-%m-%d %H:%M") + "\n")
        report_file.write('============================================================\n')
        report_file.write(' \n')
        report_file.write(' --> Meteo model monitoring \n')
        for key in models_check:
            report_file.write(key + ': ' + models_check[key] + "\n")
        report_file.write(' \n')
        report_file.write(' --> Operational chains check \n')
        for key in runs_check.index:
            report_file.write(key + ': ' + runs_check.loc[key]["Run status"] + " - " + runs_check.loc[key]["Run check"] + "\n")
        report_file.write('============================================================')

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function to public results of check on a google spreadsheet
def public_online_gdrive(url,api_key, models_check, runs_check, time_run):
    gc = pygsheets.authorize(service_file=api_key)

    sh = gc.open_by_url(url)

    wks = sh[0]
    #wks.insert_rows(1,300)
    wks.delete_rows(1,100)
    wks.insert_rows(1,100)
    wks.clear()

    # Header
    wks.cell('A1').set_text_format('bold', True).value = "RUN TIME (UTC)"
    wks.cell('B1').value = time_run.strftime("%Y-%m-%d %H:%M")
    wks.cell('C1').set_text_format('bold', True).value = "CHECK TIME (UTC)"
    wks.cell('D1').value = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    last_header_row = 1

    # Meteo models
    wks.cell('A' + str(last_header_row+2)).set_text_format('bold', True).value = "METEO MODELS"
    wks.set_dataframe(pd.DataFrame.from_dict(models_check, orient='index'), (last_header_row + 3, 1), copy_index=True, copy_head=False)
    last_meteo_row = last_header_row + 1 + len(models_check)

    wks.add_conditional_formatting('B' + str(last_header_row + 3), 'B' + str(last_header_row + 3 + len(models_check) -1),
                                   "TEXT_NOT_CONTAINS", format={'backgroundColor': {'green': 0.1, 'red': 0.95, 'blue': 0.05}},
                                   condition_values=["OK"])
    wks.add_conditional_formatting('B' + str(last_header_row + 3), 'B' + str(last_header_row + 3 + len(models_check) -1),
                                   "TEXT_CONTAINS", format={'backgroundColor': {'green': 0.75, 'red': 0.1, 'blue': 0.1}},
                                   condition_values=["OK"])

    # Hydro models
    wks.cell('A' + str(last_meteo_row + 3)).set_text_format('bold', True).value = "HYDROLOGICAL MODELS"
    wks.cell('A' + str(last_meteo_row + 4)).set_text_format('bold', True).set_text_format('italic', True).value = "Run name"
    wks.cell('B' + str(last_meteo_row + 4)).set_text_format('bold', True).set_text_format('italic', True).value = "Run status"
    wks.cell('C' + str(last_meteo_row + 4)).set_text_format('bold', True).set_text_format('italic', True).value = "Run start (UTC)"
    wks.cell('D' + str(last_meteo_row + 4)).set_text_format('bold', True).set_text_format('italic', True).value = "Run end (UTC)"
    wks.cell('E' + str(last_meteo_row + 4)).set_text_format('bold', True).set_text_format('italic', True).value = "Expected end (UTC)"
    wks.cell('F' + str(last_meteo_row + 4)).set_text_format('bold', True).set_text_format('italic', True).value = "Run check"
    wks.set_dataframe(runs_check, (last_meteo_row + 5, 1), copy_index=True, copy_head=False)

    wks.add_conditional_formatting('F' + str(last_meteo_row + 5), 'F' + str(last_meteo_row + 5 + len(runs_check)),
                                   "TEXT_CONTAINS", format={'backgroundColor': {'green': 0.75, 'red': 0.1, 'blue': 0.1}},
                                   condition_values=["OK"])
    wks.add_conditional_formatting('F' + str(last_meteo_row + 5), 'F' + str(last_meteo_row + 5 + len(runs_check)),
                                   "TEXT_CONTAINS", format={'backgroundColor': {'green': 0.7, 'red': 0.7, 'blue': 0.7}},
                                   condition_values=["UNKNOWN"])
    wks.add_conditional_formatting('F' + str(last_meteo_row + 5), 'F' + str(last_meteo_row + 5 + len(runs_check)),
                                   "TEXT_CONTAINS", format={'backgroundColor': {'green': 0.1, 'red': 0.95, 'blue': 0.05}},
                                   condition_values=["WARNING"])
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function to check the run END lockfile
def check_run_state(start_lock_file, end_lock_file):
    if os.path.isfile(start_lock_file) and os.path.isfile(end_lock_file):
        out_string = "Has run"
        time_start = datetime.utcfromtimestamp(os.stat(start_lock_file).st_mtime).strftime("%Y-%m-%d %H:%M")
        time_end_value = datetime.utcfromtimestamp(os.stat(end_lock_file).st_mtime)
        time_end = time_end_value.strftime("%Y-%m-%d %H:%M")
    elif os.path.isfile(start_lock_file) and not os.path.isfile(end_lock_file):
        out_string = "Is running"
        time_start = datetime.utcfromtimestamp(os.stat(start_lock_file).st_mtime).strftime("%Y-%m-%d %H:%M")
        time_end = " "
        time_end_value = None
    elif not os.path.isfile(start_lock_file) and not os.path.isfile(end_lock_file):
        out_string = "Has not run"
        time_start = " "
        time_end = " "
        time_end_value = None
    else:
        out_string = "Unknown condition"
        time_start = " "
        time_end = " "
        time_end_value = None

    return out_string, time_start, time_end, time_end_value
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
def check_run_condition(time_end_value, eta_value):
    time_now_utc = datetime.now(timezone.utc)

    if time_end_value is not None:
        status = "OK"

    elif eta_value is None:
        status = "UNKNOWN"

    elif eta_value < time_now_utc:
        status = "WARNING"

    elif eta_value > time_now_utc:
        status = "OK, wait for scheduled time"

    else:
        status = "OK"

    return status

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function to check the contitional probabilistic runs
def check_conditional_probabilistic_runs(active_lock, notactive_lock):
    if os.path.isfile(active_lock) and not os.path.isfile(notactive_lock):
        status = "active"
    elif os.path.isfile(notactive_lock) and not os.path.isfile(active_lock):
        status = "not active"
    else:
        status = "unknown"
    return status

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function to fill a time template
def fill_time_template(empty_template, time_now):
    filled_template = {}
    for k in empty_template.keys():
        filled_template[k] = time_now.strftime(empty_template[k])
    return filled_template

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function to check the time-step of the last real-time meteo model
def check_last_realtime_model(file_template, empty_template, length_check=24, freq_check="H"):
    time_to_check = pd.date_range(datetime.now(timezone.utc), periods=length_check, freq="-1" + freq_check)
    last_available = None
    for time_check in time_to_check:
        filled_template = fill_time_template(empty_template, time_check)
        file_now = file_template.format(**filled_template)
        if os.path.isfile(file_now):
            last_available = time_check
            break

    if not last_available is None:
        out_string = "OK! Last available data: " + last_available.strftime("%Y-%m-%d %H:00")
    else:
        out_string = "WARNING! Last available data more than " + str(length_check) + " " + freq_check + " ago"

    return out_string

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function to check the availability of a forecast file
def check_forecast_availability(file_now, eta_value):
    time_now_utc = datetime.now() #(timezone.utc)

    if os.path.isfile(file_now):
        last_mod = os.path.getmtime(file_now)
        out_string = "OK! Model is available at " + datetime.utcfromtimestamp(last_mod).strftime("%Y-%m-%d %H:%M")
    else:
        if eta_value is None:
            out_string = "WARNING! Model is not available"
        elif eta_value < time_now_utc:
            out_string = "WARNING! Model is not available"
        else:
            out_string = "OK! Model is not available yet"

    return out_string

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to read file json
def read_file_json(file_name):
    env_ws = {}
    for env_item, env_value in os.environ.items():
        env_ws[env_item] = env_value

    with open(file_name, "r") as file_handle:
        json_block = []
        for file_row in file_handle:

            for env_key, env_value in env_ws.items():
                env_tag = '$' + env_key
                if env_tag in file_row:
                    env_value = env_value.strip("'\\'")
                    file_row = file_row.replace(env_tag, env_value)
                    file_row = file_row.replace('//', '/')

            # Add the line to our JSON block
            json_block.append(file_row)

            # Check whether we closed our JSON block
            if file_row.startswith('}'):
                # Do something with the JSON dictionary
                json_dict = json.loads(''.join(json_block))
                # Start a new block
                json_block = []

    return json_dict

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_settings, alg_time

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to set logging information
def set_logging(logger_file='log.txt', logger_format=None):
    if logger_format is None:
        logger_format = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

    # Remove old logging file
    if os.path.exists(logger_file):
        os.remove(logger_file)

    # Set level of root debugger
    logging.root.setLevel(logging.INFO)

    # Open logging basic configuration
    logging.basicConfig(level=logging.INFO, format=logger_format, filename=logger_file, filemode='w')

    # Set logger handle
    logger_handle_1 = logging.FileHandler(logger_file, 'w')
    logger_handle_2 = logging.StreamHandler()
    # Set logger level
    logger_handle_1.setLevel(logging.INFO)
    logger_handle_2.setLevel(logging.INFO)
    # Set logger formatter
    logger_formatter = logging.Formatter(logger_format)
    logger_handle_1.setFormatter(logger_formatter)
    logger_handle_2.setFormatter(logger_formatter)
    # Add handle to logging
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Read section file
def read_section(section_path=None, column_labels=None, sep="\s+", column_names=["HMC_X", "HMC_Y", "BASIN", "SEC_NAME"],
                 fmt='tabular'):
    if not os.path.isfile(section_path):
        logging.error(' ---> ERROR! Section file not found!')
        raise IOError("Verify section file path:" + section_path)

    if fmt == 'tabular':
        section_df = pd.read_csv(section_path, sep=sep, header=None)

        if len(section_df.columns) > len(column_names):
            logging.warning(' ---> WARNING! Section files has ' + str(len(section_df.columns)) + ' columns!')
            logging.info(' ---> First  ' + str(len(column_names)) + ' columns are interpreted as ' + ','.join(
                column_names) + ', others are ignored!')
            column_names.extend([''] * (len(section_df.columns) - len(column_names)))
        if len(section_df.columns) < len(column_names):
            logging.error(' ---> ERROR! Section files has ' + str(
                len(section_df.columns)) + ' columns, cannot interpret as standard HMC section file!')
            raise IOError("Verify your section file!")

        section_df.columns = column_names

    elif fmt == 'shapefile':
        section_df = gpd.read_file(section_path)

    return section_df

# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------