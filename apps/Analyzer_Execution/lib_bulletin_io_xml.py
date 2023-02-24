"""
Library Features:

Name:          lib_bulletin_io_xml
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
# method to update dataframe method to the xml custom node(s)
def to_xml(df, filename=None, mode='w'):

    def row_to_xml(row):
        xml = ['<marker>']
        for i, col_name in enumerate(row.index):
            # xml.append('  <field name="{0}">{1}</field>'.format(col_name, row.iloc[i]))
            xml.append(' {0}="{1}" '.format(col_name, row.iloc[i]))
        xml.append('</marker>')
        # xml.append('/>')
        return ''.join(xml)

    nodes = '\n'.join(df.apply(row_to_xml, axis=1))

    res = '<?xml version="1.0" encoding="UTF-8"?>\n'
    res += '<markers>\n'
    res += nodes + '\n'
    res += '</markers>\n'

    if filename is None:
        return res

    with open(filename, mode) as f:
        f.write(res)

# define the "to_xml" method as a method of the dataframe
pd.DataFrame.to_xml = to_xml
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write the html bulletin summary
def write_bulletin_warnings(
        time_run, time_exec, time_format='%Y-%m-%d %H:%M', time_mode='LOCAL',
        file_name='bulletin_operational_chain.xml',
        bulletin_dframe=None, sections_dframe=None,
        map_fields_expected=None):

    # map dataframe fields
    if map_fields_expected is None:
        map_fields_expected = {
            'section_longitude': 'lon', 'section_latitude': 'lat', 'section_tag': 'tag',
            'section_code': 'code', 'section_description': 'name', 'domain_description': 'basin',
            'thr_code': 'ALERT'}
    # get expected column list
    bulletin_cols_expected = list(map_fields_expected.keys())

    # check expected and found columns and mapping fields
    bulletin_map_keys_found, bulletin_map_value_found = [], []
    for bulletin_map_key in bulletin_cols_expected:
        if bulletin_map_key in list(bulletin_dframe.columns):
            bulletin_map_value = map_fields_expected[bulletin_map_key]
            bulletin_map_keys_found.append(bulletin_map_key)
            bulletin_map_value_found.append(bulletin_map_value)
    map_fields_found = dict(zip(bulletin_map_keys_found, bulletin_map_value_found))

    # filter and update bulletin data according to the mapping fields
    bulletin_dframe = bulletin_dframe[bulletin_map_keys_found]
    bulletin_dframe = bulletin_dframe.rename(columns=map_fields_found)

    # write data to xml
    bulletin_dframe.to_xml(file_name)

# -------------------------------------------------------------------------------------
