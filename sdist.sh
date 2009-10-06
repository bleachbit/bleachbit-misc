#!/bin/bash

# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Build clean source tarball and copy for building in virtual machine
#


VER=0.6.5
NAME=bleachbit
NAMEV=${NAME}-${VER}
SVND=/tmp/bleachbit_svn


if [[ -d $SVND ]]; then
	echo "svn update"
	cd $SVND/trunk
	svn update
else
	echo "mkdir $SVND"
	mkdir $SVND
	cd $SVND
	echo "svn checkout"
	svn co https://bleachbit.svn.sourceforge.net/svnroot/bleachbit/trunk
	cd -
	cd $SVND/trunk
fi


echo "python setup"
rm dist/$NAMEV.tar.{bz2,gz,lzma}
python setup.py sdist --formats=bztar,gztar

[[ -e "dist/$NAMEV.tar.gz" ]] || echo dist/$NAMEV.tar.gz missing
[[ -e "dist/$NAMEV.tar.gz" ]] || exit 1


echo "creating LZMA tarball"
bzcat $SVND/trunk/dist/$NAMEV.tar.bz2 | xz -9 - > $SVND/trunk/dist/$NAMEV.tar.lzma
[[ -e "dist/$NAMEV.tar.lzma" ]] || echo dist/$NAMEV.tar.lzma missing
[[ -e "dist/$NAMEV.tar.lzma" ]] || exit 1



echo "rpmbuild"
rm -f ~/rpmbuild/SOURCES/$NAMEV.tar.gz
cp $SVND/trunk/dist/$NAMEV.tar.gz ~/rpmbuild/SOURCES/
rm ~/rpmbuild/RPMS/noarch/bleachbit*rpm
rpmbuild -bb $NAME.spec


echo "rpmlint"
rpmlint ~/rpmbuild/RPMS/noarch/bleachbit*
cd -


echo "copying to ~/tmp/vm"
rm -f ~/tmp/vm/bleachbit-*.tar.{gz,bz2}
rm -rf ~/tmp/vm/debian/
mkdir -p ~/tmp/vm/
cp $SVND/trunk/dist/bleachbit-${VER}.tar.gz ~/tmp/vm/
cp -a $SVND/trunk/debian ~/tmp/vm/
cp -a $SVND/trunk/bleachbit.spec ~/tmp/vm/
