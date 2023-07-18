User documentation
##################

License
=======

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Summary
=======

fdsnwsscripts is a collection of next generation distributed data request tools that are based
on `FDSN web services <https://www.fdsn.org/webservices>` and the
`EIDA routing service <https://www.orfeus-eu.org/data/eida/eidaws/routing>`.

Installation
============

The easiest way to install this packege is by means of `pip`. ::

  $ pip3 install fdsnwsscripts

Download
--------

If you would like to install it from the source code, you can download the code from the Github
repository of GEOFON at https://github.com/GEOFON/fdsnws_scripts.git ::

  $ git clone https://github.com/GEOFON/fdsnws_scripts.git
  $ cd fdsnws_scripts

and then install it with `pip`. ::

  $ pip3 install -e .

Requirements
------------

 * Python 3.6+

Testing the software
--------------------

You can test some of the functionality of the package by means of `pytest`. Just run it in the root folder
of the cloned repository. ::

    % pytest --cov .
    ===================== test session starts ============================
    platform darwin -- Python 3.9.0, pytest-7.2.0, pluggy-1.0.0
    rootdir: /Users/javier/git/fdsnws_scripts
    plugins: cov-4.0.0, anyio-3.6.2
    collected 10 items

    fdsnwsscripts/test_fdsnavail.py ..........                                                                                                                                           [100%]

    ---------- coverage: platform darwin, python 3.9.0-final-0 -----------
    Name                                             Stmts   Miss  Cover
    --------------------------------------------------------------------
    fdsnwsscripts/__init__.py                            0      0   100%
    fdsnwsscripts/fdsnavail.py                         313     98    69%
    fdsnwsscripts/fdsnws2sds.py                        273    273     0%
    fdsnwsscripts/fdsnws2seed.py                       191    191     0%
    fdsnwsscripts/fdsnws_fetch.py                      706    706     0%
    fdsnwsscripts/fdsnxml2arclink.py                    38     38     0%
    fdsnwsscripts/seiscomp/__init__.py                   0      0   100%
    fdsnwsscripts/seiscomp/db/__init__.py                3      3     0%
    fdsnwsscripts/seiscomp/db/generic/__init__.py        0      0   100%
    fdsnwsscripts/seiscomp/db/generic/inventory.py     808    808     0%
    fdsnwsscripts/seiscomp/db/xmlio/__init__.py          0      0   100%
    fdsnwsscripts/seiscomp/db/xmlio/inventory.py       732    732     0%
    fdsnwsscripts/seiscomp/db/xmlio/xmlwrap.py        3312   3312     0%
    fdsnwsscripts/seiscomp/fdsnxml.py                  584    584     0%
    fdsnwsscripts/seiscomp/fseed.py                   1802   1802     0%
    fdsnwsscripts/seiscomp/logs.py                      23     23     0%
    fdsnwsscripts/seiscomp/mseedlite.py                275    123    55%
    fdsnwsscripts/test_fdsnavail.py                    130      0   100%
    setup.py                                             7      7     0%
    --------------------------------------------------------------------
    TOTAL                                             9197   8700     5%

    ======================== 10 passed in 7.28s ========================




Common command-line options
===========================

The following command-line options are common to all scripts: ::

    --version:
    show program's version number and exit

    -h, --help:
    show help message and exit

    -v, --verbose:
    verbose mode

    -u URL, --url=URL:
    URL of routing service (default https://geofon.gfz-potsdam.de/eidaws/routing/1/)

    -N NETWORK, --network=NETWORK:
    network code or pattern

    -S STATION, --station=STATION:
    station code or pattern

    -L LOCATION, --location=LOCATION:
    location code or pattern

    -C CHANNEL, --channel=CHANNEL:
    channel code or pattern

    -s STARTTIME, --starttime=STARTTIME:
    start time

    -e ENDTIME, --endtime=ENDTIME:
    end time

    -t TIMEOUT, --timeout=TIMEOUT:
    request timeout in seconds (default 600)

    -r RETRIES, --retries=RETRIES:
    number of retries (default 10)

    -w RETRY_WAIT, --retry-wait=RETRY_WAIT:
    seconds to wait before each retry (default 60)

    -n THREADS, --threads=THREADS:
    maximum number of download threads (default 5)

    -c CREDENTIALS_FILE, --credentials-file=CREDENTIALS_FILE:
    URL,user,password file (CSV format) for queryauth

    -a AUTH_FILE, --auth-file=AUTH_FILE:
    file that contains the auth token


fdsnws_fetch
============

fdsnws_fetch can be used to request data from FDSNWS dataselect or station service
(with EIDA routing), based on command-line parameters or a request file in ArcLink,
Breq_Fast or FDSNWS POST format. Result is saved in a single miniSEED file.

Additional command-line options
-------------------------------
::

    -l, --longhelp:
    show extended help message and exit

    -y SERVICE, --service=SERVICE:
    target service (default dataselect)

    -q PARAMETER=VALUE, --query=PARAMETER=VALUE:
    additional query parameter

    -p POST_FILE, --post-file=POST_FILE:
    request file in FDSNWS POST format

    -f ARCLINK_FILE, --arclink-file=ARCLINK_FILE:
    request file in ArcLink format

    -b BREQFAST_FILE, --breqfast-file=BREQFAST_FILE:
    request file in breq_fast format

    -o OUTPUT_FILE, --output-file=OUTPUT_FILE:
    file where downloaded data is written

    -z, --no-citation
    suppress network citation info

    -Z, --no-check
    suppress checking received routes and data


Examples
--------
Request 60 minutes of the "LHZ" channel of EIDA stations starting with "A" for a seismic event
around 2010-02-27 07:00 (UTC). Optionally add "-v" for verbosity. Resulting Mini-SEED data
will be written to file "data.mseed". ::

  $ fdsnws_fetch -N '*' -S 'A*' -L '*' -C 'LHZ' -s "2010-02-27T07:00:00Z" -e "2010-02-27T08:00:00Z" -v -o data.mseed

The above request is anonymous and therefore restricted data will not be included. To include
restricted data, use a file containing a token obtained from an EIDA authentication service and/or
a CSV file with username and password for each node not implementing the EIDA auth extension. ::

  $ fdsnws_fetch -a token.asc -c credentials.csv -N '*' -S 'A*' -L '*' -C 'LHZ' -s "2010-02-27T07:00:00Z" -e "2010-02-27T08:00:00Z" -v -o data.mseed

StationXML metadata for the above request can be requested using the following command: ::

  $ fdsnws_fetch -N '*' -S 'A*' -L '*' -C 'LHZ' -s "2010-02-27T07:00:00Z" -e "2010-02-27T08:00:00Z" -y station -q level=response -v -o station.xml

Multiple query parameters can be used: ::

  $ fdsnws_fetch -N '*' -S '*' -L '*' -C '*' -s "2010-02-27T07:00:00Z" -e "2010-02-27T08:00:00Z" -y station -q format=text -q level=channel -q latitude=20 -q longitude=-150 -q maxradius=15 -v -o station.txt

Bulk requests can be made in ArcLink (-f), breq_fast (-b) or native FDSNWS POST (-p) format.
Query parameters should not be included in the request file, but specified on the command line. ::

  $ cat >req.arclink
  2010,02,18,12,00,00 2010,02,18,12,10,00 GE WLF BH*
  2010,02,18,12,00,00 2010,02,18,12,10,00 GE VSU BH*

  $ fdsnws_fetch -f req.arclink -y station -q level=channel -v -o station.xml

In order to access restricted data, you need an authentication token that can be obtained by
sending an email to breqfast@webdc.eu, containing ::

  .AUTH your_email_address

The location of token file can be specified with "-a"; if `${HOME}/.eidatoken` exists, it is used by default.


fdsnws2sds
==========

`fdsnws2sds` can be used to download large amounts of waveform data from EIDA FDSN web
services. Compared to `fdsnws_fetch`

* Only command-line options can be used, no request files.
* Only waveform requests are supported.
* Large requests are automatically split into small pieces to avoid exceeding limits.
* Data is saved as SDS structure.
* Download can be stopped and restarted.

Additional command-line options
-------------------------------
::

    -o OUTPUT_DIR, --output-dir=OUTPUT_DIR:
    SDS directory where downloaded data is written

    -l MAX_LINES, --max-lines=MAX_LINES
    max lines per request (default 1000)

    -m MAX_TIMESPAN, --max-timespan=MAX_TIMESPAN
    max timespan per request in minutes (default 1440)

    -z, --no-citation
    suppress network citation info

    -Z, --no-check
    suppress checking received routes and data

Example
-------
::

  $ fdsnws2sds -N 7G -s 2014-04-01 -e 2018-01-01 -o SDS



fdsnws2seed
===========

`fdsnws2seed` can be used to obtain full SEED and dataless SEED data with EIDA FDSN web
services. Usage of `fdsnws2seed` is recommended when SEED format is required for compatibility
with old applications. New applications should use FDSN StationXML instead of SEED.

Additional command-line options
-------------------------------
::

    -q PARAMETER=VALUE, --query=PARAMETER=VALUE:
    additional query parameter

    -p POST_FILE, --post-file=POST_FILE:
    request file in FDSNWS POST format

    -f ARCLINK_FILE, --arclink-file=ARCLINK_FILE:
    request file in ArcLink format

    -b BREQFAST_FILE, --breqfast-file=BREQFAST_FILE:
    request file in breq_fast format

    -d, --dataless:
    create dataless SEED volume

    -l LABEL, --label=LABEL:
    label of SEED volume

    -o OUTPUT_FILE, --output-file=OUTPUT_FILE:
    file where SEED data is written

    -z, --no-citation
    suppress network citation info

    -Z, --no-check
    suppress checking received routes and data

Example
-------
::

    $ cat >req.breq
    .NAME Joe Seismologist
    .INST GFZ Potsdam
    .END
    WLF GE 2017 08 01 12 00 00.0000 2017 08 01 12 10 00.0000 01 BH?

    $ ./fdsnws2seed -v -r 1 -b req.breq -o req.seed

