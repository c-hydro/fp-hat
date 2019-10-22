import matplotlib.cm as cm
import matplotlib.colors as colors
import os
import json
import glob
import csv


def write_rgb_colormaps(filename, color_list, n=10):
    with open(filename, 'w') as file:
        for color_row in color_list:
            color_rgb = ','.join(str(row) for row in color_row)
            color_rgb = '[' + color_rgb + '],'
            file.write(color_rgb + '\n')


def get_rgb_colormaps(minimum, maximum, value):
    minimum, maximum = float(minimum), float(maximum)
    ratio = 2 * (value-minimum) / (maximum - minimum)
    b = int(max(0, 255*(1 - ratio)))
    r = int(max(0, 255*(ratio - 1)))
    g = 255 - b - r
    return r, g, b


def colormaps_path():
    """Returns application's default path for storing user-defined colormaps"""
    return os.path.dirname(__file__)


def get_system_colormaps():
    """Returns the list of colormaps that ship with matplotlib"""
    return [m for m in cm.datad]


def get_user_colormaps(cmap_fldr=colormaps_path()):
    """Returns a list of user-defined colormaps in the specified folder (defaults to
    standard colormaps folder if not specified)."""
    user_colormaps = []
    for root, dirs, files in os.walk(cmap_fldr):
        files = glob.glob(root + '/*.cmap')
        for name in files:
            with open(os.path.join(root, name), "r") as fidin:
                cmap_dict = json.load(fidin)
                user_colormaps.append(cmap_dict.get('name', name))
                user_colormaps.append(cmap_dict.get('vmin', name))
                user_colormaps.append(cmap_dict.get('vmax', name))
                user_colormaps.append(cmap_dict.get('tick_label', name))
                user_colormaps.append(cmap_dict.get('tick_loc', name))
    return user_colormaps


def load_colormap(json_file):
    """Generates and returns a matplotlib colormap from the specified JSON file,
    or None if the file was invalid."""
    colormap = None
    with open(json_file, "r") as fidin:
        cmap_dict = json.load(fidin)
        if cmap_dict.get('colors', None) is None:
            return colormap
        colormap_type = cmap_dict.get('type', 'linear')
        colormap_name = cmap_dict.get('name', os.path.basename(json_file))
        if colormap_type == 'linear':
            colormap = colors.LinearSegmentedColormap.from_list(name=colormap_name,
                                                                colors=cmap_dict['colors'])
        elif colormap_type == 'list':
            colormap = colors.ListedColormap(name=colormap_name, colors=cmap_dict['colors'])

        if 'vmin' in list(cmap_dict.keys()):
            colormap_vmin = cmap_dict['vmin']
        else:
            colormap_vmin = None
        if 'vmax' in list(cmap_dict.keys()):
            colormap_vmax = cmap_dict['vmax']
        else:
            colormap_vmax = None
        if 'tick_label' in list(cmap_dict.keys()):
            colormap_ticklabel = cmap_dict['tick_label']
        else:
            colormap_ticklabel = None
        if 'tick_loc' in list(cmap_dict.keys()):
            colormap_tickloc = cmap_dict['tick_loc']
        else:
            colormap_tickloc = None

        setattr(colormap, 'vmin', colormap_vmin)
        setattr(colormap, 'vmax', colormap_vmax)
        setattr(colormap, 'ticklabel', colormap_ticklabel)
        setattr(colormap, 'tickloc', colormap_tickloc)

    return colormap


def load(cmap_name, cmap_folder=colormaps_path()):
    """Returns the matplotlib colormap of the specified name -
    if not found in the predefined
    colormaps, searches for the colormap in the specified
    folder (defaults to standard colormaps
    folder if not specified)."""

    if cmap_name.endswith('.cmap'):
        cmap_name_user = cmap_name
    else:
        cmap_name_user = cmap_name + '.cmap'
    user_colormaps = get_user_colormaps(cmap_folder)
    system_colormaps = get_system_colormaps()

    if cmap_name_user in user_colormaps:
        cmap_file = os.path.join(cmap_folder, cmap_name_user)
        cmap = load_colormap(cmap_file)
    elif cmap_name in system_colormaps:

        cmap = cm.get_cmap(cmap_name)
        cmap_color = []
        for iN in range(0, cmap.N):
            cmap_color.append(list(cmap(iN)))
        cmap_color[0][3] = 0.0

        write_rgb_colormaps(os.path.join(cmap_folder, 'current_map.txt'), cmap_color)
        cmap = colors.LinearSegmentedColormap.from_list(name=cmap_name, colors=cmap_color)

        return cmap
    else:
        raise ValueError('Colormap not found')
    return cmap
