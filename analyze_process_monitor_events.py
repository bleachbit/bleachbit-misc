#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2016 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

"""

BleachBit's Windows build some files that are unnecessary to the application,
so this program helps analyze which files are actually needed to inform a
delete-list or whitelist.

Instructions:

1. Build BleachBit without deleting any of the files from the runtime,
or at least be sure not to delete any important files.

2. Run Microsoft Process Monitor and set up a filter.

3. Run BleachBit, and exercise all its functions.

4. From Process Monitor save the events to a CSV file.

5. Run this program like follows.

python3 analyze_process_monitor_events.py event_log.csv C:\\Users\\username\\Desktop\\BleachBit-portable\\ ~/bleachbit/dist

The arguments are
1. The trace file
2. The base directory of the BleachBit application when it was being traced
3. The directory containing the BleachBit files for comparison

Notice the Windows path has double slashes, and notice by the third argument
that this program can run on Unix-style systems.

"""

import csv
import os
import sys

if not len(sys.argv) == 4:
    print('Please read the instructions about this program in its source.')
    sys.exit(1)

csv_filename = sys.argv[1]
base_path = sys.argv[2]
compare_path = sys.argv[3]

whitelist = set()

with open(csv_filename, newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        if not 'SUCCESS' == row[5]:
            continue
        fn_raw = row[4]
        fn_clean = fn_raw.replace(base_path, '').lower()
        whitelist.add(fn_clean)

print('***********WHITELIST')
for fn in sorted(whitelist):
    print(fn)

keep = set()
remove = set()

for root, dirs, files in os.walk(compare_path, topdown=False):
    for name in files:
        full_path = os.path.join(root, name)
        clean_path = full_path.replace(compare_path, '')[1:].lower()
        if '/' == full_path[0]:
            # running on Unix-like system
            clean_path = clean_path.replace('/', '\\')
        if clean_path in whitelist:
            keep.add(clean_path)
        else:
            remove.add(clean_path)

print('')
print('**********KEEP')
for fn in sorted(keep):
    print(fn)

print('')
print('**********REMOVE')
for fn in sorted(remove):
    print(fn)
