#!/usr/bin/env python3
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2014-2024 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#


"""
This program helps manage the translations in the bleachbit.desktop file.

Here is how it works
1. The bleachbit/po/Makefile adds strings from bleachbit.desktop to bleachbit.pot
2. Weblate syncs translation strings from GitHub to hosted.weblate.org
3. Weblate asks users to translate the strings
4. Weblate pushes the .po files to the GitHub repository
5. This program extracts the two strings
6. I copy the output of this program and paste it into bleachbit.desktop
"""


import gettext
import os
import sys

bleachbit_repo_dir = '../bleachbit'
if not os.path.exists(bleachbit_repo_dir):
    print('The bleachbit repository does not exist in ', bleachbit_repo_dir)
    sys.exit(1)
os.chdir(bleachbit_repo_dir)
sys.path.append(".")

import setup


locale_dir = 'locale'

gettext.bindtextdomain('bleachbit', locale_dir)
gettext.textdomain('bleachbit')
gettext.install('bleachbit', locale_dir)


def get_lang_str(langid, str):
    lang = gettext.translation(
        'bleachbit', localedir=locale_dir, languages=[langid])
    lang.install()
    return lang.gettext(str)


def update_desktop(parser, key, value):
    changes = 0
    for langid in sorted(setup.supported_languages()):
        if '_new' in langid:
            raise ValueError('langid=_new')
        translated = get_lang_str(langid, value)
        if translated != value:
            key_lang = f"{key}[{langid}]"
            if key_lang in parser['Desktop Entry']:
                old_string = parser['Desktop Entry'][key_lang]
            else:
                old_string = ''
            if old_string != translated:
                changes += 1
            parser['Desktop Entry'][key_lang] = translated
    return changes

def process_desktop_file():
    from configparser import ConfigParser
    parser = ConfigParser()
    parser.optionxform = str # preserve case
    parser.read('org.bleachbit.BleachBit.desktop', encoding='utf-8')
    changes = update_desktop(
        parser, 'Comment', 'Free space and maintain privacy')
    changes += update_desktop(
        parser, 'GenericName', 'Unnecessary file cleaner')
    print(f"Made {changes} change(s) to org.bleachbit.BleachBit.desktop")
    with open('org.bleachbit.BleachBit.desktop', 'w', encoding='utf-8') as f:
        parser.write(f, space_around_delimiters=False)

def main():
    if not os.path.exists('po/es.po'):
        print('ERROR: po/es.po does not exist.')
        print('Tip: Verify you are in the root directory of the BleachBit repository.')
        sys.exit(1)
    if not os.path.exists('po/es.mo'):
        print('ERROR: po/es.mo does not exist, so it seems translations are not compiled.')
        print('Tip: try running "make -C po local" from the BleachBit repo.')
        print('Running the command for you.')
        ret = subprocess.run(['make', '-C', 'po', 'local'])
        if ret.returncode != 0:
            print('ERROR: running "make -C po local" failed')
            sys.exit(1)
        if not os.path.exists('po/es.mo'):
            print('ERROR: po/es.mo does not exist even after running "make -C po local"')
            sys.exit(1)
    process_desktop_file()



main()
