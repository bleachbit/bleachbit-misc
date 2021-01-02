#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2014-2021 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

"""
Verify the online update notification system returns the right version numbers
"""

from __future__ import absolute_import

import os
import sys
dir_bb_root = os.path.abspath('../bleachbit')
os.chdir(dir_bb_root)
sys.path.append(dir_bb_root)
import bleachbit
import bleachbit.Update

latest_stable = '4.2.0'
latest_beta = None

# tuple in the format
# (current version sent, version returned 1, version returned 2)
tests = \
    (('3.0', latest_stable, None),
     ('3.0.1', latest_stable, None),
     ('3.1.0', latest_stable, None),
     ('3.2.0', latest_stable, None),
     ('3.9.0',latest_stable, None),
     ('3.9.1',latest_stable,None),
     ('3.9.2', latest_stable, None),
     ('4.0.0', latest_stable, None),
     ('4.1.0', latest_stable, None),
     ('4.1.1', latest_stable, None),
     ('4.2.0', None, None))

for test in tests:
    print ('\n', '*' * 10, test[0])
    bleachbit.APP_VERSION = test[0]
    bleachbit.update_check_url = "%s/update/%s" % (
        bleachbit.base_url, bleachbit.APP_VERSION)
    v1e = test[1]  # e=expected
    v2e = test[2]
    cu = bleachbit.Update.check_updates(True, False, None, None)
    print ('returned=', cu)
    match = False
    if cu == ():
        v1r = None  # r=returned
        v2r = None
    else:
        if cu[0]:
            v1r = cu[0][0]
        else:
            v1r = None
        if len(cu) > 1:
            v2r = cu[1][0]
        else:
            v2r = None
    if not v1e == v1r:
        print ('ERROR: sent version %s, expected v1=%s, returned v1=%s' % \
            (test[0], v1e, v1r))
    if not v2e == v2r:
        print ('ERROR: sent version %s, expected v1=%s, returned v2=%s' % \
            (test[0], v2e, v2r))
