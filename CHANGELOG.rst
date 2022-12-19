=========
Changelog
=========

Version 1.5.2 [2022-12-19]
===========
APP: **HAT_RunAnalyzer_HMC.py**
    - FIX: bugs related to the operational mode.
APP: **HAT_RunPublisher_HMC_Maps.py**
	- ADD: grid static information from file or using the basic geographical information (xll_corner, yll_corner, rows, cols and cell_size).
    - FIX: bugs related to the operational mode.
    - FIX: bugs related to the mandatory/ancillary static data (terrain, flow_directions and river_network).
APP: **HAT_RunPublisher_HMC_TimeSeries.py**
	- ADD: label of time reference system in the plots.
    - FIX: bugs related to the operational mode.

Version 1.5.1 [2021-07-28]
===========
APP: **HAT_RunAnalyzer_HMC.py**
    - Operational Release.
APP: **HAT_RunPublisher_HMC_Maps.py**
    - Operational Release.
APP: **HAT_RunPublisher_HMC_TimeSeries.py**
    - Operational Release.

Version 1.5.0 [2021-09-03]
===========
APP: **HAT_RunPublisher_HMC_Maps.py**
	- Release for refactoring maps app.
APP: **HAT_RunPublisher_HMC_TimeSeries.py**
	- Release for refactoring time-series app.

APP: **HAT_RunAnalyzer_HMC.py**
	- FIX: bugs related to real-time mode.
    - FIX: bugs related to undefined datasets.
APP: **HAT_RunPublisher_HMC_Maps.py**
	- FIX: bugs related to real-time mode.
	- FIX: bugs related to variable units and limits.
	- FIX: bugs related to rolling average and accumulated maps.
	- FIX: bugs related to selection of first or last step for instantaneous maps.
	- ADD: snow variables, colormaps and maps (SWE, SnowDensity, SnowMelting, SnowMask);
	- ADD: information to the map renderer.
APP: **HAT_RunPublisher_HMC_TimeSeries.py**
	- FIX: bugs related to real-time mode.
	- FIX: bugs related to observed discharge time-series.
    - FIX: bugs related to undefined datasets;
    - ADD: dynamic discharge graph limits;
    - ADD: information to the map renderer.

TOOL: **hat_tool_postprocessing_registry_file.py**

Version 1.2.0 [2021-02-22]
===========
APP: **HAT_DataOrganizer_HMC_NRT.py**
	- FIX: bugs related to xarray library;
	- FIX: bugs related to progressbar library
APP: **HAT_DataPublisher_HMC_NRT.py**
	- FIX: bugs related to matplotlib=3.1.3 and cartopy=0.17 libraries
APP: **HAT_RunAnalyzer_HMC_MAIN.py**
	- Release for HMC version 3.x.x

Version 1.1.5 [2019-10-22]
===========
APP: **HAT_DataManager_HMC_NRT.py**
	- ADD: method to set terrain variable in buffered datasets when is missed
	- ADD: effective time steps information about computing gridded average or accumulated variable(s) skipping empty step(s) 
	- FIX: empty time steps condition in computing gridded average or accumulated variable(s)
	- ADD: update dimensions names to standard name if needed [X, Y, time] -> [west_east, south_north, time] 
	- ADD: multiple deterministic and probabilistic nwp run(s)

Version 1.1.4 [2019-07-08]
===========
APP: **HAT_DataManager_HMC_NRT.py**
	- ADD: variables to datasets (soil moisture and accumulated rain time-series)
	- ADD: management of tmp file(s) in a common system folder
	- FIX: datasets finder according with operative chain requests

Version 1.1.3 [2019-05-27]
===========
APP: **HAT_DataPublisher_HMC_NRT.py**
	- ADD: soil moisture and accumulated rain to time-series graph(s)

Version 1.1.2 [2019-05-16]
===========
APP: **HAT_DataManager_HMC_NRT.py**
	- FIX: bug about selecting gridded variables with mean equal to zero
	- FIX: bug about out of range probabilistic runs
APP: **HAT_DataPublisher_HMC_NRT.py**
	- FIX: bugs in data seeking and data plotting (hydrapp time-series and maps product)

Version 1.1.1 [2019-03-04]
===========
APP: **HAT_DataManager_HMC_NRT.py**
	- FIX: nasty bugs arisen in operative mode fixed

Version 1.1.0 [2019-02-22]
===========
APP: **HAT_DataPublisher_HMC_NRT.py**
	- Beta release

Version 1.0.0 [2019-02-13]
===========
APP: **HAT_DataManager_HMC_NRT.py**
	- Beta release

Version 0.0.1 [2019-01-16]
===========
- Start development and configuration of HAT python package

