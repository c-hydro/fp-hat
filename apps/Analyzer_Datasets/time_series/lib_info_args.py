"""
Library Features:

Name:          lib_info_args
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210408'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import pandas as pd
#######################################################################################

# -------------------------------------------------------------------------------------
# Time information
time_type = 'GMT'  # 'GMT', 'local'
time_units = 'days since 1858-11-17 00:00:00'
time_calendar = 'gregorian'
time_format_datasets = "%Y%m%d%H%M"
time_format_algorithm = '%Y-%m-%d %H:%M'
time_machine = pd.Timestamp.now

# Logging information
logger_name = 'hat_publisher_timeseries_logger'
logger_file = 'hat_publisher_timeseries.txt'
logger_handle = 'file'  # 'file' or 'stream'
logger_format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)-80s %(filename)s:[%(lineno)-6s - %(funcName)-20s()] '

# Definition of wkt for projections
proj_wkt = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
proj_epsg = 'EPSG:4326'

# Definition of zip extension
zip_extension = '.gz'
# -------------------------------------------------------------------------------------
