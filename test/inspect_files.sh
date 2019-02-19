#!/bin/bash

i=$1

(broken=$(echo $i | perl -ne '/(.*)(\....)/; print "$1.broken$2"')
checkEagle --file $i  --crash-on-error --internal-check
xmllint --format $i -o $i.clean
xmllint --format $broken -o $broken.clean

diff -u $i.clean $broken.clean)2>&1 |less

