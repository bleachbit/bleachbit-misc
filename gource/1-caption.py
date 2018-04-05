#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2018 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

"""
Convert the caption CSV file into a PSV file

The CSV is comma delimited with date in YYYY-MM-DD format

The PSV is pipe delimited with date-time as Unix time
"""

import csv
import datetime

with open('caption-yymmdd.csv') as infile, open('caption.psv', 'w') as outfile:
    csvr = csv.reader(infile, delimiter=',')
    for row in csvr:
        ymd = row[0]
        y = int(ymd[0:4])
        m = int(ymd[5:7])
        d = int(ymd[8:10])
        dt = datetime.datetime(y, m, d)
        unixtime = dt.strftime('%s')
        caption = row[1]
        outfile.write('%s|%s\n' % (unixtime, caption))
