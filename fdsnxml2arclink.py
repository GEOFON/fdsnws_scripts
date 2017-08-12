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
from seiscomp import fdsnxml, logs

def log_print(s):
    print(s, file=sys.stderr)
    sys.stderr.flush()

logs.error = log_print
logs.warning = log_print
logs.notice = log_print
logs.info = log_print
logs.debug = lambda s: None

if len(sys.argv) not in (2, 3):
    logs.notice("Usage: %s input_file [output_file]" % sys.argv[0])
    sys.exit(1)

inv = fdsnxml.Inventory()

try:
    inv.load_fdsnxml(sys.argv[1])

except fdsnxml.Error as e:
    logs.error(e)
    sys.exit(1)

inv.save_xml(sys.argv[2] if len(sys.argv) == 3 else sys.stdout, instr=1)

