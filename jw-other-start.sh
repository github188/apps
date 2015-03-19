#!/bin/sh
# for other hardware

RAID_DIR="/var/run/raid-info"
RAID_DIR_LOCK="${RAID_DIR}/lock"
RAID_DIR_BYMD="${RAID_DIR}/by-md"
RAID_DIR_BYNAME="${RAID_DIR}/by-name"
RAID_DIR_BYUUID="${RAID_DIR}/by-uuid"
RAID_DIR_BYDISK="${RAID_DIR}/by-disk"

rm -rf $RAID_DIR
mkdir $RAID_DIR
mkdir $RAID_DIR_LOCK
mkdir $RAID_DIR_BYMD
mkdir $RAID_DIR_BYNAME
mkdir $RAID_DIR_BYUUID
mkdir $RAID_DIR_BYDISK

PROGS="/usr/local/bin/log-daemon /usr/local/bin/us_d"
for prog in $PROGS
do
	pidfile=/var/run/`basename $prog`.pid
	pid=`cat $pidfile 2>/dev/null`
	if ls -l /proc/$pid/exe 2>/dev/null | grep -q $prog; then
		kill $pid
		sleep 1
	fi
	start-stop-daemon --start --make-pidfile --pidfile $pidfile --background  --exec $prog
	if [ $? -eq 0 ]; then
		echo `basename $prog` started
	else
		echo `basename $prog` start fail!
		exit 1
	fi
done

/usr/local/bin/md-assemble.sh
	
# 等待md添加到tmp目录
while true
do
	sys_mds=`ls /sys/block/ | grep "md[1-9]" | wc -l`
	tmp_mds=`ls $RAID_DIR_BYUUID | wc -l`
	if [ $tmp_mds -lt $sys_mds ]; then
		sleep 1
		continue
	else
		break
	fi
done

