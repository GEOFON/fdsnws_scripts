#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from fdsnwsscripts.seiscomp.mseedlite import Input
from fdsnwsscripts.seiscomp.mseedlite import Record
import os
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
from pprint import pprint
from typing import Dict
from typing import List
from typing import Tuple
from typing import Iterable
import requests
from json import dumps
import argparse


VERSION = "2023.153"


def str2date(dstr):
    """Transform a string to a datetime.

    :param dstr: A datetime in ISO format.
    :type dstr: string
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
    __slots__ = ()

    def strfilter(self):
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
    def __init__(self, stream: Stream, starttime: datetime, endtime: datetime, postfile: str = None):
        # Dictionary to save extents
        self.__dict: Dict[Stream, list] = dict()

        # GEOFON Routing Service
        routing = 'https://geofon.gfz-potsdam.de/eidaws/routing/1/query?format=post&service=availability'
        # If the selection is received via parameters
        if postfile is None:
            auxurl = "%s&%s" % (routing, stream.strfilter())
            if starttime is not None:
                auxurl += "&starttime=%s" % starttime.isoformat()
            if endtime is not None:
                auxurl += "&endtime=%s" % endtime.isoformat()
            # Query routes
            routes = requests.get(auxurl)
        # If there is a post file as input
        else:
            with open(postfile, 'r') as fin:
                # Query routes
                routes = requests.post(routing, fin.read())

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

    def __getitem__(self, item) -> List[datetime]:
        return self.__dict[item]

    def streams(self) -> Iterable[Stream]:
        return self.__dict.keys()

    def json(self):
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

        result = ""
        for st, ts in self:
            result += "%s %s %s %s %s %s\n" % (st.net, st.sta, st.loc, st.cha, ts[0].isoformat(), ts[1].isoformat())
        return result

    def addchunk(self, streamid: Stream, newts: List[datetime]):
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
                                print('Missing part: %s, %s' % (aux1[0], min(aux1[1], ts2[0])))
                                resdiff.addchunk(st1, [aux1[0], min(aux1[1], ts2[0])])
                            else:
                                print('Discarding: %s, %s' % (aux1[0], min(aux1[1], ts2[0])))
                        break
            except KeyError:
                # print('Stream %s not found -> Adding %s' % (st1, ts1))
                resdiff.addchunk(st1, ts1)
                continue

        return resdiff

    def __str__(self) -> str:
        return dumps(self.json(), default=datetime.fromisoformat)


def mseed2avail(directory: str):
    scanresult = Availability()
    for file in os.listdir(directory):
        if not file.endswith('.mseed'):
            continue

        with open(file, 'rb') as fin:
            for rec in Input(fin):
                streamid = Stream(rec.net, rec.sta, rec.loc, rec.cha, rec.rectype, rec.fsamp)
                # print("%s.%s.%s.%s %s %s" % (rec.net, rec.sta, rec.loc, rec.cha, rec.begin_time, rec.end_time))
                scanresult.addchunk(streamid, [rec.begin_time, rec.end_time])

    return scanresult


def query(args):
    if args.post_file is not None:
        sys.exit(-2)
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

    # Save the availability
    # print(remote.post())
    if args.output_file is None:
        print(remote.post())
        return

    with open(args.output_file, 'wt') as fout:
        fout.write(remote.post())


def scan(args):
    pass


def compare(args):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version", action='version', version="%(prog)s " + VERSION)
    parser.add_argument("-u", "--url", default="geofon.gfz-potsdam.de",
                        help="URL of availability web service. (default is EIDA).")
    parser.add_argument("-o", "--output-file", type=str, default=None, help="file where downloaded data is written")
    parser.add_argument("-f", "--output-format", type=str, default='post',
                        help="format to save the availability data (default: post)")

    subparserhelp = """
    There are three commands you can run with this utility:
    query: to request the availability for the streams specified in the input parameters
    scan: to read all miniseed files in a directory,
    compare: to compare the result from an availability web service against your local data
    """
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
    parser_query.set_defaults(func=query)
    args = parser.parse_args()

    # Call one of the three functions defined (query, scan, compare)
    args.func(args)

    # local = mseed2avail('.')
    # pprint(local.json())

    # print((remote - local).json())
    # remote - local


if __name__ == '__main__':
    main()
