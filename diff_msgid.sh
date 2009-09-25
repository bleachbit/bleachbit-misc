#!/bin/bash

# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Compare change .pot strings from trunk to release version given on command line
#


OLDPO=../releases/$1/po
[ -d $OLDPO ] ||  echo "$OLDPO does not exist"
[ -d $OLDPO ] ||  exit

cd ../trunk/po
make bleachbit.pot
cd -

cd ../releases/$1/po
make bleachbit.pot
cd -

msggrep -Kie . --no-wrap ../trunk/po/bleachbit.pot  | grep ^msgid  | cut -c 8- | sort > /tmp/msgid-trunk
msggrep -Kie . --no-wrap $OLDPO/bleachbit.pot  | grep ^msgid  | cut -c 8- | sort > /tmp/msgid-release-$1

diff -u /tmp/msgid-{release-$1,trunk}

rm -f /tmp/msgid-trunk
rm -f /tmp/msgid-release-$1

cd $OLDPO
make clean
cd -
