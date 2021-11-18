#!/usr/bin/python3

"""
HYDE Downloading Tool - DROPS Weather Stations

__date__ = '20191118'
__version__ = '1.0.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'HAT'

General command line:
python3 hyde_organizer_hydrapp_plot_ts.py -settings_file configuration.json
"""

# -------------------------------------------------------------------------------------
# Libraries
import glob
from os import listdir, makedirs
from os.path import isfile, join, splitext, exists, isdir
import shutil
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    path_img_db = "/home/fabio/Desktop/hydrapp_img/db/"

    path_img_root = "/home/fabio/Desktop/hydrapp_img/*"
    file_suffix_img = '.jpg'
    file_root_img = '{:}_{:}.jpg'

    folders_img = glob.glob(path_img_root)

    if not exists(path_img_db):
        makedirs(path_img_db)

    for folder_img in folders_img:

        if isdir(folder_img):
            folder_time = folder_img.split('/')[-1]
            files_img = [f for f in listdir(folder_img) if isfile(join(folder_img, f))]

            for file_img in files_img:
                [file_root_tmp, file_suffix_tmp] = splitext(file_img)

                if file_suffix_tmp == file_suffix_img:

                    file_root_db = file_root_img.format(file_root_tmp, folder_time)

                    source_img = join(folder_img, file_img)
                    destination_img = join(path_img_db, file_root_db)

                    if exists(source_img):
                        shutil.copyfile(source_img, destination_img)

    print('fine')
    print('')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# -------------------------------------------------------------------------------------


