#!/bin/sh
# for arm hisi3536 hardware

mdadm -Ss
cd /usr/local/modules
rmmod raid456 2>/dev/null
rmmod raid10 2>/dev/null
rmmod raid1 2>/dev/null
rmmod raid0 2>/dev/null
rmmod linear 2>/dev/null
rmmod md-mod 2>/dev/null
rmmod async_pq.ko 2>/dev/null
rmmod async_raid6_recov.ko 2>/dev/null
rmmod raid6_pq.ko 2>/dev/null
rmmod async_memcpy.ko 2>/dev/null
rmmod async_xor.ko 2>/dev/null
rmmod async_tx.ko 2>/dev/null
rmmod xor.ko 2>/dev/null

insmod xor.ko
insmod async_tx.ko
insmod async_xor.ko
insmod async_memcpy.ko
insmod raid6_pq.ko
insmod async_raid6_recov.ko
insmod async_pq.ko
insmod md-mod.ko
insmod linear.ko
insmod raid0.ko
insmod raid1.ko
insmod raid10.ko
insmod raid456.ko
if [ $? -ne 0 ]; then
	echo "raid modules insmod error."
	cd - >/dev/null
	exit 1
fi
cd - >/dev/null

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

sys-manager vg --load-sync-prio >/dev/null
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

