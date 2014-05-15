#!/bin/bash

# Copyright (C) 2014 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Build clean source tarball
#


NAME=bleachbit
GITD=/tmp/bleachbit_git
GITURL=https://github.com/az0/bleachbit.git

if [[ -d $GITD ]]; then
	echo "rm -rf $GITD"
	rm -rf "$GITD"
fi
echo "mkdir $GITD"
mkdir $GITD
cd $GITD
echo "git clone "
git clone --single-branch $GITURL $GITDIR
cd bleachbit

echo "python setup"
VER=`python bleachbit.py --version | perl -ne 'print if s/^BleachBit version (.*)/$1/'`
NAMEV=${NAME}-${VER}
make clean
python setup.py sdist --formats=bztar,gztar

[[ -e "dist/$NAMEV.tar.gz" ]] || echo dist/$NAMEV.tar.gz missing
[[ -e "dist/$NAMEV.tar.gz" ]] || exit 1


echo "creating LZMA tarball"
bzcat dist/$NAMEV.tar.bz2 | xz -9 - > dist/$NAMEV.tar.lzma
[[ -e "dist/$NAMEV.tar.lzma" ]] || echo dist/$NAMEV.tar.lzma missing
[[ -e "dist/$NAMEV.tar.lzma" ]] || exit 1


