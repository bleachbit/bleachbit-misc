#!/bin/bash

# Copyright (C) 2014 by Andrew Ziem. All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Some material from the Automatic Build System Setup for Chakra (GPLv3+)
# Some material from makepkg (GPLv2+)
#
# Helps automate finding duplicate cleaners in the bleachbit repositories via FSlint.
# To use, you will need: bash, git, and fslint installed.
#
#

# Workspace name (safe to change)
WORKSPACENAME="duplicate-scan-workspace"

# Directory variables
CURDIR="${PWD}"
WORKSPACE="${CURDIR}/${WORKSPACENAME}"

# Formatted output functions
msg() {
        local mesg=$1; shift
        printf "${GREEN}==>${ALL_OFF}${BOLD} ${mesg}${ALL_OFF}\n" "$@" >&2
}

msg2() {
        local mesg=$1; shift
        printf "${BLUE}  ->${ALL_OFF}${BOLD} ${mesg}${ALL_OFF}\n" "$@" >&2
}

# Delete old workspace if one exists
if [ -d "${WORKSPACE}" ]; then
    msg "Deleting old workspace..."
    # Needs sudo because of write-protected .git files
    sudo rm -rd "${WORKSPACE}"
fi

# Create a new workspace
msg "Creating new workspace..."
msg2 "Cloning az0/bleachbit..."
git clone https://github.com/az0/bleachbit.git "${WORKSPACE}"/bleachbit
msg2 "Cloning az0/cleanerml..."
git clone https://github.com/az0/cleanerml.git "${WORKSPACE}"/cleanerml

# Launch fslint targeting the workspace while hiding standard output
msg "Launching FSlint..."
fslint-gui "${WORKSPACE}" > /dev/null 2>&1
