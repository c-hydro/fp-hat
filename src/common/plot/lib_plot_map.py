"""
Library Features:

Name:          lib_plot_map
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180918'
Version:       '1.0.0'
"""

#######################################################################################
# Library
from numpy import arange

import matplotlib.pylab as plt
from mpl_toolkits.basemap import Basemap
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to plot map using pcolormesh
def plotMap_Pcolor(a2dData, a2dGeoX, a2dGeoY, a1dGeoBox,
                   dDataMin=0, dDataMax=10, sColorMap='RdBu_r', sCBarLabel='NA', sMapRes='l'):

    # Define geobox
    dGeoYMin = a1dGeoBox[0]
    dGeoXMin = a1dGeoBox[1]
    dGeoYMax = a1dGeoBox[2]
    dGeoXMax = a1dGeoBox[3]

    oFig = plt.figure(figsize=(18, 18))
    oBaseMap = Basemap(projection='cea', resolution=sMapRes,
                       llcrnrlat=dGeoYMin, llcrnrlon=dGeoXMin,
                       urcrnrlat=dGeoYMax, urcrnrlon=dGeoXMax
                       )

    oBaseMap.drawcoastlines(color='lightgray', linewidth=1.25)
    # oBaseMap.fillcontinents()
    oBaseMap.drawmapboundary(fill_color='aqua')

    oBaseMap.pcolormesh(a2dGeoX, a2dGeoY, a2dData, latlon=True, cmap=sColorMap)

    oBaseMap.drawparallels(arange(dGeoYMin, dGeoYMax, 0.4), labels=[True, False, False, False])
    oBaseMap.drawmeridians(arange(dGeoXMin, dGeoXMax, 0.4), labels=[False, False, False, True])

    oBaseMap.colorbar(location='right', format='%d', label=sCBarLabel)

    plt.clim(dDataMin, dDataMax)
    plt.show()
# -------------------------------------------------------------------------------------
