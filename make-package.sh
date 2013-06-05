#!/usr/bin/env bash

# individual modules
DISK_BIN='us/us_d us/us_cmd us/mon_test us/script/* us/md-auto-resume/md-assume.sh us/md-auto-resume/mdscan/mdinfo pic_ctl/test/dled_test test-utils/tools-test-led'
UDV_LIB='udv/libudv.a'
UDV_BIN='udv/libpyext_udv.py'
WEBIFACE_BIN='web-iface/sys-manager'
ISCSI_BIN='iscsi/*'
NAS_BIN='nas/nas nas/nasconf nas/tr-simple nas/*.py nas/*.sh nas/usermanage'
SYSCONF_BIN='sys-conf/* sys-conf/.build-date'
COMMON_BIN='common/loglist common/log-daemon common/libcommon.py'
MON_BIN='monitor/sys-mon monitor/buzzer monitor/set-buzzer.sh monitor/libsysmon.py'
WEB_BIN='web/*'

# sync list
BIN_LIST="$DISK_BIN $UDV_BIN $WEBIFACE_BIN $ISCSI_BIN $NAS_BIN $SYSCONF_BIN $COMMON_BIN $MON_BIN $WEB_BIN"
LIB_LIST="$UDV_LIB"

sync_apps()
{
	local _target="$1"
	mkdir -pv $_target/usr/local/{bin,lib}
	chmod +x $BIN_LIST
	cp -fRav $BIN_LIST  "$_target"/usr/local/bin/
	rm -f "$_target"/usr/local/bin/Makefile
	rm -f "$_target"/usr/local/bin/*.c
	rm -f "$_target"/usr/local/bin/*.h
	cp -fRav $LIB_LIST  "$_target"/usr/local/lib/
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
