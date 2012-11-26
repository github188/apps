#!/bin/bash

modprobe bonding
echo -bond0 > /sys/class/net/bonding_masters

/opt/bond_conf.sh
/opt/dns.conf