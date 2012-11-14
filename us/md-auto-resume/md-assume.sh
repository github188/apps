#!/usr/bin/env bash

export PATH=/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin

mdadm -Ss

disk_list=''

assemble() # arg1: md_num, arg2: disk_list
{
	if [ -z "$1" -o -z "$2" ]; then
		return
	fi

	local mddev=/dev/md$1
	local disks=$2
	local disk
	local slaves
	local disk_name
	mdadm -Af $mddev $disks
	slaves=`ls /sys/block/md1/slaves 2>/dev/null`
	if [ -z "$slaves" ]; then
		return
	fi

	for disk in $disks
	do
		disk_name=${disk##*/}
		if ! echo $slaves | grep -w "$disk_name" 1>/dev/null 2>&1; then
			mdadm -a $mddev $disk
		fi
	done
}

while read LINE
do
        echo "$LINE"
        if `echo "$LINE" | grep "Get md" >/dev/null`; then
		if [ ! -z "$disk_list" ]; then
			assemble $md_num "$disk_list"
			disk_list=''
		fi
                md_num=${LINE##*md_num: }
                continue
        fi
        disk_list="$disk_list $LINE"
done<<EOF
$(/usr/local/bin/mdinfo 2>/dev/null)
EOF

if [ ! -z "$disk_list" ]; then
	assemble $md_num "$disk_list"
fi

