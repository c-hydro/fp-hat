#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HAT - DataPublisher HMC NRT - LOCAL'
script_version="1.5.0"
script_date='2019/03/04'

# Python virtual environment information
fp_folder_libs='/home/fabio/Documents/Work_Area/Code_Development/Library/virtualenv_python3/'
fp_env_libs='virtualenv_python3'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/home/fabio/Documents/Work_Area/Code_Development/Workspace/PyCharm_Workspace/hat-master/apps//HAT_DataPublisher_HMC_NRT.py'
settings_file='/home/fabio/Documents/Work_Area/Code_Development/Workspace/PyCharm_Workspace/hat-master/apps/hat_datapublisher_hmc_nrt_configuration_example_generic.json'
script_folder='/home/fabio/Documents/Work_Area/Code_Development/Workspace/PyCharm_Workspace/hat-master/'
stats_folder='/home/fabio/Desktop/PyCharm_Workspace/hat-master/bin/local/'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y%m%d%H00")
time_now='201910221500' #'201905131000' # DEBUG 
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
python3 -m cProfile -o stats.binary $script_file -settings_file $settings_file -time $time_now

cprofilev -f ${stats_folder}stats.binary
gprof2dot -f pstats ${stats_folder}stats.binary | dot -Tsvg -o profile.svg

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

