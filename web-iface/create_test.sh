#!/usr/bin/env sh

for num in `seq 1 10`
do
	sudo ./sys-manager udv --create --vg /dev/md1 --name "udv$num" --capacity 5000000
done
