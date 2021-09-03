"""
Library Features:

Name:          lib_graph_map_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210903'
Version:       '1.0.0'
"""
#######################################################################################
# Libraries
import os
import json
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to read map table
def read_map_table(file_name):
    if os.path.exists(file_name):
        with open(file_name) as file_handle:
            file_table = json.load(file_handle)
    else:
        log_stream.error(' ===> Fx table "' + file_name + '" does not exist.')
        raise IOError('Fx table is not available in the selected location')
    return file_table
# -------------------------------------------------------------------------------------
