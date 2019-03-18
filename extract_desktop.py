#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2014 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#


"""
List entries for bleachbit.desktop
"""


import gettext
import os
import sys
import subprocess
import re

bleachbit_repo_dir = '../bleachbit'
if not os.path.exists(bleachbit_repo_dir):
    print('The bleachbit repository does not exist in ', bleachbit_repo_dir)
    sys.exit(1)
os.chdir(bleachbit_repo_dir)
sys.path.append(".")

import setup
import bleachbit.Unix


locale_dir = 'locale'

gettext.bindtextdomain('bleachbit', locale_dir)
gettext.textdomain('bleachbit')
gettext.install('bleachbit', locale_dir, unicode=1)


def get_lang_str(langid, str):
    lang = gettext.translation(
        'bleachbit', localedir=locale_dir, languages=[langid])
    lang.install()
    return lang.gettext(str)


def print_desktop_keys(key, value):
    print '%s=%s' % (key, value)
    for langid in sorted(setup.supported_languages()):
        translated = get_lang_str(langid, value)
        if translated != value:
            print '%s[%s]=%s' % (key, langid, translated)


def main():
    if not os.path.exists('po/es.po'):
        print('ERROR: po/es.po does not exist. It should always be in the bleachbit repo.')
        sys.exit(1)
    if not os.path.exists('po/es.mo'):
        print('ERROR: po/es.mo does not exist, so it seems translations are not compiled.')
        print('Tip: try running "make -c po local" from the bleachbit repo.')
        sys.exit(1)
    print_desktop_keys('Comment', 'Free space and maintain privacy')
    print_desktop_keys('GenericName', 'Unnecessary file cleaner')


main()
