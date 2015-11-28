#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2014 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

"""
Verify the online update notification system returns the right version numbers
"""

import os
import sys
dir_bb_root = os.path.abspath('../bleachbit')
os.chdir(dir_bb_root)
sys.path.append(dir_bb_root)
import bleachbit.Update
import bleachbit.Common

latest_stable = '1.6'
latest_beta = '1.7.7 (beta)'

# tuple in the format
# (current version sent, version returned 1, version returned 2)
tests = \
    (('1.2', latest_stable, None),
     ('1.4', latest_stable, None),
     ('1.5.1', latest_stable, None),
     ('1.5.2', latest_stable, None),
     ('1.6', latest_beta, None),
     ('1.7.5', latest_stable, latest_beta),
     ('1.7.6', latest_stable, latest_beta),
     ('1.7.7', None, None))

for test in tests:
    print '\n', '*' * 10, test[0]
    bleachbit.Common.APP_VERSION = test[0]
    v1e = test[1]  # e=expected
    v2e = test[2]
    cu = bleachbit.Update.check_updates(True, False, None, None)
    print 'returned=', cu
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
        print 'ERROR: sent version %s, expected v1=%s, returned v1=%s' % \
            (test[0], v1e, v1r)
    if not v2e == v2r:
        print 'ERROR: sent version %s, expected v1=%s, returned v2=%s' % \
            (test[0], v2e, v2r)
