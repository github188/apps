#!/usr/bin/env sh

reset_sd()
{
	sd_list=$(ls /dev/sd[b-z])
	[ "$sd_list" = "" ] && return
	for sd in $sd_list
	do
		set -x
		echo $sd
		yes | parted "$sd" mklabel gpt
	done
}

if [ -f /usr/local/bin/sys-manager ]; then
	if `file /usr/local/bin/sys-manager | grep 'python script' > /dev/null`; then
		mv /usr/local/bin/sys-manager /usr/local/bin/sys-manager-py
	fi
fi

rsync -av web-iface/sys-manager /usr/local/bin/

rsync -av udv/libudv.a /usr/local/lib

rsync -av iscsi/* /usr/local/bin

cd us
./install.sh
cd -

reset_sd

ldconfig
