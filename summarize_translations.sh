#!/bin/bash

# Copyright (C) 2010 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#

cd ../trunk/po
make clean
make refresh-po > /dev/null
make local > /dev/null
cd ../../misc
python summarize_translations.py > /tmp/summarized_translations.html
svn revert ../trunk/po/*po
links -dump /tmp/summarized_translations.html

