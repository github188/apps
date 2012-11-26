#!/usr/bin/env sh

set -x

target_ip="$1"
target=""
[ ! -z "$target_ip" ] && target="root@$target_ip:"

reset_sd()
{
	sd_list=$(ls /dev/sd[b-z])
	[ "$sd_list" = "" ] && return
	for sd in $sd_list
	do
		echo $sd
		yes | parted "$sd" mklabel gpt
	done
}

#if [ -f /usr/local/bin/sys-manager ]; then
#	if `file /usr/local/bin/sys-manager | grep 'python script' > /dev/null`; then
#		mv /usr/local/bin/sys-manager /usr/local/bin/sys-manager-py
#	fi
#fi

file_list='us/us_d us/us_cmd us/mon_test us/script/* us/md-auto-resume/md-assume.sh us/md-auto-resume/mdscan/mdinfo'
rsync -av $file_list "$target"/usr/local/bin/

rsync -av web-iface/sys-manager "$target"/usr/local/bin/

rsync -av udv/libudv.a "$target"/usr/local/lib
rsync -av udv/libpyext_udv.py "$target"/usr/local/bin

rsync -av iscsi/* "$target"/usr/local/bin

rsync -av extra/* "$target"/usr/local/bin

rsync -av nas/nas "$target"/usr/local/bin
rsync -av nas/nasconf "$target"/usr/local/bin
rsync -av nas/tr-simple "$target"/usr/local/bin
rsync -av nas/*.py "$target"/usr/local/bin
rsync -av nas/*.sh "$target"/usr/local/bin
rsync -av nas/lib*.py "$target"/usr/local/bin

rsync -av sys-conf/* "$target"/usr/local/bin

rsync -av conf/* "$target"/

rsync -v common/loglist "$target"/usr/local/bin

rsync -av driver-backup/* "$target"/lib/modules/3.4.13/extra

#reset_sd
[ -z "$target" ] && ldconfig
