#!/usr/bin/env bash

# individual modules
DISK_BIN='us/us_d us/us_cmd us/script/* us/md-auto-resume/md-assemble.sh us/md-auto-resume/mdscan/mdinfo pic_ctl/test/dled_test test-utils/tools-test-led'
UDV_BIN='udv/*'
WEBIFACE_BIN='web-iface/sys-manager'
ISCSI_BIN='iscsi/*'
NAS_BIN='nas/*'
SYSCONF_BIN='sys-conf/* sys-conf/.build-date'
COMMON_BIN='common/*'
MON_BIN='monitor/*'
WEB_BIN='web/*'

# sync list
BIN_LIST="$DISK_BIN $UDV_BIN $WEBIFACE_BIN $ISCSI_BIN $NAS_BIN $SYSCONF_BIN $COMMON_BIN $MON_BIN $WEB_BIN"
LIB_LIST=""

sync_apps()
{
	local _target="$1"
	mkdir -pv $_target/usr/local/{bin,lib}

	cp -fRav $BIN_LIST  "$_target"/usr/local/bin/
	cp -fRav $LIB_LIST  "$_target"/usr/local/lib/
	
	# 编译python脚本
	./compile-python "$_target"/usr/local/bin/
	
	# 删除程序源码, 中间文件, 配置文件
	rm -f "$_target"/usr/local/bin/*.py
	rm -f "$_target"/usr/local/bin/Makefile
	rm -f "$_target"/usr/local/bin/*.c
	rm -f "$_target"/usr/local/bin/*.h
	rm -f "$_target"/usr/local/bin/*.o
	rm -f "$_target"/usr/local/bin/*.a
	rm -f "$_target"/usr/local/bin/*.xml
	chmod +x "$_target"/usr/local/bin/*
	chmod -x "$_target"/usr/local/bin/*.pyc

	chown -fRv root:root $_target/*
}

sync_rootfs()
{
	local _target="$1"
	cp -fRav rootfs/* "$_target"/

	chown -fvR root:root $_target/*
	chmod -fv 440 $_target/etc/sudoers
}

sync_conf()
{
	local _target="$1"
	mkdir -pv $_target/opt/jw-conf/system/
	mkdir -pv $_target/opt/jw-conf.bak/system/
	cp -fav monitor/conf-example.xml "$_target"/opt/jw-conf/system/sysmon-conf.xml
	cp -fav monitor/conf-example.xml "$_target"/opt/jw-conf.bak/system/sysmon-conf.xml
}

tar_pkg()
{
	local _target="$1"
	_f="/tmp/apps-$(date +%Y%m%d-%H%M%S).tar.bz2"
	cd "$_target"
	tar jcf $_f ./*
	[ $? -eq 0 ] && echo "Package $_f created!"
	rm -rf $_target
}


target="/tmp/.pkg"
rm -fr $target
mkdir $target

sync_apps "$target"
sync_rootfs "$target"
sync_conf "$target"
tar_pkg "$target"
