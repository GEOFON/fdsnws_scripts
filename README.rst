fdsnwsscripts
=============

.. image:: https://img.shields.io/pypi/v/fdsnwsscripts.svg
   :target: https://img.shields.io/pypi/v/fdsnwsscripts.svg
   
.. image:: https://img.shields.io/badge/DOI-10.5880/gfz.2.4.2024.002-green
   :target: https://doi.org/10.5880/gfz.2.4.2024.002

.. image:: https://img.shields.io/badge/License-LGPLv3-blue
   :target: https://www.gnu.org/licenses/lgpl-3.0.en.html

.. image:: https://img.shields.io/pypi/pyversions/fdsnwsscripts.svg
   :target: https://img.shields.io/pypi/pyversions/fdsnwsscripts.svg
   
.. image:: https://img.shields.io/pypi/format/fdsnwsscripts.svg
   :target: https://img.shields.io/pypi/format/fdsnwsscripts.svg
   
.. image:: https://img.shields.io/pypi/status/fdsnwsscripts.svg
   :target: https://img.shields.io/pypi/status/fdsnwsscripts.svg
   
Scripts for working with (EIDA) FDSN web services.

Citation
--------
Please cite the use of this software as:

Heinloo, A. (2024). fdsnws_scripts: a collection of next generation distributed data request tools based on FDSN web services and the EIDA routing service (Version 2023.191) [Computer software]. GFZ Data Services. DOI: 10.5880/gfz.2.4.2024.002

Overview
--------

`fdsnws_scripts` is a collection of next generation distributed data request tools that are based on FDSN `web services
<http://www.fdsn.org/webservices/>`_ and the EIDA `routing service <https://www.orfeus-eu.org/data/eida/webservices/routing/>`_.

You may use these tools to request

* seismic waveform data, as mini-SEED, using the fdsnws-dataselect web service,

* seismic metadata, as FDSN Station XML, using the fdsnws-station web service.

* availability information, as JSON or POST format, using the fdsnws-availability web service.

There are four tools here:

#. `fdsnws_fetch` can request waveform data or metadata, from multiple data centres (access points) with a single command. It does this using the EIDA routing service to discover which data centre(s) holds the data requested.

#. `fdsnws2sds` supports requests for larger amounts of data, saving it in an SDS tree-like file system structure (the SeisComP Data Structure).
   SDS is defined `here <https://www.seiscomp.de/doc/apps/slarchive.html#slarchive-section-sds>`_.

#. `fdsnws2seed` provides full SEED and dataless SEED using EIDA FDSN web services. Modern applications should use FDSN StationXML instead of SEED.

#. `fdsnavail` lets the user interact with the new FDSN availability web service and compare to their local data holdings to find missing data.

Documentation
-------------

Detailed user and developer documentation is available at `Read the Docs <https://fdsnwsscripts.readthedocs.io/>`_
