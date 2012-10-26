#!/bin/bash

echo +bond0 > /sys/class/net/bonding_masters
echo 0 > /sys/class/net/bond0/bonding/mode
ifconfig bond0 192.168.70.88 netmask 255.255.255.0 up
echo 100 > /sys/class/net/bond0/bonding/miimon
ifdown eth2 > /dev/null
echo +eth2 > /sys/class/net/bond0/bonding/slaves
ifdown eth3 > /dev/null
echo +eth3 > /sys/class/net/bond0/bonding/slaves

