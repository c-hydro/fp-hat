=========
Changelog
=========

Version 1.2.0 [2021-02-22]
===========
 APP: HAT_DataManager_HMC_NRT
- FIX: bugs related to xarray library;
- FIX: bugs related to progressbar library

Version 1.1.5 [2019-10-22]
===========
 APP: HAT_DataManager_HMC_NRT
- ADD: method to set terrain variable in buffered datasets when is missed
- ADD: effective time steps information about computing gridded average or accumulated variable(s) skipping empty step(s) 
- FIX: empty time steps condition in computing gridded average or accumulated variable(s)
- ADD: update dimensions names to standard name if needed [X, Y, time] -> [west_east, south_north, time] 
- ADD: multiple deterministic and probabilistic nwp run(s)

Version 1.1.4 [2019-07-08]
===========
 APP: HAT_DataManager_HMC_NRT
- ADD: variables to datasets (soil moisture and accumulated rain time-series)
- ADD: management of tmp file(s) in a common system folder
- FIX: datasets finder according with operative chain requests

Version 1.1.3 [2019-05-27]
===========
 APP: HAT_DataPublisher_HMC_NRT
- ADD: soil moisture and accumulated rain to time-series graph(s)

Version 1.1.2 [2019-05-16]
===========
 APP: HAT_DataManager_HMC_NRT
- FIX: bug about selecting gridded variables with mean equal to zero
- FIX: bug about out of range probabilistic runs
 APP: HAT_DataPublisher_HMC_NRT
- FIX: bugs in data seeking and data plotting (hydrapp time-series and maps product)

Version 1.1.1 [2019-03-04]
===========
 APP: HAT_DataManager_HMC_NRT
- FIX: nasty bugs arisen in operative mode fixed

Version 1.1.0 [2019-03-22]
===========
 APP: HAT_DataPublisher_HMC_NRT
- Beta release

Version 1.0.0 [2019-02-13]
===========
 APP: HAT_DataManager_HMC_NRT
- Beta release

Version 0.0.1 [2019-01-16]
===========
- Start development and configuration of HAT python package

