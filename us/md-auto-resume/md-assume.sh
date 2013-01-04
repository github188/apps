#!/usr/bin/env bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin

mdadm -Ss

disk_list=''

mddev_wait() # mddev
{
	mddev="$1"
	for i in `seq 5`
	do
		mdadm -D $mddev 2>&1 >/dev/null
		[ $? -eq 0 ] && break
		sleep 1
	done
}

mddev_part_wait() # mddev
{
	mddev="$1"
	for i in `seq 5`
	do
		yes | parted $mddev print 2>&1 >/dev/null
		[ $? -eq 0 ] && break
		sleep 1
	done
}

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
	local array_state
	mdadm -Af $mddev $disks
	array_state=`cat /sys/block/md$1/md/array_state`
	if [ "$array_state" = "inactive" ]; then
		mdadm -S $mddev
		return
	fi
	slaves=`ls /sys/block/md$1/slaves 2>/dev/null`
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

	# restore partitions
	#yes Fix | parted "$mddev" print > /dev/null

	mddev_wait $mddev
	mddev_part_wait $mddev
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

