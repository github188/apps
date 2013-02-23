#!/bin/bash

usage()
{
	echo ""
	echo "pkg-install.sh -p|--package filename [-t|--target remote_ip]"
	echo ""
	exit -1
}

local_install()
{
	local _pkg="$1"
	/etc/init.d/jw-apps stop
	cd /
	tar jxvf "$_pkg"
	if [ $? -eq 0 ]; then
		echo "---------- package $_pkg installed OK! ------------"
		sys-manager log --insert --module SysConf --category Auto --event Info --content '存储系统软件包升级成功!'
	else
		echo "---------- package $_pkg install failed! ------------"
	fi
	/etc/init.d/jw-apps start
	rm -fr "$_pkg"
}

remote_install()
{
	local _pkg="$1"
	local _rmt="$2"
	scp "$_pkg" "root@$_rmt:$_pkg"
	ssh "root@$_rmt" "pkg-install.sh --package $_pkg"
}

TEMP=`getopt -o p:t: --long package:,target: -n 'pkg-install.sh' -- "$@"`

if [ $? != 0 ]; then
	echo "Terminating..." >&2
	exit 1
fi

eval set -- "$TEMP"

target=""
package=""

while true; do
	case "$1" in
		-p|--package) package="$2" ; shift 2 ;;
		-t|--target) target="$2" ; shift 2 ;;
		--) shift ; break ;;
		*) echo "Internal error!" ; exit 1 ;;
	esac
done

echo "$package"
echo "$target"

[ "$package" = "" ] && usage

if [ "$target" == "" ]; then
	local_install "$package"
else
	remote_install "$package" "$target"
fi
