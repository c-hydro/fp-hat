"""
Library Features:

Name:          lib_utils_system
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201202'
Version:       '1.0.0'
"""
# -------------------------------------------------------------------------------------
# Library
import os
import logging

from copy import deepcopy
from datetime import datetime

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to slice list every n elements
def slice_list(source, step):
    return [source[i::step] for i in range(step)]
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def make_folder(path_folder):
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert coupled list to dictionary
def convert_list2dict(list_keys, list_values):
    dictionary = {k: v for k, v in zip(list_keys, list_values)}
    return dictionary
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to join folder and filename (managing some exceptions)
def join_path(folder_name, file_name):
    if folder_name and file_name:
        path_name = os.path.join(folder_name, file_name)
    elif (folder_name is None) and file_name:
        path_name = file_name
    elif folder_name and file_name == "":
        log_stream.warning(' ===> FileName is defined by empty string')
        path_name = deepcopy(folder_name)
    else:
        log_stream.error(' ===> FolderName: "' + str(folder_name) + '" FileName: "' +
                         str(file_name) + '". Join folder and file names ... FAILED. ')
        raise NotImplemented('Case not implemented yet')
    return path_name
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to add format(s) string (path or filename)
def fill_tags2string(string_raw, tags_format=None, tags_filling=None, tags_template='[TMPL_TAG_{:}]'):

    apply_tags = False
    if string_raw is not None:
        for tag in list(tags_format.keys()):
            if tag in string_raw:
                apply_tags = True
                break

    if apply_tags:

        string_filled = None
        tag_dictionary = {}
        for tag_id, (tag_key, tag_value) in enumerate(tags_format.items()):
            tag_key_tmp = '{' + tag_key + '}'
            if tag_value is not None:

                tag_id = tags_template.format(tag_id)
                tag_dictionary[tag_id] = {'key': None, 'value': None}

                if tag_key_tmp in string_raw:
                    tag_dictionary[tag_id] = {'key': tag_key, 'value': tag_value}
                    string_filled = string_raw.replace(tag_key_tmp, tag_id)
                    string_raw = string_filled
                else:
                    tag_dictionary[tag_id] = {'key': tag_key, 'value': None}

        dim_max = 1
        for tags_filling_values_tmp in tags_filling.values():
            if isinstance(tags_filling_values_tmp, list):
                dim_tmp = tags_filling_values_tmp.__len__()
                if dim_tmp > dim_max:
                    dim_max = dim_tmp

        string_filled_list = [string_filled] * dim_max

        string_filled_def = []
        for string_id, string_filled_step in enumerate(string_filled_list):

            for tag_dict_template, tag_dict_fields in tag_dictionary.items():
                tag_dict_key = tag_dict_fields['key']
                tag_dict_value = tag_dict_fields['value']

                if tag_dict_template in string_filled_step:
                    if tag_dict_value is not None:

                        if tag_dict_key in list(tags_filling.keys()):

                            value_filling_obj = tags_filling[tag_dict_key]

                            if isinstance(value_filling_obj, list):
                                value_filling = value_filling_obj[string_id]
                            else:
                                value_filling = value_filling_obj

                            string_filled_step = string_filled_step.replace(tag_dict_template, tag_dict_key)

                            if isinstance(value_filling, datetime):
                                tag_dict_value = value_filling.strftime(tag_dict_value)
                            elif isinstance(value_filling, (float, int)):
                                tag_dict_value = tag_dict_key.format(value_filling)
                            else:
                                tag_dict_value = value_filling

                            string_filled_step = string_filled_step.replace(tag_dict_key, tag_dict_value)

                        else:

                            # reverse the tag if not filled
                            tag_dict_key = '{' + tag_dict_key + '}'
                            string_filled_step = string_filled_step.replace(tag_dict_template, tag_dict_key)

            string_filled_def.append(string_filled_step)

        if dim_max == 1:
            string_filled_out = string_filled_def[0].replace('//', '/')
        else:
            string_filled_out = []
            for string_filled_tmp in string_filled_def:
                string_filled_out.append(string_filled_tmp.replace('//', '/'))

        return string_filled_out
    else:
        return string_raw
# -------------------------------------------------------------------------------------
