#!/usr/bin/env python
# -*- coding: utf-8 -*-

###########################################################################
# (C) 2017 Helmholtz-Zentrum Potsdam - Deutsches GeoForschungsZentrum GFZ #
#                                                                         #
# License: LGPLv3 (https://www.gnu.org/copyleft/lesser.html)              #
###########################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
import os
import optparse
import subprocess
import dateutil.parser
from seiscomp import fdsnxml, mseedlite, fseed, logs
from xml.etree import cElementTree as ET

VERSION = "2017.217"
ORGANIZATION = "EIDA"


def exec_fetch(param, data, verbose):
    cmd = [sys.path[0] + "/fdsnws_fetch"]

    if verbose:
        cmd += ["-v"]

    if data is not None:
        cmd += ["-p", "/dev/stdin"]

    cmd += ["-o", "/dev/stdout"]
    cmd += param

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    if data is not None:
        proc.stdin.write(data)

    proc.stdin.close()
    return proc


def get_citation(nets, param, verbose):
    postdata = ""
    for (net, year) in nets:
        postdata += "%s * * * %d-01-01T00:00:00Z %d-12-31T23:59:59Z\n" \
                    % (net, year, year)

    if not isinstance(postdata, bytes):
        postdata = postdata.encode('utf-8')

    try:
        proc = exec_fetch(param, postdata, verbose)

    except OSError as e:
        logs.error(str(e))
        logs.error("error running fdsnws_fetch")
        return 1

    net_desc = {}

    for line in proc.stdout:
        try:
            if isinstance(line, bytes):
                line = line.decode('utf-8')

            if not line or line.startswith('#'):
                continue

            (code, desc, start) = line.split('|')[:3]

            year = dateutil.parser.parse(start).year

        except (ValueError, UnicodeDecodeError) as e:
            logs.error("error parsing text format: %s" % str(e))
            continue

        if code[0] in '0123456789XYZ':
            net_desc['%s_%d' % (code, year)] = desc

        else:
            net_desc[code] = desc

    logs.notice("You received seismic waveform data from the following "
                "network(s):")

    for code in sorted(net_desc):
        logs.notice("%s %s" % (code, net_desc[code]))

    logs.notice("\nAcknowledgment is extremely important for network operators\n"
                "providing open data. When preparing publications, please\n"
                "cite the data appropriately. The FDSN service at\n\n"
                "    http://www.fdsn.org/networks/citation/?networks=%s\n\n"
                "provides a helpful guide based on available network\n"
                "Digital Object Identifiers.\n"
                % "+".join(sorted(net_desc)))


def main():
    param0 = ['-y', 'station', '-q', 'format=text', '-q', 'level=network']
    param1 = ['-y', 'station', '-q', 'format=xml', '-q', 'level=response']
    param2 = ['-y', 'dataselect', '-z']
    nets = set()

    def add_param0(option, opt_str, value, parser):
        param0.append(opt_str)
        param0.append(value)

    def add_param1(option, opt_str, value, parser):
        param1.append(opt_str)
        param1.append(value)

    def add_param2(option, opt_str, value, parser):
        param2.append(opt_str)
        param2.append(value)

    def add_param(option, opt_str, value, parser):
        add_param0(option, opt_str, value, parser)
        add_param1(option, opt_str, value, parser)
        add_param2(option, opt_str, value, parser)

    parser = optparse.OptionParser(
            usage="Usage: %prog [-h|--help] [OPTIONS] -o file",
            version="%prog " + VERSION)

    parser.set_defaults(
            url="http://geofon.gfz-potsdam.de/eidaws/routing/1/",
            timeout=600,
            retries=10,
            retry_wait=60,
            threads=5)

    parser.add_option("-v", "--verbose", action="store_true", default=False,
                      help="verbose mode")

    parser.add_option("-u", "--url", type="string", action="callback",
                      callback=add_param,
                      help="URL of routing service (default %default)")

    parser.add_option("-N", "--network", type="string", action="callback",
                      callback=add_param,
                      help="network code or pattern")

    parser.add_option("-S", "--station", type="string", action="callback",
                      callback=add_param,
                      help="station code or pattern")

    parser.add_option("-L", "--location", type="string", action="callback",
                      callback=add_param,
                      help="location code or pattern")

    parser.add_option("-C", "--channel", type="string", action="callback",
                      callback=add_param,
                      help="channel code or pattern")

    parser.add_option("-s", "--starttime", type="string", action="callback",
                      callback=add_param,
                      help="start time")

    parser.add_option("-e", "--endtime", type="string", action="callback",
                      callback=add_param,
                      help="end time")

    parser.add_option("-t", "--timeout", type="int", action="callback",
                      callback=add_param,
                      help="request timeout in seconds (default %default)")

    parser.add_option("-r", "--retries", type="int", action="callback",
                      callback=add_param,
                      help="number of retries (default %default)")

    parser.add_option("-w", "--retry-wait", type="int", action="callback",
                      callback=add_param,
                      help="seconds to wait before each retry (default %default)")

    parser.add_option("-n", "--threads", type="int", action="callback",
                      callback=add_param,
                      help="maximum number of download threads (default %default)")

    parser.add_option("-c", "--credentials-file", type="string", action="callback",
                      callback=add_param2,
                      help="URL,user,password file (CSV format) for queryauth")

    parser.add_option("-a", "--auth-file", type="string", action="callback",
                      callback=add_param2,
                      help="file that contains the auth token")

    parser.add_option("-p", "--post-file", type="string", action="callback",
                      callback=add_param,
                      help="request file in FDSNWS POST format")

    parser.add_option("-f", "--arclink-file", type="string", action="callback",
                      callback=add_param,
                      help="request file in ArcLink format")

    parser.add_option("-b", "--breqfast-file", type="string", action="callback",
                      callback=add_param,
                      help="request file in breq_fast format")

    parser.add_option("-d", "--dataless", action="store_true", default=False,
                      help="create dataless SEED volume")

    parser.add_option("-l", "--label", type="string",
                      help="label of SEED volume")

    parser.add_option("-o", "--output-file", type="string",
                      help="file where SEED data is written")

    parser.add_option("-z", "--no-citation", action="store_true", default=False,
                      help="suppress network citation info")

    (options, args) = parser.parse_args()

    if args or not options.output_file:
        parser.print_usage()
        return 1

    def log_verbose(s):
        sys.stderr.write(s + '\n')
        sys.stderr.flush()

    def log_silent(s):
        pass

    logs.error = log_verbose
    logs.warning = log_verbose
    logs.notice = log_verbose
    logs.info = (log_silent, log_verbose)[options.verbose]
    logs.debug = log_silent

    try:
        proc = exec_fetch(param1, None, options.verbose)

    except OSError as e:
        logs.error(str(e))
        logs.error("error running fdsnws_fetch")
        return 1

    inv = fdsnxml.Inventory()

    try:
        inv.load_fdsnxml(proc.stdout)

    except ET.ParseError as e:
        if str(e) != "no element found: line 1, column 0":
            raise

    proc.stdout.close()
    proc.wait()

    if proc.returncode != 0:
        logs.error("error running fdsnws_fetch")
        return 1

    seed_volume = fseed.SEEDVolume(inv, ORGANIZATION, options.label, False)

    if options.dataless:
        for net in sum([i.values() for i in inv.network.itervalues()], []):
            for sta in sum([i.values() for i in net.station.itervalues()], []):
                for loc in sum([i.values() for i in sta.sensorLocation.itervalues()], []):
                    for cha in sum([i.values() for i in loc.stream.itervalues()], []):
                        seed_volume.add_chan(net.code, sta.code, loc.code, cha.code, cha.start, cha.end)

    else:
        try:
            proc = exec_fetch(param2, None, options.verbose)

        except OSError as e:
            logs.error(str(e))
            logs.error("error running fdsnws_fetch")
            return 1

        for rec in mseedlite.Input(proc.stdout):
            seed_volume.add_data(rec)
            nets.add((rec.net, rec.begin_time.year))

        proc.stdout.close()
        proc.wait()

        if proc.returncode != 0:
            logs.error("error running fdsnws_fetch")
            return 1

    with open(options.output_file, "wb") as fd:
        seed_volume.output(fd)

    if nets and not options.no_citation:
        logs.info("retrieving network citation info")
        get_citation(nets, param0, options.verbose)

    return 0


if __name__ == "__main__":
    sys.exit(main())

