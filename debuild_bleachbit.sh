#!/bin/bash

# Copyright (C) 2009 by Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# http://bleachbit.blogspot.com/2009/02/building-virtual-ubuntu.html
#

# Handle fatal errors.
function fail {
	echo $1
	notify-send -u critical $1
        exit 1
}

# Check which version of Ubuntu is running.
RELEASE=`grep DISTRIB_RELEASE /etc/lsb-release | cut -b17-`
echo "Detected version distribution version $RELEASE"

mkdir ~/bleachbit
cd ~/bleachbit
# Extract the source code tarball.
tar xzvf ~/tmp/vm/bleachbit*.tar.gz || fail "tar failed"
cd ~/bleachbit/bleachbit-[0-9].[0-9].[0-9]* || fail "'cd' failed"
# Create .deb packaging directory.
mkdir debian
cd debian
# Copy .deb packaging files.
cp ~/tmp/vm/debian/* .
# Create links because openSUSE Build Service and dpkg like different names.
ln -s debian.control control
ln -s debian.rules rules
ln -s debian.changelog changelog
cd ~/bleachbit/bleachbit-[0-9].[0-9].[0-9]*
# Ubuntu 6.06 doesn't have Python central, so remove it.
if [[ "x$RELEASE" == "x6.06" ]];
then
	echo "Applying Ubuntu 6.06 changes"
	cd debian
	sed -i -e 's/, python-central//g' control
	sed -i -e 's/, python-central//g' bleachbit.dsc
	sed -i -e 's/dh_pycentral//g' rules
	cd ..

fi
# Build.
debuild
# Check build.
cd ~/bleachbit
[[ ! -e *deb ]] || fail "no .deb files"
# Lintian performs checks against a database of packaging rules.
lintian *deb
