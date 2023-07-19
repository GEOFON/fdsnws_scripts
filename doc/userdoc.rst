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
on `FDSN web services <https://www.fdsn.org/webservices>`_ and the
`EIDA routing service <https://www.orfeus-eu.org/data/eida/eidaws/routing>`_.

You may use these tools to request:

* seismic waveform data, as mini-SEED, using the fdsnws-dataselect web service,
* seismic metadata, as FDSN Station XML, using the fdsnws-station web service.

There are four tools here:

* `fdsnws_fetch` can request waveform data or metadata, from multiple data centres (access points)
  with a single command. It does this using the EIDA routing service to discover which data centre(s)
  holds the data requested.
* `fdsnws2sds` supports requests for larger amounts of data, saving it in an SDS tree-like file system
  structure (the SeisComP Data Structure). SDS is defined
  `here <https://www.seiscomp.de/doc/apps/slarchive.html#slarchive-section-sds>`_.
* `fdsnws2seed` provides full SEED and dataless SEED using EIDA FDSN web services. Modern applications
  should use FDSN StationXML instead of SEED.
* `fdsnavail` provides three different commands to: _query_ the new availability web services, _scan_
  your local data holdings and give you a result as the availability web service, and _compare_ your
  local data with what it has been declared in the data centre and provide you a list of what you miss.

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

The following command-line options are common to almost all scripts: ::

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


fdsnavail
=========

`fdsnavail` lets the user interact with the new availability web service deployed at many data centres.
There are three modes of operation: `query`, `scan`, and `compare`.

Command-line options
--------------------

For each of the three modes there is a different number of parameters. The general options are: ::

    % fdsnavail -h
    usage: fdsnavail [-h] [-V] {query,scan,compare} ...

    positional arguments:
      {query,scan,compare}  Commands:
        query               Request availability data from a web service
        scan                Scan the local data holdings in miniseed and generate the availability as returned by a web service
        compare             Compare the availability from a web service with the one from the local data

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         show program's version number and exit

For the `query` command you have the following options: ::

    % fdsnavail query -h
    usage: fdsnavail query [-h] [-N NETWORK] [-S STATION] [-L LOCATION] [-C CHANNEL] [-s STARTTIME] [-e ENDTIME] [--gap-tolerance GAP_TOLERANCE] [-p POST_FILE] [-o OUTPUT_FILE]
                           [-f {post,json}]

    optional arguments:
      -h, --help            show this help message and exit
      -N NETWORK, --network NETWORK
                            Network code
      -S STATION, --station STATION
                            Station code
      -L LOCATION, --location LOCATION
                            Location code
      -C CHANNEL, --channel CHANNEL
                            Channel code
      -s STARTTIME, --starttime STARTTIME
                            start time
      -e ENDTIME, --endtime ENDTIME
                            end time
      --gap-tolerance GAP_TOLERANCE
                            Tolerance in seconds for gap detection
      -p POST_FILE, --post-file POST_FILE
                            request file in FDSNWS POST format
      -o OUTPUT_FILE, --output-file OUTPUT_FILE
                            file where informed availability is written
      -f {post,json}, --output-format {post,json}
                            format used to save the availability data (default: post)

For the `scan` mode you have: ::

    % fdsnavail scan -h
    usage: fdsnavail scan [-h] [-d DIRECTORY] [--structure {files,sds}] [-o OUTPUT_FILE] [-f {post,json}]

    optional arguments:
      -h, --help            show this help message and exit
      -d DIRECTORY, --directory DIRECTORY
                            Root directory of the data holdings
      --structure {files,sds}
                            Organization of the data holdings
      -o OUTPUT_FILE, --output-file OUTPUT_FILE
                            file where the result of the scan is written
      -f {post,json}, --output-format {post,json}
                            format used to save the scan result (default: post)

and in the `compare` mode: ::

    % fdsnavail compare -h
    usage: fdsnavail compare [-h] [-N NETWORK] [-S STATION] [-L LOCATION] [-C CHANNEL] [-s STARTTIME] [-e ENDTIME] [--gap-tolerance GAP_TOLERANCE] [-p POST_FILE] [-d DIRECTORY]
                             [--structure {sds,files}] [-o OUTPUT_FILE] [-f {post,json}]

    optional arguments:
      -h, --help            show this help message and exit
      -N NETWORK, --network NETWORK
                            Network code
      -S STATION, --station STATION
                            Station code
      -L LOCATION, --location LOCATION
                            Location code
      -C CHANNEL, --channel CHANNEL
                            Channel code
      -s STARTTIME, --starttime STARTTIME
                            start time
      -e ENDTIME, --endtime ENDTIME
                            end time
      --gap-tolerance GAP_TOLERANCE
                            Tolerance in seconds for gap detection
      -p POST_FILE, --post-file POST_FILE
                            request file in FDSNWS POST format
      -d DIRECTORY, --directory DIRECTORY
                            Root directory of the data holdings
      --structure {sds,files}
                            Organization of the data holdings
      -o OUTPUT_FILE, --output-file OUTPUT_FILE
                            file where the result of the comparison is written
      -f {post,json}, --output-format {post,json}
                            format used to save the comparison (default: post)

Example
-------

A typical example regarding a usual workflow could be the following.

A user requests the availability for some data that (s)he wants to get and saves it in the file `remote.txt` for later use.
For instance, three days of data from GE.APE.*.BH?. ::

    % fdsnavail query -N GE -S APE -C "BH?" -s "2001-02-01" -e "2001-02-03" -o remote.txt
    javier@sec24-dynip-171 temp2 % cat remote.txt
    GE APE -- BHE 2001-02-01T06:41:54.215000 2001-02-01T06:44:43.015000
    GE APE -- BHE 2001-02-01T07:14:59.112000 2001-02-01T23:09:37.812000
    GE APE -- BHE 2001-02-02T06:47:42.215000 2001-02-02T07:02:58.915000
    GE APE -- BHE 2001-02-02T07:28:36.215000 2001-02-02T07:31:54.235000
    GE APE -- BHE 2001-02-02T07:32:54.235000 2001-02-02T18:58:45.935000
    GE APE -- BHN 2001-02-01T06:41:54.215000 2001-02-01T06:44:22.915000
    GE APE -- BHN 2001-02-01T07:14:59.112000 2001-02-01T23:08:47.812000
    GE APE -- BHN 2001-02-02T06:29:49.215000 2001-02-02T06:32:53.715000
    GE APE -- BHN 2001-02-02T06:47:42.215000 2001-02-02T07:03:52.015000
    GE APE -- BHN 2001-02-02T07:28:36.215000 2001-02-02T07:31:54.535000
    GE APE -- BHN 2001-02-02T07:32:54.535000 2001-02-02T18:59:54.935000
    GE APE -- BHZ 2001-02-01T06:41:54.215000 2001-02-01T06:44:53.215000
    GE APE -- BHZ 2001-02-01T07:14:59.112000 2001-02-01T23:10:36.712000
    GE APE -- BHZ 2001-02-02T06:29:49.215000 2001-02-02T06:32:54.615000
    GE APE -- BHZ 2001-02-02T06:47:42.215000 2001-02-02T07:03:48.415000
    GE APE -- BHZ 2001-02-02T07:28:36.215000 2001-02-02T07:31:54.635000
    GE APE -- BHZ 2001-02-02T07:32:54.635000 2001-02-02T19:00:43.635000

Now, with all available data defined in the `remote.txt` file, the user knows exactly which data to request
and that all these data should be received, as this is what the data centre declares to have. Namely, there
should be no exceptions. The user requests the data by means of `fdsnws_fetch` and saves it in `GE.APE.mseed`. ::

    % fdsnws_fetch -p remote.txt -o GE.APE.mseed

    You received seismic waveform data from the following network(s):
    GE GEOFON Program, GFZ Potsdam, Germany

    Acknowledgment is extremely important for network operators
    providing open data. When preparing publications, please
    cite the data appropriately. The FDSN service at

        http://www.fdsn.org/networks/citation/?networks=GE

    provides a helpful guide based on available network
    Digital Object Identifiers.

    % ls -lh GE.APE.mseed
    -rw-r--r--  1 user  staff   6.4M Jul 19 17:59 GE.APE.mseed

You can check details about the data you downloaded with the `scan` command. Just to be sure what you have received. ::

    % fdsnavail scan -f post -d .
    GE APE -- BHE 2001-02-01T06:41:54.215867 2001-02-01T06:44:43.015867
    GE APE -- BHE 2001-02-01T07:14:59.112276 2001-02-01T23:09:37.821675
    GE APE -- BHE 2001-02-02T06:47:42.215867 2001-02-02T07:02:58.915867
    GE APE -- BHE 2001-02-02T07:28:36.215867 2001-02-02T07:31:54.235700
    GE APE -- BHE 2001-02-02T07:32:54.235736 2001-02-02T18:58:45.946361
    GE APE -- BHN 2001-02-01T06:41:54.215867 2001-02-01T06:44:22.915867
    GE APE -- BHN 2001-02-01T07:14:59.112277 2001-02-01T23:08:47.821659
    GE APE -- BHN 2001-02-02T06:29:49.215867 2001-02-02T06:32:53.715867
    GE APE -- BHN 2001-02-02T06:47:42.215867 2001-02-02T07:03:52.015867
    GE APE -- BHN 2001-02-02T07:28:36.215867 2001-02-02T07:31:54.535700
    GE APE -- BHN 2001-02-02T07:32:54.535736 2001-02-02T18:59:54.946376
    GE APE -- BHZ 2001-02-01T06:41:54.215867 2001-02-01T06:44:53.215867
    GE APE -- BHZ 2001-02-01T07:14:59.112277 2001-02-01T23:10:36.721690
    GE APE -- BHZ 2001-02-02T06:29:49.215867 2001-02-02T06:32:54.615867
    GE APE -- BHZ 2001-02-02T06:47:42.215867 2001-02-02T07:03:48.415867
    GE APE -- BHZ 2001-02-02T07:28:36.215867 2001-02-02T07:31:54.635700
    GE APE -- BHZ 2001-02-02T07:32:54.635736 2001-02-02T19:00:43.646391

But the most useful thing to do is to `compare` your local data with the data at the data centre.
In this way, you know **exactly** if you miss some data or not.
For instance, let's do the comparison between what we have (downloaded in the previous step) and
the data declared by the availability web service. ::

    % fdsnavail compare -d . -N GE -S APE -C "BH?" -s "2001-02-01" -e "2001-02-03" -o diff.txt
    % cat diff.txt
    % ls -lh diff.txt
    -rw-r--r--  1 user  staff     0B Jul 19 18:16 diff.txt

We can see that we don't miss any data.

To check that this is actually working, we could think that some days later we want to get more data.
For instance, one day more (until 2001-02-04). Then, we check what we already have with the data we would like to have.
For instance, ::

    % fdsnavail compare -d . -N GE -S APE -C "BH?" -s "2001-02-01" -e "2001-02-04" -o diff.txt
    javier@sec24-dynip-171 temp2 % cat diff.txt
    GE APE -- BHE 2001-02-03T10:39:26.215000 2001-02-03T11:01:38.515000
    GE APE -- BHE 2001-02-03T11:30:58.436000 2001-02-03T11:36:05.836000
    GE APE -- BHN 2001-02-03T10:39:26.215000 2001-02-03T11:03:03.915000
    GE APE -- BHN 2001-02-03T11:30:58.436000 2001-02-03T11:36:14.036000
    GE APE -- BHZ 2001-02-03T10:39:26.215000 2001-02-03T11:03:11.415000
    GE APE -- BHZ 2001-02-03T11:30:58.436000 2001-02-03T11:33:46.436000

We can then see, that we miss some time windows related to the day 2001-02-03, that we hadn't requested previously.
The default output format is `post`, what is very practical to later submit it via `fdsnws_fetch` or any other client you
would like to use, as this is the expected format for the dataselect web service.
