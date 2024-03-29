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
	update_dir="/tmp/.update_dir"
	custom_update_cmd="$update_dir/pkg-install-custom.sh"

	rm -rf $update_dir
	mkdir $update_dir
	cd $update_dir
	tar xfj "$_pkg"
	ret=$?
	rm -fr "$_pkg"
	if [ $ret -ne 0 ]; then
		rm -rf $update_dir
		return 2
	fi

	if [ "x`uname -m`" = "xx86_64" ]; then
		platform="64-bit"
	else
		platform="32-bit"
	fi

	if ! file usr/local/bin/sys-manager | grep -q $platform; then
		cd /tmp
		rm -rf $update_dir
		return 3
	fi

	if [ -x $custom_update_cmd ]; then
		$custom_update_cmd
		ret=$?
		if [ $ret -ne 0 ]; then
			cd /tmp
			rm -rf $update_dir
			return $ret
		fi
	else
		cp -fa ./* /
	fi

	cd /tmp
	rm -rf $update_dir
	rm -f /usr/local/bin/*.py

	return 0
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
	echo "升级包: $package 不存在"
	exit 1
fi

if [ "$target" == "" ]; then
	local_install "$package"
	ret=$?
	if [ $ret -eq 0 ]; then
		echo "升级包: $package 安装成功"
		exit 0
	elif [ $ret -eq 2 ]; then
		echo "升级包格式错误"
	elif [ $ret -eq 3 ]; then
		echo "升级包不适用本机的系统平台"
	elif [ $ret -eq 4 ]; then
		echo "升级包不兼容本机的系统版本"
	else
		echo "升级失败"
	fi
	exit $ret
else
	remote_install "$package" "$target"
fi
