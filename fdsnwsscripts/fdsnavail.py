#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


def str2date(dstr):
    """Transform a string to a datetime.

    :param dstr: A datetime in ISO format.
    :type dstr: string
    :return: A datetime represented the converted input.
    :rtype: datetime
    """
    # In case of empty string
    if not len(dstr):
        return None

    dateparts = dstr.replace('-', ' ').replace('T', ' ')
    dateparts = dateparts.replace(':', ' ').replace('.', ' ')
    dateparts = dateparts.replace('Z', '').split()
    return datetime(*map(int, dateparts))


class Stream(namedtuple('Stream', ['net', 'sta', 'loc', 'cha', 'qua', 'sr'])):
    __slots__ = ()


class Availability:
    pass


class Availability:
    def __init__(self, url: str = None):
        self.__url = url
        self.__dict: Dict[Stream, list] = dict()
        # If there is no URL we will use the addchunk method
        if url is None:
            return

        # If there is a URL load teh dict from the response
        resp = requests.get(url)
        for ds in resp.json()['datasources']:
            stream = Stream(ds['network'], ds['station'], ds['location'], ds['channel'], ds['quality'], ds['samplerate'])
            for ts in ds['timespans']:
                self.addchunk(stream, [str2date(ts[0]), str2date(ts[1])])

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", default="geofon.gfz-potsdam.de",
                        help="URL of availability web service. (default is EIDA).")
    parser.add_argument("-N", "--network", type=str, default=None, help="Network code")
    parser.add_argument("-S", "--station", type=str, default=None, help="Station code")
    parser.add_argument("-L", "--location", type=str, default=None, help="Location code")
    parser.add_argument("-C", "--channel", type=str, default=None, help="Channel code")
    parser.add_argument("-s", "--starttime", type=str, default=None, help="start time")
    parser.add_argument("-e", "--endtime", type=str, default=None, help="end time")
    # parser.add_argument("-p", "--post-file", type=str, default=None, help="request file in FDSNWS POST format")
    parser.add_argument("-o", "--output-file", type=str, default=None, help="file where downloaded data is written")
    args = parser.parse_args()

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
    # params = "net=GE&sta=APE&cha=BH?&start=2001-01-01&end=2001-04-01"
    urlavail = "https://%s/fdsnws/availability/1/query?%s&mergegaps=0&format=json" % (args.url,
                                                                                      str.join('&', params))
    # Retrieve the availability for the selected streams/time windows
    remote = Availability(urlavail)
    print(remote.post())
    # local = mseed2avail('.')
    # pprint(local.json())

    # print((remote - local).json())
    # remote - local


if __name__ == '__main__':
    main()
