"""
Library Features:

Name:          lib_utils_zip
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200401'
Version:       '3.0.0'
"""

#################################################################################
# Library
import logging
import os

from lib_info_args import logger_name, zip_extension

# Logging
log_stream = logging.getLogger(logger_name)
#################################################################################

# --------------------------------------------------------------------------------
# Zip format dictionary
zip_dictionary = dict(Type_1='gz', Type_2='bz2', Type_3='7z', Type_4='tar',
                      Type_5='tar.gz', Type_6='tar.7z', Type_7='zip')
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to check if zip extension is a known string
def check_zip_extension(zip_extension):

    # Check if string starts with point
    if zip_extension.startswith('.'):
        zip_extension_parser = zip_extension[1:]
    else:
        zip_extension_parser = zip_extension

    # Check if zip extension is a known string
    if zip_extension_parser not in list(zip_dictionary.values()):
        log_stream.error(' ===> Zip extension is not allowed. Check your compressed filename,')
        raise RuntimeError('Zip extension is wrong.')

    return zip_extension_parser

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to add only compressed extension
def add_zip_extension(file_name_unzip, zip_extension_template=zip_extension):

    if not zip_extension_template[0] == '.':
        zip_extension_template = '.' + zip_extension_template

    if not file_name_unzip.endswith(zip_extension_template):
        file_name_zip = file_name_unzip + zip_extension_template
    else:
        file_name_zip = file_name_unzip
    return file_name_zip
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to remove only compressed extension 
def remove_zip_extension(file_name_zip, zip_extension_template=zip_extension):

    # Check zip extension format
    if zip_extension is not None:
        # Check zip extension format in selected mode
        zip_ext_str = check_zip_extension(zip_extension_template)
    else:
        # Check zip extension format in default mode
        file_name_unzip, zip_extension_template = os.path.splitext(file_name_zip)
        # Check zip extension format
        zip_ext_str = check_zip_extension(zip_extension_template)

    if not zip_ext_str.startswith('.'):
        zip_ext_str = '.' + zip_ext_str

    file_name_unzip = file_name_zip.split(zip_ext_str)[0]

    return file_name_unzip
# --------------------------------------------------------------------------------
