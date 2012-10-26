#!/usr/bin/env bash

export PATH=/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin

mdadm -Ss

disks=0
disk_list=''

while read LINE
do
        echo "$LINE"
        if `echo "$LINE" | grep "Get md" >/dev/null`; then
                disks=${LINE##*disks=}
                disks=${disks%%,*}
                md_num=${LINE##*md_num: }
                continue
        fi
        if [ $disks -ge 0 ]; then
                disk_list="$disk_list $LINE"
                let "disks=disks-1"
        fi
        if [ $disks -eq 0 ] && [ ! -z "$disk_list" ]; then
                2>/dev/null mdadm -A /dev/md$md_num $disk_list
                disks=0
                disk_list=''
        fi
done<<EOF
$(/usr/local/bin/mdinfo 2>/dev/null)
EOF
