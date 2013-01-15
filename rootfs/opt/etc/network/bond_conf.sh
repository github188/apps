#!/bin/bash

modprobe bonding
2>&1 echo -bond0 > /sys/class/net/bonding_masters >/dev/null
[ $? -eq 0 ] && echo "Bounding Device bond0 Loaded Success!"

