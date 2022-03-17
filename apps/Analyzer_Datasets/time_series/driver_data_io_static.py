"""
Class Features

Name:          driver_data_io_static
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210429'
Version:       '1.0.0'
"""

######################################################################################
# Library
import logging
import os

from lib_data_geo_ascii import read_data_grid
from lib_data_geo_shapefile import read_data_section
from lib_utils_geo import compute_section_mask, compute_section_area, order_section_area
from lib_utils_io import read_obj, write_obj
from lib_utils_system import make_folder, join_path

from lib_graph_ts_utils import read_ts_table

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
######################################################################################


# -------------------------------------------------------------------------------------
# Class DriverStatic
class DriverStatic:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, src_dict, dst_dict=None,
                 alg_ancillary=None, alg_template_tags=None,
                 flag_terrain_data='terrain',
                 flag_river_network_data='river_network', flag_flow_directions_data='flow_directions',
                 flag_section_data='sections', flag_table_graph_data='table_graph_lut',
                 flag_info_data='info',
                 flag_static_source='source', flag_static_destination='destination',
                 flag_cleaning_static=True):

        self.flag_terrain_data = flag_terrain_data
        self.flag_section_data = flag_section_data
        self.flag_river_network_data = flag_river_network_data
        self.flag_flow_directions_data = flag_flow_directions_data
        self.flag_table_graph_data = flag_table_graph_data
        self.flag_info_data = flag_info_data

        self.flag_static_source = flag_static_source
        self.flag_static_destination = flag_static_destination

        self.alg_ancillary = alg_ancillary

        self.alg_template_tags = alg_template_tags
        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'
        self.file_data_filter_tag = 'file_data_filter'
        # self.file_datatype_tag = 'type'

        self.folder_name_terrain_src = src_dict[self.flag_terrain_data][self.folder_name_tag]
        self.file_name_terrain_src = src_dict[self.flag_terrain_data][self.file_name_tag]
        self.file_path_terrain_src = join_path(self.folder_name_terrain_src, self.file_name_terrain_src)

        self.folder_name_flow_directions_src = src_dict[self.flag_flow_directions_data][self.folder_name_tag]
        self.file_name_flow_directions_src = src_dict[self.flag_flow_directions_data][self.file_name_tag]
        self.file_path_flow_directions_src = join_path(
            self.folder_name_flow_directions_src, self.file_name_flow_directions_src)

        self.folder_name_river_network_src = src_dict[self.flag_river_network_data][self.folder_name_tag]
        self.file_name_river_network_src = src_dict[self.flag_river_network_data][self.file_name_tag]
        self.file_path_river_network_src = join_path(
            self.folder_name_river_network_src, self.file_name_river_network_src)

        self.folder_name_section_src = src_dict[self.flag_section_data][self.folder_name_tag]
        self.file_name_section_src = src_dict[self.flag_section_data][self.file_name_tag]
        self.file_path_section_src = join_path(self.folder_name_section_src, self.file_name_section_src)
        # self.file_type_section_src = src_dict[self.flag_section_data][self.file_datatype_tag]

        self.file_filter_section_src = src_dict[self.flag_section_data][self.file_data_filter_tag]

        self.folder_name_table_graph_src = src_dict[self.flag_table_graph_data][self.folder_name_tag]
        self.file_name_table_graph_src = src_dict[self.flag_table_graph_data][self.file_name_tag]
        self.file_path_table_graph_src = join_path(self.folder_name_table_graph_src, self.file_name_table_graph_src)

        self.folder_name_info_dst = dst_dict[self.flag_info_data][self.folder_name_tag]
        self.file_name_info_dst = dst_dict[self.flag_info_data][self.file_name_tag]
        self.file_path_info_dst = join_path(self.folder_name_info_dst, self.file_name_info_dst)

        self.flag_cleaning_static = flag_cleaning_static

        self.str_delimited = ':'

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize geographical data
    def organize_static(self):

        # Info start
        log_stream.info(' ----> Organize static datasets ... ')

        flag_cleaning_static = self.flag_cleaning_static
        file_path_info = self.file_path_info_dst
        if flag_cleaning_static:
            if os.path.exists(file_path_info):
                os.remove(file_path_info)

        # Read gridded static data source
        if not os.path.exists(file_path_info):
            da_terrain = read_data_grid(self.file_path_terrain_src,
                                        var_limit_min=0, var_limit_max=None, output_format='data_array')
            da_flow_directions = read_data_grid(self.file_path_flow_directions_src,
                                                var_limit_min=0, var_limit_max=9, output_format='data_array')
            da_river_network = read_data_grid(self.file_path_river_network_src,
                                              var_limit_min=0, var_limit_max=1, output_format='data_array')
            # Read sections shapefile
            df_section_selected = read_data_section(self.file_path_section_src, file_filter=self.file_filter_section_src)

            # Read table_graph_lut
            dict_table_graph = read_ts_table(self.file_path_table_graph_src)

            # Compute section mask
            # obj_section_mask = compute_section_mask(da_flow_directions,
            # terrain_da=da_terrain, section_dframe=df_section)

            # Compute section area
            df_section_selected = compute_section_area(
                da_flow_directions, terrain_da=da_terrain, section_dframe=df_section_selected)
            # Order section area (using a area rule)
            df_section_selected = order_section_area(df_section_selected)

            # Data collection object
            static_data_collections = {self.flag_terrain_data: da_terrain,
                                       self.flag_river_network_data: da_river_network,
                                       self.flag_section_data: df_section_selected,
                                       self.flag_table_graph_data: dict_table_graph}

            # Write info datasets
            folder_name_info, file_name_info = os.path.split(file_path_info)
            make_folder(folder_name_info)

            write_obj(file_path_info, static_data_collections)

            # Info end
            log_stream.info(' ----> Organize static datasets ... DONE')

        else:
            # Read info datasets
            static_data_collections = read_obj(file_path_info)
            # Info end
            log_stream.info(' ----> Organize static datasets ... LOADED. Info datasets created previously')

        return static_data_collections
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
