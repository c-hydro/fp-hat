#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HAT - Run Analyzer HMC - REALTIME'
script_version="1.0.0"
script_date='2020/06/15'

# Python virtual environment information
fp_folder_libs=$HOME/fp_libs_python
fp_env_libs='fp_env_python'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/home/dpc-marche/library/hat-run_analyzer/HAT_RunAnalyzer_HMC_Main.py'
setting_file='/home/dpc-marche/library/hat-run_analyzer/hat_runanalyzer_hmc_configuration_realtime.json'
script_folder='/home/dpc-marche/library/hat-run_analyzer/'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y%m%d%H00")
# time_now='201807230000' # DEBUG 
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Add to path python virtual environment
export PATH="$fp_folder_libs/bin:$PATH"
source activate $fp_env_libs

# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."

# Run python script (using setting and time)
python3 $script_file -settings_file $setting_file -time $time_now

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

