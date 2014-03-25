#!/usr/bin/env bash

# individual modules
DISK_BIN='us/us_d us/us_cmd us/script/* us/md-auto-resume/md-assemble.sh us/md-auto-resume/mdscan/mdinfo pic_ctl/utils/disk_reset'
UDV_BIN='udv/*'
WEBIFACE_BIN='web-iface/sys-manager'
ISCSI_BIN='iscsi/*'
NAS_BIN='nas/*'
SYSCONF_BIN='sys-conf/* sys-conf/.build-date'
COMMON_BIN='common/*'
MON_BIN='monitor/*'
WEB_BIN='web/*'
MISC_BIN='watchdog/watchdog led-ctl/daemon/led-ctl-daemon led-ctl/cmd/tools-test-led'

# sync list
BIN_LIST="$DISK_BIN $UDV_BIN $WEBIFACE_BIN $ISCSI_BIN $NAS_BIN $SYSCONF_BIN $COMMON_BIN $MON_BIN $WEB_BIN $MISC_BIN"
LIB_LIST=""

# 升级包
if [ `arch` = "x86_64" ]; then
	ARCH="64bit"
else
	ARCH="32bit"
fi
pkg_prefix="jw-linux"
PKG_TAR="/tmp/${pkg_prefix}-upgrade-${ARCH}-$(date +%Y%m%d).tar.bz2"
PKG_BIN="/tmp/${pkg_prefix}-upgrade-${ARCH}-$(date +%Y%m%d).bin"

sync_apps()
{
	local _target="$1"
	mkdir -p $_target/usr/local/bin

	echo "copy all app files ..."
	cp -fa $BIN_LIST  "$_target"/usr/local/bin/
	
	# 编译python脚本
	echo "compile python source ..."
	./compile-python "$_target"/usr/local/bin/ >/dev/null
	
	# 删除程序源码, 中间文件, 配置文件
	echo "remove source ..."
	rm -f "$_target"/usr/local/bin/*.py
	rm -f "$_target"/usr/local/bin/Makefile
	rm -f "$_target"/usr/local/bin/*.c
	rm -f "$_target"/usr/local/bin/*.h
	rm -f "$_target"/usr/local/bin/*.o
	rm -f "$_target"/usr/local/bin/*.a
	rm -f "$_target"/usr/local/bin/*.xml
	chmod +x "$_target"/usr/local/bin/*
	chmod -x "$_target"/usr/local/bin/*.pyc
}

sync_rootfs()
{
	local _target="$1"
	
	echo "copy rootfs ..."
	cp -fa rootfs/* "$_target"/
	cp -fa rootfs-debian7/* "$_target"/

	chmod -f 440 $_target/etc/sudoers
}

sync_conf()
{
	local _target="$1"
	
	echo "copy conf ..."
	mkdir -p $_target/opt/jw-conf/system
	cp -fa monitor/sysmon-conf.xml* "$_target"/opt/jw-conf/system/
	
	mkdir -p $_target/opt/jw-conf/disk
	cp -fa us/ata2slot.xml* $_target/opt/jw-conf/disk/
}

sysnc_kernel()
{
	local _target="$1"
	
	echo "copy kernel ..."
	mkdir -p $_target/boot/grub
	mkdir -p $_target/lib/modules/
	cp -f /boot/*`uname -r` $_target/boot/
	cp -f /boot/grub/grub.cfg $_target/boot/grub/
	cp -fa /lib/modules/`uname -r` $_target/lib/modules/
}

sysnc_web()
{
	local _target="$1"
	local _source="$2" 
	local git_version
	local version
	
	echo "copy web ..."
	
	cd $_source
	git_version=`git log 2>/dev/null | head -n 1`
	if [ -z "$git_version" ]; then
		while [ -z "$version" ]
		do
			read -p "input web version: " version
		done
	else
		version=${git_version:0-6}
	fi
	
	mkdir -p $_target/var
	cp -fa $_source $_target/var/
	echo $version > $_target/var/www/version
}

tar_pkg()
{
	local _target="$1"
	
	echo "pakaging ..."
	cd "$_target"
	chown -fR root:root ./*
	tar jcf $PKG_TAR ./*
	rm -rf $_target
}

encode_pkg()
{
	echo "encoding pkg ..."
	openssl enc -des3 -salt -pass file:/sys/kernel/vendor -in $PKG_TAR -out $PKG_BIN
	[ $? -eq 0 ] && echo "Package $PKG_BIN create ok"
	rm -f $PKG_TAR
}

usage()
{
	echo "usage:"
	echo "    make-package.sh [--kernel] [--web <web_dir>]"
	echo ""
}

pack_kernel=0
pack_web=0
web_dir=""
while [ ! -z "$1" ]
do
	case "$1" in
		--kernel)
		pack_kernel=1
		;;
		--web)
		pack_web=1
		web_dir=$2
		shift
		;;
		*)
		usage
		exit 1
		;;
	esac
	shift
done

if [ $pack_web -eq 1 ] && [ ! -f "$web_dir/index.html" ]; then
	echo "web dir input error, please check"
	exit 1
fi

target="/tmp/.pkg"
rm -fr $target
mkdir $target
rm -f $PKG_TAR
rm -f $PKG_BIN

sync_apps "$target"
sync_rootfs "$target"
sync_conf "$target"
if [ $pack_kernel -eq 1 ]; then
	sysnc_kernel "$target"
fi
if [ $pack_web -eq 1 ]; then
	sysnc_web "$target" $web_dir
fi

# 定制化升级
if [ -x ./pkg-install-custom.sh ]; then
	cp ./pkg-install-custom.sh $target/
fi

tar_pkg "$target"
encode_pkg
