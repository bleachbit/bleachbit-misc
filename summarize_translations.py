#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab

# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#


import gettext
import os
import os.path
import re
import subprocess
import sys

dir_bb_root = os.path.abspath('../trunk')
dir_bb_locale = os.path.abspath('../trunk/locale')
dir_bb_po = os.path.abspath('../trunk/po')

os.chdir(dir_bb_root)
sys.path.append(dir_bb_root)

import setup
import bleachbit.Unix

gettext.bindtextdomain('bleachbit', dir_bb_locale)
gettext.textdomain('bleachbit')
gettext.install('bleachbit', dir_bb_locale, unicode=1)

strs = [
    'Delete',
    'Unnecessary file cleaner',
    'Free space and maintain privacy',
    'Program to clean unnecessary files',
    'translator-credits']

summary_str = 'Free space and maintain privacy'


def get_translation_progress(lang):
    """Get the progress for a translation"""
    assert (type(lang) is str)
    oldcwd = os.getcwd()
    os.chdir(dir_bb_po)
    args = ['msgfmt', '--statistics', '-o', lang + '.mo', lang + '.po']
    outputs = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    output = outputs[1]
    os.chdir(oldcwd)
    # 53 translated messages, 82 untranslated messages.
    match = re.search(
        '([0-9]+) translated messages.* ([0-9]+) untranslated message', output)
    if match:
        # you should run 'make refresh-po' to update untranslated
        translated = int(match.group(1))
        untranslated = int(match.group(2))
        return "%.2f%%" % (100. * translated / (untranslated + translated))
    match = re.search('([0-9]+) translated messages', output)
    if match:
        return "100%"
    sys.stderr.write("Unknown output for language '%s': '%s'" % (lang, output))
    return "?"


def main():
    print """
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head>
<body>
"""
    print '<table>\n'
    print '<tr><td>Code</td><td>Name</td><td>Percentage translated</td><td>"%s"</td></tr>\n' % summary_str
    for langid in sorted(setup.supported_languages()):
        assert (type(langid) is str)
        print '<tr lang="%s">' % (langid)
        native_name = bleachbit.Unix.locales.native_name(langid)
        print '<td>%s</td>' % langid
        print '<td>%s</td>' % (native_name)
        lang = gettext.translation(
            'bleachbit', localedir=dir_bb_locale, languages=[langid])
        lang.install()
        stats = get_translation_progress(langid)
        print '<td>%s</td>' % (stats)
        free_space = lang.gettext(summary_str)
        # print 'free_space =', free_space
        if free_space == summary_str:
            free_space = '&nbsp;'
        print '<td>%s</td>' % free_space
        print '</tr>'
    print '</table>'

main()
