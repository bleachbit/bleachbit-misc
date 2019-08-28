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



def list_to_file(l, fn):
    """Write the list to a file"""
    with open(fn, 'w') as f:
        for item in sorted(l):
            f.write('%s\n' % item)

def clean_filename(fn, base_path):
    """Standardize the filename"""
    ret = fn
    if '/' == fn[0]:
        # running on Unix-like system
        ret = ret.replace('/', '\\')

    ret = ret.lower() # make lowercase
    ret = ret.replace(base_path.lower(), '') # strip off the base path
    ret = ret.replace(base_path.replace('/', '\\').lower(), '') # Unix variation
    if ret.endswith(r'\*'):
        # remove wildcard seen with QueryDirectory
        ret = ret[:-1]

    return ret

def is_filtered(path):
    if path.lower().startswith('hk'):
        # registry keys: HKCU, HKLM
        return True
    if path.lower().startswith('c:\\windows\\'):
        return True
    return False

def get_whitelist(csv_path, base_path):
    whitelist = set()

    import csv
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if not 'SUCCESS' == row[5]:
                continue
            fn_raw = row[4]
            if is_filtered(fn_raw):
                continue
            fn_clean = clean_filename(fn_raw, base_path)
            whitelist.add(fn_clean)
    return whitelist



def walk_compare_path(compare_path, whitelist):
    keep = set()
    remove = set()

    import os
    for root, dirs, files in os.walk(compare_path, topdown=False):
        for name in files:
            full_path = os.path.join(root, name)
            cleaned_path = clean_filename(full_path, compare_path)
            if cleaned_path in whitelist:
                keep.add(cleaned_path)
            else:
                remove.add(cleaned_path)
    return (keep, remove)

def go():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_path')
    parser.add_argument('base_path')
    parser.add_argument('compare_path')
    args = parser.parse_args()

    whitelist = get_whitelist(args.csv_path, args.base_path)
    list_to_file(whitelist, 'whitelist.txt')

    (keep, remove) = walk_compare_path(args.compare_path, whitelist)
    list_to_file(keep, 'keep.txt')
    list_to_file(remove, 'remove.txt')


go()
