#!/bin/bash

# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
#
# Visualize dependencies in BleachBit using Snakefood by Martin Blais
#
#


SPATH=/tmp/snakefood
BBCODE=../trunk/bleachbit
rm -rf $SPATH
rm -rf bleachbit.{sfood,dot,ps,pdf}
echo Downloading Snakefood
hg clone https://hg.furius.ca/public/snakefood/ $SPATH
echo Running sfood
PYTHONPATH="$SPATH/lib/python" python $SPATH/bin/sfood --internal $BBCODE > bleachbit.sfood
echo Running sfood-graph
cat bleachbit.sfood | PYTHONPATH="$SPATH/lib/python" python $SPATH/bin/sfood-graph > bleachbit.dot
echo Running GraphViz
dot -Tps bleachbit.dot  > bleachbit.ps
echo Converting PostScript to PDF
ps2pdf bleachbit.ps
echo Viewing PDF
gnome-open bleachbit.pdf
