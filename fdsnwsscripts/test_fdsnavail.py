#!/usr/bin/env python3

"""Tests to check that fdsnavail.py is working

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
import os
import pytest
from fdsnwsscripts.fdsnavail import __query__
from fdsnwsscripts.fdsnavail import __scan__
from fdsnwsscripts.fdsnavail import __compare__
from fdsnwsscripts.fdsnavail import query
from fdsnwsscripts.fdsnavail import Stream
from collections import namedtuple
from json import dumps
from json import loads
from typing import Union
from typing import Dict
from typing import List
from datetime import datetime

"""Test the functionality of fdsnavail.py"""


class Parameters(namedtuple('Parameters', ['network', 'station', 'location', 'channel', 'starttime', 'endtime',
                                           'output_format', 'output_file', 'post_file', 'directory', 'structure'],
                            defaults=[None, None, None, None, None, None, None, None, None, None, None])):
    __slots__ = ()


def ordered(jsonobj: Union[Dict, List]) -> Union[Dict, List]:
    if isinstance(jsonobj, dict):
        return sorted((k, ordered(v)) for k, v in jsonobj.items())
    if isinstance(jsonobj, list):
        return sorted(ordered(x) for x in jsonobj)
    else:
        return jsonobj


def test_query_get():
    # Check that the Availability created is OK
    args2 = {'network': 'GE', 'station': 'APE', 'channel': 'BH?', 'starttime': '2001-01-01', 'endtime': '2001-01-03'}
    remote = __query__(Parameters(**args2))
    streams = dict()
    streams[Stream('GE', 'APE', '', 'BHE', 'D', 20.0)] = '[["2001-01-01T08:04:31.215000", "2001-01-01T08:07:19.615000"], ["2001-01-01T09:12:28.215000", "2001-01-01T09:21:35.115000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:48:27.449000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:22.656000"]]'
    streams[Stream('GE', 'APE', '', 'BHN', 'D', 20.0)] = '[["2001-01-01T09:12:28.215000", "2001-01-01T09:18:33.815000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:49:08.049000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:15.956000"]]'
    streams[Stream('GE', 'APE', '', 'BHZ', 'D', 20.0)] = '[["2001-01-01T08:04:31.215000", "2001-01-01T08:07:21.115000"], ["2001-01-01T09:12:28.215000", "2001-01-01T09:21:30.115000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:51:29.349000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:52.956000"]]'
    for stream in streams:
        assert dumps(remote[stream], default=datetime.isoformat) == streams[stream]


def test_query_wrong():
    # Check a wrong output format
    args2 = {'network': 'GE', 'station': 'APE', 'channel': 'BH?', 'starttime': '2001-01-01', 'endtime': '2001-01-03',
             'output_format': 'wrong'}
    with pytest.raises(Exception):
        query(Parameters(**args2))


def test_query_get_json():
    args2 = {'network': 'GE', 'station': 'APE', 'channel': 'BH?', 'starttime': '2001-01-01', 'endtime': '2001-01-03',
             'output_format': 'json', 'output_file': 'deleteme.json'}
    query(Parameters(**args2))
    with open('deleteme.json') as fin:
        remote = loads(fin.read())
    # Expected values
    streams = [{"network": "GE", "station": "APE", "location": "", "channel": "BHE", "quality": "D", "samplerate": 20.0, "timespans": [["2001-01-01T08:04:31.215000", "2001-01-01T08:07:19.615000"], ["2001-01-01T09:12:28.215000", "2001-01-01T09:21:35.115000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:48:27.449000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:22.656000"]]}, {"network": "GE", "station": "APE", "location": "", "channel": "BHN", "quality": "D", "samplerate": 20.0, "timespans": [["2001-01-01T09:12:28.215000", "2001-01-01T09:18:33.815000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:49:08.049000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:15.956000"]]}, {"network": "GE", "station": "APE", "location": "", "channel": "BHZ", "quality": "D", "samplerate": 20.0, "timespans": [["2001-01-01T08:04:31.215000", "2001-01-01T08:07:21.115000"], ["2001-01-01T09:12:28.215000", "2001-01-01T09:21:30.115000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:51:29.349000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:52.956000"]]}]
    assert ordered(remote['datasources']) == ordered(streams)
    os.remove('deleteme.json')


def test_query_get_post():
    args2 = {'network': 'GE', 'station': 'APE', 'channel': 'BH?', 'starttime': '2001-01-01', 'endtime': '2001-01-03',
             'output_format': 'post', 'output_file': 'deleteme.txt'}
    query(Parameters(**args2))
    with open('deleteme.txt') as fin:
        lines = fin.readlines()
    streams = list()
    streams.append('GE APE -- BHE 2001-01-01T08:04:31.215000 2001-01-01T08:07:19.615000')
    streams.append('GE APE -- BHE 2001-01-01T09:12:28.215000 2001-01-01T09:21:35.115000')
    streams.append('GE APE -- BHE 2001-01-01T10:22:09.215000 2001-01-01T18:48:27.449000')
    streams.append('GE APE -- BHE 2001-01-02T06:59:22.215000 2001-01-02T16:45:22.656000')
    streams.append('GE APE -- BHN 2001-01-01T09:12:28.215000 2001-01-01T09:18:33.815000')
    streams.append('GE APE -- BHN 2001-01-01T10:22:09.215000 2001-01-01T18:49:08.049000')
    streams.append('GE APE -- BHN 2001-01-02T06:59:22.215000 2001-01-02T16:45:15.956000')
    streams.append('GE APE -- BHZ 2001-01-01T08:04:31.215000 2001-01-01T08:07:21.115000')
    streams.append('GE APE -- BHZ 2001-01-01T09:12:28.215000 2001-01-01T09:21:30.115000')
    streams.append('GE APE -- BHZ 2001-01-01T10:22:09.215000 2001-01-01T18:51:29.349000')
    streams.append('GE APE -- BHZ 2001-01-02T06:59:22.215000 2001-01-02T16:45:52.956000')
    for line in lines:
        assert line.strip() in streams
    os.remove('deleteme.txt')


def test_query_post():
    # Check that the Availability created is OK
    # args = Parameters(None, None, None, None, None, None, None, None, 'tests/request.post')
    args2 = {'post_file': 'tests/request.post'}
    remote = __query__(Parameters(**args2))
    streams = dict()
    streams[Stream('GE', 'APE', '', 'BHE', 'D', 20.0)] = '[["2001-01-01T08:04:31.215000", "2001-01-01T08:07:19.615000"], ["2001-01-01T09:12:28.215000", "2001-01-01T09:21:35.115000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:48:27.449000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:22.656000"]]'
    streams[Stream('GE', 'APE', '', 'BHN', 'D', 20.0)] = '[["2001-01-01T09:12:28.215000", "2001-01-01T09:18:33.815000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:49:08.049000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:15.956000"]]'
    streams[Stream('GE', 'APE', '', 'BHZ', 'D', 20.0)] = '[["2001-01-01T08:04:31.215000", "2001-01-01T08:07:21.115000"], ["2001-01-01T09:12:28.215000", "2001-01-01T09:21:30.115000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:51:29.349000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:52.956000"]]'
    for stream in streams:
        assert dumps(remote[stream], default=datetime.isoformat) == streams[stream]


def test_query_post_json():
    # args = Parameters(None, None, None, None, None, None, 'json', 'deleteme.json', 'tests/request.post')
    args2 = {'output_format': 'json', 'output_file': 'deleteme.json', 'post_file': 'tests/request.post'}
    query(Parameters(**args2))
    with open('deleteme.json') as fin:
        remote = loads(fin.read())
    # Expected values
    streams = [{"network": "GE", "station": "APE", "location": "", "channel": "BHE", "quality": "D", "samplerate": 20.0, "timespans": [["2001-01-01T08:04:31.215000", "2001-01-01T08:07:19.615000"], ["2001-01-01T09:12:28.215000", "2001-01-01T09:21:35.115000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:48:27.449000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:22.656000"]]}, {"network": "GE", "station": "APE", "location": "", "channel": "BHN", "quality": "D", "samplerate": 20.0, "timespans": [["2001-01-01T09:12:28.215000", "2001-01-01T09:18:33.815000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:49:08.049000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:15.956000"]]}, {"network": "GE", "station": "APE", "location": "", "channel": "BHZ", "quality": "D", "samplerate": 20.0, "timespans": [["2001-01-01T08:04:31.215000", "2001-01-01T08:07:21.115000"], ["2001-01-01T09:12:28.215000", "2001-01-01T09:21:30.115000"], ["2001-01-01T10:22:09.215000", "2001-01-01T18:51:29.349000"], ["2001-01-02T06:59:22.215000", "2001-01-02T16:45:52.956000"]]}]
    assert ordered(remote['datasources']) == ordered(streams)
    os.remove('deleteme.json')


def test_query_post_post():
    # args = Parameters(None, None, None, None, None, None, 'post', 'deleteme.txt', 'tests/request.post')
    args2 = {'output_format': 'post', 'output_file': 'deleteme.txt', 'post_file': 'tests/request.post'}
    query(Parameters(**args2))
    with open('deleteme.txt') as fin:
        lines = fin.readlines()
    streams = list()
    streams.append('GE APE -- BHE 2001-01-01T08:04:31.215000 2001-01-01T08:07:19.615000')
    streams.append('GE APE -- BHE 2001-01-01T09:12:28.215000 2001-01-01T09:21:35.115000')
    streams.append('GE APE -- BHE 2001-01-01T10:22:09.215000 2001-01-01T18:48:27.449000')
    streams.append('GE APE -- BHE 2001-01-02T06:59:22.215000 2001-01-02T16:45:22.656000')
    streams.append('GE APE -- BHN 2001-01-01T09:12:28.215000 2001-01-01T09:18:33.815000')
    streams.append('GE APE -- BHN 2001-01-01T10:22:09.215000 2001-01-01T18:49:08.049000')
    streams.append('GE APE -- BHN 2001-01-02T06:59:22.215000 2001-01-02T16:45:15.956000')
    streams.append('GE APE -- BHZ 2001-01-01T08:04:31.215000 2001-01-01T08:07:21.115000')
    streams.append('GE APE -- BHZ 2001-01-01T09:12:28.215000 2001-01-01T09:21:30.115000')
    streams.append('GE APE -- BHZ 2001-01-01T10:22:09.215000 2001-01-01T18:51:29.349000')
    streams.append('GE APE -- BHZ 2001-01-02T06:59:22.215000 2001-01-02T16:45:52.956000')
    for line in lines:
        assert line.strip() in streams
    os.remove('deleteme.txt')


def test_scan_sds():
    args2 = {'directory': 'tests/sds', 'structure': 'sds'}
    local = __scan__(Parameters(**args2))
    for stream, ts in local:
        print(stream, ts)
    streams = dict()
    streams[Stream('GE', 'APE', '', 'BHE', 'D', 20.0)] = '[["2001-01-01T08:04:31.215867", "2001-01-01T08:07:19.615867"], ["2001-01-01T09:12:28.215867", "2001-01-01T09:21:35.115867"], ["2001-01-01T10:22:09.215867", "2001-01-01T18:48:27.455540"]]'
    streams[Stream('GE', 'APE', '', 'BHN', 'D', 20.0)] = '[["2001-01-01T09:12:28.215867", "2001-01-01T09:18:33.815866"], ["2001-01-01T10:22:09.215867", "2001-01-01T18:49:08.055540"]]'
    streams[Stream('GE', 'APE', '', 'BHZ', 'D', 20.0)] = '[["2001-01-01T08:04:31.215867", "2001-01-01T08:07:21.115867"], ["2001-01-01T09:12:28.215867", "2001-01-01T09:21:30.115867"], ["2001-01-01T10:22:09.215867", "2001-01-01T18:51:29.355580"]]'
    for stream in streams:
        assert dumps(local[stream], default=datetime.isoformat) == streams[stream]


def test_scan_mseedfiles():
    args2 = {'directory': 'tests', 'structure': 'files'}
    local = __scan__(Parameters(**args2))
    streams = dict()
    streams[Stream('GE', 'APE', '', 'BHE', 'D', 20.0)] = '[["2001-01-01T08:04:31.215867", "2001-01-01T08:07:19.615867"], ["2001-01-01T09:12:28.215867", "2001-01-01T09:21:35.115867"], ["2001-01-01T10:22:09.215867", "2001-01-01T18:48:27.455540"]]'
    streams[Stream('GE', 'APE', '', 'BHN', 'D', 20.0)] = '[["2001-01-01T09:12:28.215867", "2001-01-01T09:18:33.815866"], ["2001-01-01T10:22:09.215867", "2001-01-01T18:49:08.055540"]]'
    streams[Stream('GE', 'APE', '', 'BHZ', 'D', 20.0)] = '[["2001-01-01T08:04:31.215867", "2001-01-01T08:07:21.115867"], ["2001-01-01T09:12:28.215867", "2001-01-01T09:21:30.115867"], ["2001-01-01T10:22:09.215867", "2001-01-01T18:51:29.355580"]]'
    for stream in streams:
        assert dumps(local[stream], default=datetime.isoformat) == streams[stream]


def test_compare_mseedfiles():
    args2 = {'directory': 'tests', 'structure': 'files', 'post_file': 'tests/request.post'}
    local = __compare__(Parameters(**args2))
    streams = dict()
    streams[Stream('GE', 'APE', '', 'BHE', 'D', 20.0)] = '[["2001-01-02T06:59:22.215000", "2001-01-02T16:45:22.656000"]]'
    streams[Stream('GE', 'APE', '', 'BHN', 'D', 20.0)] = '[["2001-01-02T06:59:22.215000", "2001-01-02T16:45:15.956000"]]'
    streams[Stream('GE', 'APE', '', 'BHZ', 'D', 20.0)] = '[["2001-01-02T06:59:22.215000", "2001-01-02T16:45:52.956000"]]'
    for stream in streams:
        assert dumps(local[stream], default=datetime.isoformat) == streams[stream]
