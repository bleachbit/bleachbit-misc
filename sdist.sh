#!/bin/bash

# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Build clean source tarball and copy for building in virtual machine
#


NAME=bleachbit
SVND=/tmp/bleachbit_svn
BRANCH=/releases/0.8.4
BRANCHD=$SVND/0.8.4


if [[ -d $SVND ]]; then
	echo "svn update"
	cd $SVND
	svn update
	cd $BRANCHD
else
	echo "mkdir $SVND"
	mkdir $SVND
	cd $SVND
	echo "svn checkout"
	svn co https://bleachbit.svn.sourceforge.net/svnroot/bleachbit/$BRANCH
	cd -
	cd $BRANCHD
fi


echo "python setup"
VER=`python bleachbit.py --version | perl -ne 'print if s/^BleachBit version (.*)/$1/'`
NAMEV=${NAME}-${VER}
make clean
python setup.py sdist --formats=bztar,gztar

[[ -e "dist/$NAMEV.tar.gz" ]] || echo dist/$NAMEV.tar.gz missing
[[ -e "dist/$NAMEV.tar.gz" ]] || exit 1


echo "creating LZMA tarball"
bzcat $BRANCHD/dist/$NAMEV.tar.bz2 | xz -9 - > $BRANCHD/dist/$NAMEV.tar.lzma
[[ -e "dist/$NAMEV.tar.lzma" ]] || echo dist/$NAMEV.tar.lzma missing
[[ -e "dist/$NAMEV.tar.lzma" ]] || exit 1



echo "rpmbuild"
rm -f ~/rpmbuild/SOURCES/$NAMEV.tar.gz
cp $BRANCHD/dist/$NAMEV.tar.gz ~/rpmbuild/SOURCES/
rm -f ~/rpmbuild/RPMS/noarch/bleachbit*rpm
rpmbuild -bb $NAME.spec


echo "rpmlint"
rpmlint ~/rpmbuild/RPMS/noarch/bleachbit*
cd -


echo "copying to ~/tmp/vm"
rm -f ~/tmp/vm/bleachbit-*.tar.{gz,bz2}
rm -rf ~/tmp/vm/debian/
mkdir -p ~/tmp/vm/
cp $BRANCHD/dist/bleachbit-${VER}.tar.gz ~/tmp/vm/
cp -a $BRANCHD/debian ~/tmp/vm/
cp -a $BRANCHD/bleachbit.spec ~/tmp/vm/
