#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""fdsnavail

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

   :Copyright:
       2019-2025 GFZ Helmholtz Centre for Geosciences
   :License:
       LGPLv3 GNU Lesser General Public License v. 3 (29 June 2007, or later)
   :Platform:
       Linux
"""

import sys
from fdsnwsscripts.seiscomp.mseedlite import Input
import os
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
from typing import Dict
from typing import List
from typing import Tuple
from typing import Iterable
from typing import Union
import requests
from json import dumps
import argparse


VERSION = "2023.191"


def str2date(dstr: str) -> Union[datetime, None]:
    """Transform a string to a datetime.

    :param dstr: A datetime in ISO format.
    :type dstr: str
    :return: A datetime represented the converted input.
    :rtype: datetime
    """
    # In case of empty string or None
    if dstr is None or not len(dstr):
        return None

    dateparts = dstr.replace('-', ' ').replace('T', ' ')
    dateparts = dateparts.replace(':', ' ').replace('.', ' ')
    dateparts = dateparts.replace('Z', '').split()
    return datetime(*map(int, dateparts))


def line2filter(line: str) -> str:
    """Convert a line potentially from a POST request to an equivalent string with key=value pairs
    to be used in a GET request

    :param line: Line from a POST request.
    :type line: str
    :return: Equivalent string to be used in a GET request with key/value pairs.
    :rtype: str
"""
    net, sta, loc, cha, starttime, endtime = line.split()
    result = ""
    if len(net) and net != '*':
        result += '&net=%s' % net
    if len(sta) and sta != '*':
        result += '&sta=%s' % sta
    if len(loc) and loc != '*':
        result += '&loc=%s' % loc
    if len(cha) and cha != '*':
        result += '&cha=%s' % cha
    if len(starttime) and starttime != '*':
        result += '&starttime=%s' % starttime
    if len(endtime) and endtime != '*':
        result += '&endtime=%s' % endtime
    return result


class Stream(namedtuple('Stream', ['net', 'sta', 'loc', 'cha', 'qua', 'sr'])):
    """Stream with the four components from NSLC code plus quality and sampling rate"""
    __slots__ = ()

    def strfilter(self) -> str:
        """Transform the Stream to a string with key/value pairs to be used in a GET request

        :return: Equivalent string to be used in a GET request with key/value pairs.
        :rtype: str
        """
        params = list()
        if self.net is not None and len(self.net):
            params.append('net=%s' % self.net)
        if self.sta is not None and len(self.sta):
            params.append('sta=%s' % self.sta)
        if self.loc is not None and len(self.loc):
            params.append('loc=%s' % self.loc)
        if self.cha is not None and len(self.cha):
            params.append('cha=%s' % self.cha)
        return '&'.join(params)


class Availability:
    pass


class Availability:
    """
    Availability information about streams
    """
    def __init__(self, stream: Stream = None, starttime: datetime = None, endtime: datetime = None,
                 postfile: str = None):
        # Dictionary to save extents
        self.__dict: Dict[Stream, list] = dict()

        # GEOFON Routing Service
        routing = 'https://geofon.gfz-potsdam.de/eidaws/routing/1/query'

        if postfile is not None:
            if (stream is not None) or (starttime is not None) or (endtime is not None):
                raise Exception('Using post_file is incompatible with the rest of the parameters')
            with open(postfile, 'r') as fin:
                # Query routes in post format for the availability web service
                routes = requests.post(routing, 'format=post\nservice=availability\n%s' % (fin.read(),))
                # print(routes.content)
        else:
            if stream is None:
                return

            auxurl = "%s?format=post&service=availability&%s" % (routing, stream.strfilter())
            if starttime is not None:
                auxurl += "&starttime=%s" % starttime.isoformat()
            if endtime is not None:
                auxurl += "&endtime=%s" % endtime.isoformat()
            # Query routes
            routes = requests.get(auxurl)

        dc = None
        # Read each route
        for line in routes.content.decode().splitlines():
            # Read the data centre if we don't have one
            if dc is None:
                dc = line
                continue

            # End of block. Next line will be a data centre URL
            if not len(line):
                dc = None
                continue

            # Read normal line and query to the availability DC
            # Load the dict from the response
            # print("%s?format=json&mergegaps=1.0&%s" % (dc, line2filter(line)))
            resp = requests.get("%s?format=json&mergegaps=1.0&%s" % (dc, line2filter(line)))
            if resp.status_code != 200:
                print('Error retrieving %s from %s' % (line, dc))
                continue
            # Read each stream from the availability
            for ds in resp.json()['datasources']:
                stream = Stream(ds['network'], ds['station'], ds['location'], ds['channel'], ds['quality'],
                                ds['samplerate'])
                # Read each time window
                for ts in ds['timespans']:
                    self.addchunk(stream, [str2date(ts[0]), str2date(ts[1])])

        # Show the availability
        # print(self.post())

    def __iter__(self) -> Iterable[Tuple]:
        for key in self.__dict.keys():
            for ts in self.__dict[key]:
                yield key, ts

    def __getitem__(self, item: Stream) -> List[datetime]:
        return self.__dict[item]

    def streams(self) -> Iterable[Stream]:
        """Return streams in this availability object"""
        return self.__dict.keys()

    def output(self, outformat: str='post') -> Union[str, dict]:
        """Return availability information in POST or JSON format

        :param outformat: Output format
        :type outformat: str
        :rtype: dict, str
        """
        if outformat == 'post':
            return self.post()
        if outformat == 'json':
            return dumps(self.json(), default=datetime.isoformat)
        raise Exception('Unrecognized output format')

    def json(self) -> dict:
        """Return availability information in JSON format compatible with the availability specification

        :rtype: dict
        """
        return {
            'created': datetime.utcnow(),
            'version': 1,
            'datasources': [{'network': st.net,
                             'station': st.sta,
                             'location': st.loc,
                             'channel': st.cha,
                             'quality': st.qua,
                             'samplerate': st.sr,
                             'timespans': self.__dict[st]
                             } for st in self.__dict]
        }

    def post(self) -> str:
        """Return availability information in POST format compatible with the availability specification

        :rtype: str
        """
        result = ""
        for st, ts in self:
            result += "%s %s %s %s %s %s\n" % (st.net, st.sta, st.loc if len(st.loc) else '--',
                                               st.cha, ts[0].isoformat(), ts[1].isoformat())
        return result

    def addchunk(self, streamid: Stream, newts: List[datetime]):
        """Add a new timewindow to this object. This method takes care of merging entries if the availability can be expressed in a more compact way.

        :param streamid: Stream to be added
        :type streamid: Stream
        :param newts: Time window to be added in the form of a list with two components
        :type newts: list
        """
        if newts[0] >= newts[1]:
            raise Exception('%s >= %s' % (newts[0], newts[1]))
        # key = Stream(net, sta, loc, cha, qua, sr)
        tol = timedelta(seconds=1.0/streamid.sr)

        # First chunk added
        if streamid not in self.__dict:
            self.__dict[streamid] = [[newts[0], newts[1]]]
            return

        for timespan in self.__dict[streamid]:
            # Too early
            if newts[0] > timespan[1] + tol:
                continue
            if timespan[0] - tol < newts[0] <= timespan[1] + tol:
                timespan[1] = max(timespan[1], newts[1])
                return
            if (newts[0] < timespan[0] - tol) and (newts[1] > timespan[0] - tol):
                timespan[0] = newts[0]
                timespan[1] = max(timespan[1], newts[1])
                return

            if newts[1] < timespan[0] - tol:
                timespan[0] = newts[0]
                timespan[1] = max(timespan[1], newts[1])
                return

        # Add the chunk at the end because it is completely new and without overlaps
        self.__dict[streamid].append([newts[0], newts[1]])

    def __iadd__(self, other: Availability):
        itother = iter(other)
        for st, lts in itother:
            # print(st, lts)
            self.addchunk(st, lts)
            # print('self', self.__dict)

    def __sub__(self, other: Availability) -> Availability:
        # streams = set(self.streams())
        # streams.update(other.streams())

        resdiff = Availability()

        itself = iter(self)
        for st1, ts1 in itself:
            # We can duplicate the list of timespans and reduce/delete as we find the equivalent in the other list
            aux1 = ts1.copy()
            # print('Evaluating %s %s' % (st1, ts1))
            try:
                for ts2 in other[st1]:
                    # We are in the same stream
                    # How to calculate the difference in timewindow?
                    # If the other timewindow ends too early, just discard it
                    if ts2[1] < aux1[0]:
                        continue

                    if ts2[1] < aux1[1]:
                        # Substract the timewindow that is already present ( < ts2[1] )
                        aux1[0] = ts2[1]
                        continue

                    if ts2[1] > aux1[1]:
                        # TODO Potential error here
                        # If there is a gap on the left AND it is longer than the sampling rate
                        secs = (min(aux1[1], ts2[0]) - aux1[0]).total_seconds()
                        if (aux1[0] < ts2[0]):
                            if (secs > 1.0/st1.sr):
                                # print('Missing part: %s, %s' % (aux1[0], min(aux1[1], ts2[0])))
                                resdiff.addchunk(st1, [aux1[0], min(aux1[1], ts2[0])])
                            # else:
                                # print('Discarding: %s, %s' % (aux1[0], min(aux1[1], ts2[0])))
                        break
                else:
                    # We couldn't find a matching time window in the "other" object
                    # print('Missing part: %s, %s' % (aux1[0], aux1[1]))
                    resdiff.addchunk(st1, [aux1[0], aux1[1]])

            except KeyError:
                # print('Stream %s not found -> Adding %s' % (st1, ts1))
                resdiff.addchunk(st1, ts1)
                continue

        return resdiff

    def __str__(self) -> str:
        return self.post()

    def __repr__(self) -> str:
        return dumps(self.json(), default=datetime.isoformat)


def mseed2avail(directory: str) -> Availability:
    """Scan all the files with extension ".mseed" in the directory passed as input parameter.

    :param directory: Directory where the files should be scanned
    :type directory: str
    :returns: Availability information from the mseed files
    :rtype: Availability
    """
    scanresult = Availability()
    for file in os.scandir(directory):
        if not file.name.endswith('.mseed'):
            continue

        with open(file.path, 'rb') as fin:
            for rec in Input(fin):
                streamid = Stream(rec.net, rec.sta, rec.loc, rec.cha, rec.rectype, rec.fsamp)
                # print("%s.%s.%s.%s %s %s" % (rec.net, rec.sta, rec.loc, rec.cha, rec.begin_time, rec.end_time))
                scanresult.addchunk(streamid, [rec.begin_time, rec.end_time])

    return scanresult


# FIXME This is based on scan_sds. Check if we could merge them at some moment (fsdnws_fetch.py)
def sds2avail(directory: str) -> Availability:
    """Scan all the files with extension ".mseed" in the directory passed as input parameter

    :param directory: Directory where the root of the SDS is located
    :type directory: str
    :returns: Availability information from the SDS structure
    :rtype: Availability
"""
    scanresult = Availability()

    def scan_cha(d: str):
        aux, realcha = os.path.split(d)
        realcha = realcha[:-2]
        aux, realsta = os.path.split(aux)
        aux, realnet = os.path.split(aux)
        aux, realyear = os.path.split(aux)
        for f in os.scandir(d):
            try:
                (net, sta, loc, cha, ext, yr, doy) = f.name.split('.')
                # Check that the filename components are coherent with the directory ones
                if (realyear != yr) or (realnet != net) or (realsta != sta) or (realcha != cha):
                    raise ValueError
            except ValueError:
                print("invalid SDS file: " + f.name)
                continue

            with open(f.path, 'rb') as fin:
                for rec in Input(fin):
                    # Check that the record header components are coherent with the rest of the information
                    if (realnet != rec.net) or (realsta != rec.sta) or (realcha != rec.cha):
                        print('Skipping file with incoherent headers! (%s)' % f.name)
                        continue
                    streamid = Stream(rec.net, rec.sta, rec.loc, rec.cha, rec.rectype, rec.fsamp)
                    # print("%s.%s.%s.%s %s %s" % (rec.net, rec.sta, rec.loc, rec.cha, rec.begin_time, rec.end_time))
                    scanresult.addchunk(streamid, [rec.begin_time, rec.end_time])

                # First approach was to take the first and last record, but the gaps in the middle would be missing!
                # # Check first record
                # rec = Record(fd)
                # filestart = rec.begin_time
                # # Check last record
                # fd.seek(-rec.size, 2)
                # rec = Record(fd)
                # fileend = rec.end_time
                # streamid = Stream(rec.net, rec.sta, rec.loc, rec.cha, rec.rectype, rec.fsamp)
                # print("%s.%s.%s.%s %s %s" % (rec.net, rec.sta, rec.loc, rec.cha, rec.begin_time, rec.end_time))
                # scanresult.addchunk(streamid, [filestart, fileend])

    def scan_sta(d: str):
        for cha in os.scandir(d):
            if not cha.is_dir():
                continue
            if not cha.name.endswith('.D'):
                continue
            scan_cha(cha.path)

    def scan_net(d: str):
        for sta in os.scandir(d):
            if not sta.is_dir():
                continue
            scan_sta(sta.path)

    def scan_year(d: str):
        for net in os.scandir(d):
            if not net.is_dir():
                continue
            scan_net(net.path)

    for year in os.scandir(directory):
        if not year.is_dir():
            continue
        try:
            int(year.name)
        except ValueError:
            continue
        scan_year(year.path)

    return scanresult


def __query__(args) -> Availability:
    if args.post_file is not None:
        remote = Availability(postfile=args.post_file)
        # print(remote)
    else:
        params = list()
        if args.network is not None:
            params.append('net=%s' % args.network)
        if args.station is not None:
            params.append('sta=%s' % args.station)
        if args.location is not None:
            params.append('loc=%s' % args.location)
        if args.channel is not None:
            params.append('cha=%s' % args.channel)
        if args.starttime is not None:
            str2date(args.starttime)
            params.append('start=%s' % args.starttime)
        if args.endtime is not None:
            str2date(args.endtime)
            params.append('end=%s' % args.endtime)
        # Retrieve the availability for the selected streams/time windows
        remote = Availability(Stream(args.network, args.station, args.location, args.channel, None, None),
                              str2date(args.starttime), str2date(args.endtime))
    return remote


def query(args):
    remote = __query__(args)
    # Save the availability
    # print(remote.post())
    if args.output_file is None:
        print(remote.output(outformat=args.output_format))
        return

    with open(args.output_file, 'wt') as fout:
        fout.write(remote.output(outformat=args.output_format))


def __scan__(args) -> Availability:
    if args.structure == 'sds':
        return sds2avail(args.directory)
    if args.structure == 'files':
        return mseed2avail(args.directory)

    print('Other types of structure than SDS, or "*.mseed" files in a directory are still not supported')
    sys.exit(-2)


def scan(args):
    result = __scan__(args)

    # Save/show results
    if args.output_file is None:
        print(result.post())
        return

    with open(args.output_file, 'wt') as fout:
        fout.write(result.post())


def __compare__(args) -> Availability:
    remote = __query__(args)
    # print(remote.post())
    local = __scan__(args)
    # print(local.post())
    return remote - local


def compare(args):
    result = __compare__(args)

    # TODO We need a method in Availability to filter/discard very short timewindows (e.g. < 1s)
    # Save/show results
    if args.output_file is None:
        print(result.post())
        return

    with open(args.output_file, 'wt') as fout:
        fout.write(result.post())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version", action='version', version="%(prog)s " + VERSION)
    # parser.add_argument("-u", "--url", default="geofon.gfz-potsdam.de",
    #                     help="URL of availability web service. (default is EIDA).")

    subparserhelp = """Commands:"""
    subparsers = parser.add_subparsers(help=subparserhelp)

    # create the parser for the "query" command
    parser_query = subparsers.add_parser('query', help='Request availability data from a web service')
    parser_query.add_argument("-N", "--network", type=str, default=None, help="Network code")
    parser_query.add_argument("-S", "--station", type=str, default=None, help="Station code")
    parser_query.add_argument("-L", "--location", type=str, default=None, help="Location code")
    parser_query.add_argument("-C", "--channel", type=str, default=None, help="Channel code")
    parser_query.add_argument("-s", "--starttime", type=str, default=None, help="start time")
    parser_query.add_argument("-e", "--endtime", type=str, default=None, help="end time")
    parser_query.add_argument("--gap-tolerance", type=float, default=1.0, help="Tolerance in seconds for gap detection")
    parser_query.add_argument("-p", "--post-file", type=str, default=None, help="request file in FDSNWS POST format")
    parser_query.add_argument("-o", "--output-file", type=str, default=None,
                              help="file where informed availability is written")
    parser_query.add_argument("-f", "--output-format", type=str, default='post', choices=['post', 'json'],
                              help="format used to save the availability data (default: post)")
    parser_query.set_defaults(func=query)

    # create the parser for the "scan" command
    parser_scan = subparsers.add_parser('scan', help='Scan the local data holdings in miniseed and generate the availability as returned by a web service')
    parser_scan.add_argument("-d", "--directory", type=str, default=None, help="Root directory of the data holdings")
    parser_scan.add_argument("--structure", type=str, default='files', help="Organization of the data holdings",
                             choices=['files', 'sds'])
    parser_scan.add_argument("-o", "--output-file", type=str, default=None,
                             help="file where the result of the scan is written")
    parser_scan.add_argument("-f", "--output-format", type=str, default='post', choices=['post', 'json'],
                             help="format used to save the scan result (default: post)")
    parser_scan.set_defaults(func=scan)

    # Create the parser for the "compare" command
    helptxt = 'Compare the availability from a web service with the one from the local data'
    parser_compare = subparsers.add_parser('compare', help=helptxt)
    parser_compare.add_argument("-N", "--network", type=str, default=None, help="Network code")
    parser_compare.add_argument("-S", "--station", type=str, default=None, help="Station code")
    parser_compare.add_argument("-L", "--location", type=str, default=None, help="Location code")
    parser_compare.add_argument("-C", "--channel", type=str, default=None, help="Channel code")
    parser_compare.add_argument("-s", "--starttime", type=str, default=None, help="start time")
    parser_compare.add_argument("-e", "--endtime", type=str, default=None, help="end time")
    parser_compare.add_argument("--gap-tolerance", type=float, default=1.0,
                                help="Tolerance in seconds for gap detection")
    parser_compare.add_argument("-p", "--post-file", type=str, default=None, help="request file in FDSNWS POST format")
    parser_compare.add_argument("-d", "--directory", type=str, default=None, help="Root directory of the data holdings")
    parser_compare.add_argument("--structure", type=str, default='files', help="Organization of the data holdings",
                                choices=['sds', 'files'])
    parser_compare.add_argument("-o", "--output-file", type=str, default=None,
                                help="file where the result of the comparison is written")
    parser_compare.add_argument("-f", "--output-format", type=str, default='post', choices=['post', 'json'],
                                help="format used to save the comparison (default: post)")
    parser_compare.set_defaults(func=compare)
    args = parser.parse_args()

    # Call one of the three functions defined (query, scan, compare)
    args.func(args)


if __name__ == '__main__':
    main()
