# -------------------------------------------------------------------------------------
# Libraries
import logging
import tempfile
import os
import time
import json
import pickle
import rasterio
import numpy as np
import xarray as xr
import pandas as pd

from distutils.util import strtobool

from rasterio.transform import Affine
from osgeo import gdal, gdalconst

logging.getLogger('rasterio').setLevel(logging.WARNING)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read discharge file
def read_file_discharge(file_name, file_template=None, file_skiprows=4):

    file_tmp = pd.read_table(file_name)
    file_data = list(file_tmp.values)

    collections_id = 0
    obj_mod = None
    obj_observed = None
    obj_header = {}
    for row_id, row_step in enumerate(file_data):
        row_tmp = row_step[0]
        if row_id < file_skiprows:
            field_key, field_data = row_tmp.rstrip().split('=')

            if field_key in list(file_template.keys()):
                field_name = file_template[field_key]['name']
                field_type = file_template[field_key]['type']
                field_value = file_template[field_key]['value']
            else:
                field_name = field_key
                field_type = None
                field_value = None

            if field_type is not None:
                if field_type == 'time_stamp':
                    field_data = pd.Timestamp(field_data)
                elif field_type == 'time_frequency':
                    field_data = pd.Timedelta(field_data)
                elif field_type == 'int':
                    field_data = np.int(field_data)

            if field_value is not None:
                field_data = field_value

            obj_header[field_name] = field_data
        elif row_id == file_skiprows:
            columns_values = row_tmp.rstrip().split(' ')
            array_observed = np.array(columns_values, dtype=np.float)
            array_observed[array_observed < 0.0] = np.nan
            time_n = array_observed.shape[0]

            if obj_observed is None:
                obj_observed = np.zeros(shape=(time_n, 1))
                obj_observed[:, :] = np.nan
            obj_observed[:, 0] = array_observed

        elif row_id >= file_skiprows:

            columns_values = row_tmp.rstrip().split(' ')
            array_values = np.array(columns_values, dtype=np.float)
            array_values[array_values < 0.0] = np.nan
            time_n = array_values.shape[0]

            if obj_mod is None:
                obj_mod = np.zeros(shape=(time_n , obj_header['scenario_n']))
                obj_mod[:, :] = np.nan
            obj_mod[:, collections_id] = array_values

            collections_id += 1

    return obj_header, obj_mod, obj_observed
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read warning file
def read_file_warning(file_name, file_template=None, file_skiprows=4, tag_data='section_{:}'):

    file_tmp = pd.read_table(file_name)
    file_data = list(file_tmp.values)

    file_time_modified = pd.Timestamp(time.ctime(os.path.getmtime(file_name)))
    file_time_created = pd.Timestamp(time.ctime(os.path.getctime(file_name)))

    collections_id = 0
    file_header = {}
    file_collections = {}
    for row_id, row_step in enumerate(file_data):
        row_tmp = row_step[0]
        if row_id < file_skiprows:
            field_key, field_data = row_tmp.rstrip().split('=')

            if field_key in list(file_template.keys()):
                field_name = file_template[field_key]['name']
                field_type = file_template[field_key]['type']
                field_value = file_template[field_key]['value']
            else:
                field_name = field_key
                field_type = None
                field_value = None

            if field_type is not None:
                if field_type == 'time_stamp':
                    field_data = pd.Timestamp(field_data)
                elif field_type == 'time_frequency':
                    field_data = pd.Timedelta(field_data)
                elif field_type == 'int':
                    field_data = np.int(field_data)

            if field_value is not None:
                field_data = field_value

            file_header[field_name] = field_data
        elif row_id == file_skiprows:
            columns_name = row_tmp.rstrip().split(' ')
            columns_type = [str, str, float, float, bool, float, bool]
        elif row_id > file_skiprows:
            columns_values = row_tmp.rstrip().split(' ')
            file_collections[tag_data.format(collections_id)] = {}

            for column_name, column_value, column_type in zip(columns_name, columns_values, columns_type):
                file_collections[tag_data.format(collections_id)][column_name] = {}

                if column_type is float:
                    column_value = np.float(column_value)
                elif column_type is bool:
                    column_value = strtobool(column_value.lower())
                elif column_type is str:
                    column_value = column_value.strip()
                file_collections[tag_data.format(collections_id)][column_name] = column_value

            collections_id += 1

        file_header['time_file_created'] = file_time_created
        file_header['time_file_modified'] = file_time_modified

    return file_header, file_collections
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write an html status file
def write_file_status(time_run, time_exec, time_format='%Y-%m-%d %H:%M',
                    html_name='run_analyzer.html',
                    run_default=None, run_execution=None, run_ancillary=None,
                    run_alert=None, run_alarm=None, time_mode='LOCAL'):

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
        html_handle.write('.SectionWidth {width:150;}\n')
        html_handle.write('.SectionWidth1 {width:30;}\n')
        html_handle.write('.SectionWidth2 {width:10;}\n')
        html_handle.write('.tbl tr:hover {background-color: lightgray;color: blue;}\n')
        html_handle.write('</style>\n')

        html_handle.write('<table><tr><td><font size=3> Execution Time: </font></td><td><font size=5><b>' +
                          time_exec.strftime(time_format) + ' ' + time_mode + '</b></font></td></tr>\n')

        html_handle.write('<table><tr><td><font size=3> Reference Time: </font></td><td><font size=5><b>' +
                          time_run.strftime(time_format) + ' ' + time_mode + ' </b></font></td></tr>\n')

        html_handle.write('<table class="tbl">\n')
        html_handle.write('<thead>\n')
        html_handle.write('<td class="blu"><b>Run Configuration<br>Regione Marche</b></td>\n')
        html_handle.write('<td class="blu"><b>State</b></td>\n')
        html_handle.write('<td class="blu"><b>TimeStart</b></td>\n')
        html_handle.write('<td class="blu"><b>TimeEnd</b></td>\n')
        html_handle.write('<td class="blu"><b>Scenarios</b></td>\n')
        html_handle.write('<td class="blu"><b>Sections</b></td>\n')
        html_handle.write('<td class="nero SectionWidth2"></td>\n')
        html_handle.write('<td class="blu SectionWidth1"><b> OGGI <br> gialla </b></td>\n')
        html_handle.write('<td class="blu SectionWidth"><b> OGGI <br> gialla </b></td>\n')
        html_handle.write('<td class="blu SectionWidth1"><b> DOMANI <br> gialla </b></td>\n')
        html_handle.write('<td class="blu SectionWidth"><b> DOMANI <br> gialla </b></td>\n')
        html_handle.write('<td class="nero SectionWidth2"></td>\n')
        html_handle.write('<td class="blu SectionWidth1"><b> OGGI <br> rossa </b></td>\n')
        html_handle.write('<td class="blu SectionWidth"><b> OGGI <br> rossa </b></td>\n')
        html_handle.write('<td class="blu SectionWidth1"><b> DOMANI <br> rossa </b></td>\n')
        html_handle.write('<td class="blu SectionWidth"><b> DOMANI <br> rossa </b></td>\n')
        html_handle.write('</thead>\n')
        html_handle.write('<tbody>\n')

        for (run_key, run_execution_step), run_ancillary_step, run_alert_step, run_alarm_step in zip(
                run_execution.items(), run_ancillary.values(), run_alert.values(), run_alarm.values()):

            html_handle.write('<tr>')

            run_description = run_default[run_key]['description']

            if run_ancillary_step is not None:
                run_time_mod_first = run_ancillary_step['time_modified_first'].strftime(time_format)
                run_time_mod_last = run_ancillary_step['time_modified_last'].strftime(time_format)
                run_section_n_found = str(run_ancillary_step['section_n'])
                run_scenario_n = str(run_ancillary_step['scenario_n'])
                # run_time_range = str(run_ancillary_step['time_range'])

                if run_alert_step or run_alarm_step:
                    html_handle.write('<td class=verde><b>' + run_description + '</b></td>')
                    html_handle.write('<td class=verde> COMPLETED </td>')
                    html_handle.write('<td class=verde>' + str(run_time_mod_first) + ' ' + time_mode + ' </td>')
                    html_handle.write('<td class=verde>' + str(run_time_mod_last) + ' ' + time_mode + ' </td>')
                    html_handle.write('<td>' + run_scenario_n + '</td>')
                    html_handle.write('<td>' + run_section_n_found + '</td>')
                    html_handle.write('<td class=nero></td>')

                if run_alert_step:

                    for id, (run_alert_key, run_alert_value) in enumerate(run_alert_step.items()):

                        section_list_name = run_alert_value['name']
                        section_list_idx = run_alert_value['idx']
                        section_list_value = run_alert_value['value']
                        section_n_alert = str(section_list_name.__len__())

                        section_name = ','.join(section_list_name)

                        # alert today
                        if id == 0:
                            if section_list_name:
                                html_handle.write('<td class=gialla>' + section_n_alert + '/' + run_section_n_found)
                                html_handle.write('<td class=gialla>' + section_name + '</td>')
                            else:
                                html_handle.write('<td>-</td>')
                                html_handle.write('<td>-</td>')

                        # alert tomorrow
                        if id == 1:
                            if section_list_name:
                                html_handle.write('<td class=gialla>' + section_n_alert + '/' + run_section_n_found)
                                html_handle.write('<td class=gialla>' + section_name + '</td>')
                            else:
                                html_handle.write('<td>-</td>')
                                html_handle.write('<td>-</td>')
                            html_handle.write('<td class=nero></td>')

                if run_alarm_step:

                    for id, (run_alarm_key, run_alarm_value) in enumerate(run_alarm_step.items()):

                        section_list_name = run_alarm_value['name']
                        section_list_idx = run_alarm_value['idx']
                        section_list_value = run_alarm_value['value']
                        section_n_alarm = str(section_list_name.__len__())

                        section_name = ','.join(section_list_name)

                        # alert today
                        if id == 0:
                            if section_list_name:
                                html_handle.write('<td class=gialla>' + section_n_alarm + 'di' + run_section_n_found)
                                html_handle.write('<td class=gialla>' + section_name + '</td>')
                            else:
                                html_handle.write('<td>-</td>')
                                html_handle.write('<td>-</td>')

                        # alert tomorrow
                        if id == 1:
                            if section_list_name:
                                html_handle.write('<td class=gialla>' + section_n_alarm + 'di' + run_section_n_found)
                                html_handle.write('<td class=gialla>' + section_name + '</td>')
                            else:
                                html_handle.write('<td>-</td>')
                                html_handle.write('<td>-</td>')

                if (not run_alert_step) and (not run_alarm_step):
                    html_handle.write('<td class=azzurro><b>' + run_description + '</b></td>')
                    html_handle.write('<td class=azzurro> COMPLETED </td>')
                    html_handle.write('<td class=azzurro>' + str(run_time_mod_first) + ' ' + time_mode + ' </td>')
                    html_handle.write('<td class=azzurro>' + str(run_time_mod_last) + ' ' + time_mode + ' </td>')
                    html_handle.write('<td>' + run_scenario_n + '</td>')
                    html_handle.write('<td>' + run_section_n_found + '</td>')
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

            else:

                if run_execution_step and (run_ancillary_step is None):

                    run_time_mod_first = run_execution_step['time_modified_first'].strftime(time_format)
                    run_time_mod_last = run_execution_step['time_modified_last'].strftime(time_format)
                    run_scenario_n = str(run_execution_step['scenario_n'])

                    html_handle.write('<td class=grigio><b>' + run_description + '</b></td>')
                    html_handle.write('<td class=grigio> RUNNING ... </td>')
                    html_handle.write('<td class=grigio>' + str(run_time_mod_first) + ' ' + time_mode + ' </td>')
                    html_handle.write('<td class=grigio> NA </td>')
                    html_handle.write('<td>' + run_scenario_n + '</td>')
                    html_handle.write('<td> NA </td>')
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

                elif (run_execution_step is None) and (run_ancillary_step is None):

                    html_handle.write('<td class=rossa><b>' + run_description + '</b></td>')
                    html_handle.write('<td class=rossa> RUN NOT AVAILABLE </td>')
                    html_handle.write('<td class=rossa> NA </td>')
                    html_handle.write('<td class=rossa> NA </td>')
                    html_handle.write('<td> NA </td>')
                    html_handle.write('<td> NA </td>')
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

            html_handle.write('</tr>')

        ####

        html_handle.write('</tbody>')
        html_handle.write('</html>')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a tmp name
def create_filename_tmp(prefix='tmp_', suffix='.tiff', folder=None):

    if folder is None:
        folder = '/tmp'

    with tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, suffix=suffix, delete=False) as tmp:
        temp_file_name = tmp.name
    return temp_file_name
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write file tiff
def write_file_tif(file_name, file_data, file_wide, file_high, file_geotrans, file_proj,
                   file_metadata=None,
                   file_format=gdalconst.GDT_Float32):

    if not isinstance(file_data, list):
        file_data = [file_data]

    if file_metadata is None:
        file_metadata = {'description_field': 'data'}
    if not isinstance(file_metadata, list):
        file_metadata = [file_metadata] * file_data.__len__()

    if isinstance(file_geotrans, Affine):
        file_geotrans = file_geotrans.to_gdal()

    file_n = file_data.__len__()
    dset_handle = gdal.GetDriverByName('GTiff').Create(file_name, file_wide, file_high, file_n, file_format,
                                                       options=['COMPRESS=DEFLATE'])
    dset_handle.SetGeoTransform(file_geotrans)
    dset_handle.SetProjection(file_proj)

    for file_id, (file_data_step, file_metadata_step) in enumerate(zip(file_data, file_metadata)):
        dset_handle.GetRasterBand(file_id + 1).WriteArray(file_data_step)
        dset_handle.GetRasterBand(file_id + 1).SetMetadata(file_metadata_step)
    del dset_handle
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read file tif
def read_file_tif(file_name, file_bands=1):


    file_handle = rasterio.open(file_name)
    file_proj = file_handle.crs.wkt
    file_geotrans = file_handle.transform

    file_tags = file_handle.tags()
    file_bands = file_handle.count
    file_metadata = file_handle.profile

    if file_bands == 1:
        file_data = file_handle.read(1)
    elif file_bands > 1:
        file_data = []
        for band_id in range(0, file_bands):
            file_data_tmp = file_handle.read(band_id + 1)
            file_data.append(file_data_tmp)
    else:
        logging.error(' ===> File multi-band are not supported')
        raise NotImplementedError('File multi-band not implemented yet')

    return file_data, file_proj, file_geotrans
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
# Method to create a data array
def create_darray_3d(data, time, geo_x, geo_y, geo_1d=True,
                     coord_name_x='west_east', coord_name_y='south_north', coord_name_time='time',
                     dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x, dim_name_time]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={coord_name_time: (dim_name_time, time),
                                       coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)})
    else:
        logging.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_2d(data, geo_x, geo_y, geo_1d=True, name='geo',
                     coord_name_x='west_east', coord_name_y='south_north',
                     dim_name_x='west_east', dim_name_y='south_north',
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)},
                               name=name)
    else:
        logging.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data obj
def read_obj(filename):
    if os.path.exists(filename):
        data = pickle.load(open(filename, "rb"))
    else:
        data = None
    return data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write data obj
def write_obj(filename, data):
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# -------------------------------------------------------------------------------------
