#!/bin/sh

# Purpose: Install packages needed on Ubuntu to build BleachBit .debs

# http://wiki.freegeek.org/index.php/Basic_Debian_Packaging
# http://ubuntuforums.org/showthread.php?t=51003
apt-get install build-essential dh-make debhelper devscripts fakeroot libnotify-bin

# These are just nice to have
apt-get install mc sshfs vim-full

# The same for openSUSE 11.1
# /usr/sbin/yast2 --install python-devel rpmlint
# sudo zypper install python-devel rpmlint mc make update-desktop-files
