fdsnwsscripts
=============

.. image:: https://img.shields.io/pypi/v/fdsnwsscripts.svg
   :target: https://img.shields.io/pypi/v/fdsnwsscripts.svg
   
.. image:: https://img.shields.io/pypi/pyversions/fdsnwsscripts.svg
   :target: https://img.shields.io/pypi/pyversions/fdsnwsscripts.svg
   
.. image:: https://img.shields.io/pypi/format/fdsnwsscripts.svg
   :target: https://img.shields.io/pypi/format/fdsnwsscripts.svg
   
.. image:: https://img.shields.io/pypi/status/fdsnwsscripts.svg
   :target: https://img.shields.io/pypi/status/fdsnwsscripts.svg
   
Scripts for working with (EIDA) FDSN web services.

Overview
--------

The `fdsnws_scripts` is a collection of next generation distributed data request tools that are based on FDSN [http://www.fdsn.org/webservices web services] and the EIDA [http://www.orfeus-eu.org/data/eida/eidaws/routing routing service].

You may use these tools to request

* seismic waveform data, as mini-SEED, using the fdsnws-dataselect web service,

* seismic metadata, as FDSN Station XML, using the fdsnws-station web service.

More information about FDSN web services is available at GEOFON [http://geofon.gfz-potsdam.de/waveform/webservices.php] and of course from FDSN, at http://www.fdsn.org/webservices/ .


There are three tools here:

#. `fdsnws_fetch` can request waveform data or metadata, from multiple data centres (access points) with a single command. It does this using the EIDA routing service to discover which data centre(s) holds the data requested.

#. `fdsnws2sds` supports requests for larger amounts of data, saving it in an SDS tree-like file system structure.
   (The SeisComP Data Structure is defined [http://www.seiscomp3.org/doc/jakarta/current/apps/slarchive.html here] and [https://www.seiscomp3.org/wiki/doc/applications/slarchive/SDS here].)

#. `fdsnws2seed` provides full SEED and dataless SEED using EIDA FDSN web services. Modern applications should use FDSN StationXML instead of SEED.

