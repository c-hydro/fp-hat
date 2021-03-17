#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HAT - DataRunner HMC NRT - HISTORY'
script_version="1.0.0"
script_date='2019/03/25'

# Python virtual environment information
fp_folder_libs=$HOME/fp_libs_python
fp_env_libs='fp_env_python'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file_manager='/home/dpc-marche/library/hat-master/apps/HAT_RunOrganizer_HMC_NRT.py'
setting_file_manager='/home/dpc-marche/library/hat-master/apps/hat_datamanager_hmc_nrt_configuration_server_history.json'
script_file_publisher='/home/dpc-marche/library/hat-master/apps/HAT_RunPublisher_HMC_NRT.py'
setting_file_publisher='/home/dpc-marche/library/hat-master/apps/hat_datapublisher_hmc_nrt_configuration_server_history.json'
script_folder='/home/dpc-marche/library/hat-master/'

# Get information (-u to get gmt time)
#time_now=$(date -u +"%Y%m%d%H00")
time_now='201907071600' # DEBUG 
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

# Run python data manager script (using setting and time)
echo " ====> DATA MANAGER ... "
python3 $script_file_manager -settingfile $setting_file_manager -time $time_now
echo " ====> DATA MANAGER ... DONE"

# Run python data publisher script (using setting and time)
echo " ====> DATA PUBLISHER ... "
python3 $script_file_publisher -settingfile $setting_file_publisher -time $time_now
echo " ====> DATA PUBLISHER ... DONE "


# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

