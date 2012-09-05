#!/usr/bin/env sh

if [ -f /usr/local/bin/sys-manager ]; then
	if `file /usr/local/bin/sys-manager | grep 'python script' > /dev/null`; then
		mv /usr/local/bin/sys-manager /usr/local/bin/sys-manager-py
	fi
fi

rsync -av web-iface/sys-manager /usr/local/bin/

rsync -av udv/libudv.a /usr/local/lib

rsync -av iscsi/iscsi /usr/local/bin

ldconfig
