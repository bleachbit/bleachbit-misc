#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2019 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

"""
Transform Git log into translation credits
"""

import os
import subprocess
import sys


def process_line(line):
    """Process a single entry of the Git log"""
    import re
    groups = re.split(r'^\w{8} Update (.*) translation thanks to (\.*)', line)
    if len(groups) > 2:
        lang = groups[1]
        authors = groups[3].split(',')  # turn string into list
        authors = [a.strip(' ') for a in authors]  # clean up whitespace
        return (lang, authors)
    else:
        return None


def make_html_snippet(credit):
    """Make an HTML snippet to show credit

    Language list is sorted.

    Authors list is unique and sorted.
    """
    for lang in sorted(credit.keys()):
        authors = credit[lang]
        authors = sorted(set(authors))
        print('<li>Update %s translation thanks to %s</li>' %
              (lang, ', '.join(authors)))


def usage():
    print('usage:')
    print('argument 1: path to BleachBit repository')
    print('argument 2: Git revision range such as v2.2...v2.3')
    sys.exit(1)


def go():
    """Main"""
    if not len(sys.argv) == 3:
        usage()
    root_dir = sys.argv[1]
    revision_range = sys.argv[2]
    os.chdir(root_dir)
    cmd = ['git', 'log', '--oneline', revision_range, './po']
    cp = subprocess.run(cmd, capture_output=True, encoding='utf8')
    lines = cp.stdout.split('\n')
    credit = {}
    unrecognized_lines = []
    for line in lines:
        ret = process_line(line)
        if ret:
            # Found a translation update
            lang = ret[0]
            authors = ret[1]
            if lang in credit:
                credit[lang] = credit[lang] + authors
            else:
                credit[lang] = authors
        else:
            unrecognized_lines.append(line)
    make_html_snippet(credit)
    for line in sorted(unrecognized_lines):
        print('<li>%s</li>' % line)


go()
