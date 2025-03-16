#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

"""
Copyright (C) 2016-2025 by Andrew Ziem.  All rights reserved.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Windows builds are frequently and automatically published to
ci.bleachbit.org. This script helps purge the older builds.
"""

import subprocess
import unittest
from packaging.version import parse as parse_version


def key_ver(path):
    """Convert an S3 path into a StrictVersion for sorting"""
    ver_str = path.split('/')[4]
    try:
        # Extract version number before the hyphen
        ver_str = ver_str.split('-')[0]
        ret = parse_version(ver_str)
    except ValueError:
        print('Not a recognizable version:', ver_str, path)
        ret = ver_str
    return ret

def get_dirs():
    """Get the list of directories from S3."""
    args = ['s3cmd', 'ls', 's3://bleachbitci/dl/']
    ls_raw = subprocess.check_output(args)
    ls_lines = ls_raw.decode().split('\n')

    # get relevant directories
    dirs = []
    for line in ls_lines:
        if not line:
            break
        line_s = line.split()
        if not len(line_s) == 2:
            break
        if line_s[0] != 'DIR':
            break
        dirs.append(line_s[1])

    # Sort by version number, keeping the newest first.
    dirs.sort(key=key_ver, reverse=True)
    return dirs


class TestKeyVer(unittest.TestCase):
    def test_key_ver(self):
        # Test cases
        test_cases = [
            ("s3://bleachbitci/dl/4.6.2.2665-v4.6.2/", "4.6.2.2665"),
            ("s3://bleachbitci/dl/4.9.0.2773-certificate_verify/", "4.9.0.2773"),
        ]
        for path, expected in test_cases:
            with self.subTest(path=path):
                # Use parse_version for both actual and expected values
                self.assertEqual(key_ver(path), parse_version(expected))

def main():
    """Main function."""
    dirs = get_dirs()
    assert dirs is not None
    assert len(dirs) > 3
    # Keep the newest builds.
    keep_newest_n = 5
    print(f'Keeping the following {keep_newest_n} newest directories:')
    for d in dirs[:keep_newest_n]:
        print(f'     {d}')
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
            print(f's3cmd del -r {delete_dir}')
    else:
        print('nothing to delete')


if __name__ == '__main__':
    main()
