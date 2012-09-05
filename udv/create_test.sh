#!/usr/bin/env sh

for num in `seq 1 10`
do
	sudo ./test "udv$num" 5000000
done
