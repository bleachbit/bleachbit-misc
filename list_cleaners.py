#!/usr/bin/env python
# vim: ts=4:sw=4:expandtab


# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.



"""
List all cleaners in HTML format
"""



import gettext
import os
import sys

os.chdir('../trunk')
sys.path.append(".")

import bleachbit.Common
from bleachbit.Cleaner import backends
from bleachbit.CleanerML import load_cleaners



def main():
    bleachbit.Common.personal_cleaners_dir = '../bonus/cleaners'
    load_cleaners()
    for key in sorted(backends):

        options = []
        for (option_id, name) in backends[key].get_options():
            options.append(name)

        print '<li title="%s">%s</li>' % (", ".join(options), backends[key].get_name())



main()
