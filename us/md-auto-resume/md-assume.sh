#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin

mdadm -Ss >/dev/null 2>&1

disk_list=''

mddev_wait() # mddev
{
	mddev="$1"
	for i in `seq 5`
	do
		mdadm -D $mddev >/dev/null 2>&1
		[ $? -eq 0 ] && break
		sleep 1
	done
}

mddev_part_wait() # mddev
{
	mddev="$1"
	for i in `seq 5`
	do
		yes | parted $mddev print >/dev/null 2>&1
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
	local array_state
	mdadm -Af $mddev $disks >/dev/null 2>&1
	array_state=`cat /sys/block/md$1/md/array_state`
	if [ "$array_state" = "inactive" ]; then
		mdadm -S $mddev >/dev/null 2>&1
		return
	fi

	mddev_wait $mddev
	mddev_part_wait $mddev
}

RAID_DIR="/tmp/.raid-info"
RAID_DIR_LOCK="${RAID_DIR}/lock"
RAID_DIR_BYMD="${RAID_DIR}/by-md"
RAID_DIR_BYNAME="${RAID_DIR}/by-name"
RAID_DIR_BYUUID="${RAID_DIR}/by-uuid"
RAID_DIR_BYDISK="${RAID_DIR}/by-disk"

if [ ! -d $RAID_DIR ]; then
	rm -rf $RAID_DIR
	mkdir $RAID_DIR
fi
if [ ! -d $RAID_DIR_LOCK ]; then
	rm -rf $RAID_DIR_LOCK
	mkdir $RAID_DIR_LOCK
fi
if [ ! -d $RAID_DIR_BYMD ]; then
	rm -rf $RAID_DIR_BYMD
	mkdir $RAID_DIR_BYMD
fi
if [ ! -d $RAID_DIR_BYNAME ]; then
	rm -rf $RAID_DIR_BYNAME
	mkdir $RAID_DIR_BYNAME
fi
if [ ! -d $RAID_DIR_BYUUID ]; then
	rm -rf $RAID_DIR_BYUUID
	mkdir $RAID_DIR_BYUUID
fi
if [ ! -d $RAID_DIR_BYDISK ]; then
	rm -rf $RAID_DIR_BYDISK
	mkdir $RAID_DIR_BYDISK
fi

while read LINE
do
        #echo "$LINE"
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

if [ $? -eq 0 ]; then
	echo "VG ReAssembled OK"
fi
