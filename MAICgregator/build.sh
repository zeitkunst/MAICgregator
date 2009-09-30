#!/bin/bash

if /usr/bin/test "$#" -ne 1; then
    echo "Build new versions of the extension for distribution,"
    echo "copy them to the static directory of the website,"
    echo "and add them to the svn repository."
    echo ""
    echo "Usage: bash build.sh versionNumber"
    exit 1
fi

XPI_NAME=MAICgregator.$1.xpi

zip -r $XPI_NAME . -x "*.svn/*" \*.xpi

cp $XPI_NAME ../MAICgregatorServer/static
svn add ../MAICgregatorServer/static/$XPI_NAME

openssl sha1 $XPI_NAME
