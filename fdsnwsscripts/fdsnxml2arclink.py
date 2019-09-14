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
from fdsnwsscripts.seiscomp import fdsnxml, logs

def log_alert(s):
    if sys.stderr.isatty():
        s = "\033[31m" + s + "\033[m"

    sys.stderr.write(s + '\n')
    sys.stderr.flush()

def log_notice(s):
    if sys.stderr.isatty():
        s = "\033[32m" + s + "\033[m"

    sys.stderr.write(s + '\n')
    sys.stderr.flush()

def log_verbose(s):
    sys.stderr.write(s + '\n')
    sys.stderr.flush()

def log_silent(s):
    pass

def main():
    logs.error = log_alert
    logs.warning = log_alert
    logs.notice = log_notice
    logs.info = log_verbose
    logs.debug = log_silent

    if len(sys.argv) not in (2, 3):
        logs.notice("Usage: %s input_file [output_file]" % sys.argv[0])
        return 1

    inv = fdsnxml.Inventory()

    try:
        inv.load_fdsnxml(sys.argv[1])

    except fdsnxml.Error as e:
        logs.error(str(e))
        return 1

    stdout = sys.stdout.buffer if hasattr(sys.stdout, "buffer") else sys.stdout
    inv.save_xml(sys.argv[2] if len(sys.argv) == 3 else stdout, instr=1)

    return 0

if __name__ == "__main__":
    sys.exit(main())
