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
	update_cmd="pkg-install.sh"
	update_dir="/tmp/.update_dir"

	/etc/init.d/jw-apps stop

	mkdir $update_dir
	cd $update_dir
	tar xfj "$_pkg"
	rm -fr "$_pkg"
	if [ -f $update_cmd ]; then
		$update_cmd
	else
		cp -a ./* /
		cd /tmp
		rm -rf $update_dir
	fi

	if [ $? -eq 0 ]; then
		echo "package $_pkg installed OK!"
		sys-manager log --insert --module SysConf --category Auto --event Info --content '存储系统软件包升级成功!'
	else
		echo "package $_pkg install failed!"
	fi

	rm -f /usr/local/bin/*.py
	/etc/init.d/jw-apps start
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

[ "$package" = "" ] && usage
if [ ! -f "$package" ]; then
	echo "$package : No such file"
	exit 1
fi

if [ "$target" == "" ]; then
	local_install "$package"
else
	remote_install "$package" "$target"
fi
