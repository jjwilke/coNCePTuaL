#! /usr/bin/env bash

glibtoolize --copy
aclocal
autoheader
touch substitutions.dat.in
touch ncptl.pc.in
rm -f ChangeLog config.sub config.guess
automake --add-missing --copy
autoconf
