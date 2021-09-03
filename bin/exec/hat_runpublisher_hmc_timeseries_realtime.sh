#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HAT - Run Publisher - Time Series - REALTIME'
script_version="1.6.0"
script_date='2021/07/27'

# Python virtual environment information
virtualenv_folder='/hydro/library/fp_libs_python3/'
virtualenv_name='virtualenv_python3'
script_folder='/hydro/library/fp_package_hat/'

# Execution example:
# python HAT_RunPublisher_HMC_TimeSeries.py -settings_file hat_runpublisher_hmc_timeseries.json -time "2020-11-02 12:00"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
flag_run_publisher=true
script_file_publisher='/hydro/library/fp_package_hat/apps/Analyzer_Datasets/time_series/HAT_RunPublisher_HMC_TimeSeries.py'
settings_file_publisher='/hydro/fp_tools_postprocessing/analyzer_datasets/hat_runpublisher_hmc_timeseries_realtime.json'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
# time_now='2021-02-18 06:00' # DEBUG 
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Add to path python virtual environment
export PATH=$virtualenv_folder/bin:$PATH
source activate $virtualenv_name

# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ===> EXECUTION ..."

time_now=$(date -d "$time_now" +'%Y-%m-%d %H:00')
# ----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Info data publisher start
echo " ====> HAT DATA PUBLISHER ... "

# Define command-line
echo " =====> COMMAND LINE: " python $script_file_publisher -settings_file $settings_file_publisher -time "$time_now"

# Run python script (using setting and time)
if $flag_run_publisher; then
	python $script_file_publisher -settings_file $settings_file_publisher -time "$time_now"
	echo " ====> HAT DATA PUBLISHER ... DONE"
else
	echo " ====> HAT DATA PUBLISHER ... SKIPPED. MODULE NOT ACTIVATED"
fi
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script end
echo " ===> EXECUTION ... DONE"
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	

