#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2016 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

"""
Windows builds are frequently and automatically published to
ci.bleachbit.org. This script helps purge the older builds.
"""

import subprocess

args = ['s3cmd', 'ls', 's3://ci.bleachbit.org/']
ls_raw = subprocess.check_output(args)

ls_lines = ls_raw.decode().split('\n')

# get relevant directories
dirs = []
for line in ls_lines:
    if '' == ls_lines:
        break
    line_s = line.split()
    if not len(line_s) == 2:
        break
    if line_s[0] != 'DIR':
        break
    dirs.append(line_s[1])

# sort by version number,keep newest first
def key_ver(s):
    v = s.split('/')[3]
    from distutils.version import StrictVersion
    return StrictVersion(v)

dirs.sort(key=key_ver, reverse=True)

# Keep the newest builds.
keep_newest_n = 5
print('Keeping the following {} newest directories:'.format(keep_newest_n))
for d in dirs[:keep_newest_n]:
    print ('     ', d)
print()
# Delete the older builds.
if len(dirs) > keep_newest_n:
    print('Issue the following command to perform the delete')
    print()
    # s3cmd 1.6.1 does not support multiple paths to delete at once
    # Support was added in its Git repository November 2016.
    # For now, issue separate commands.
    #delete_dirs = ' '.join(dirs[keep_newest_n:])
    #delete_cmd = 's3cmd del -r {}'.format(delete_dirs)
    # print(delete_cmd)
    for delete_dir in dirs[keep_newest_n:]:
        print('s3cmd del -r {}'.format(delete_dir))
else:
    print('nothing to delete')
