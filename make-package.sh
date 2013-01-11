#!/usr/bin/env bash

# individual modules
DISK_BIN='us/us_d us/us_cmd us/mon_test us/script/* us/md-auto-resume/md-assume.sh us/md-auto-resume/mdscan/mdinfo'
UDV_LIB='udv/libudv.a'
UDV_BIN='udv/libpyext_udv.py'
WEBIFACE_BIN='web-iface/sys-manager'
ISCSI_BIN='iscsi/*'
NAS_BIN='nas/nas nas/nasconf nas/tr-simple nas/*.py nas/*.sh nas/usermanage'
SYSCONF_BIN='sys-conf/*'
COMMON_BIN='common/loglist common/log-daemon'
MON_BIN='monitor/sys-mon monitor/buzzer monitor/set-buzzer.sh monitor/libsysmon.py'

# sync list
BIN_LIST="$DISK_BIN $UDV_BIN $WEBIFACE_BIN $ISCSI_BIN $NAS_BIN $SYSCONF_BIN $COMMON_BIN $MON_BIN"
LIB_LIST="$UDV_LIB"

sync_apps()
{
	local _target="$1"
	local _rootfs="$2"
	mkdir -pv $_target
	mkdir -pv $_target/usr/local/{bin,lib}
	chmod +x $BIN_LIST
	cp -fRav $BIN_LIST  "$_target"/usr/local/bin/
	cp -fRav $LIB_LIST  "$_target"/usr/local/lib/
	chown -fRv root:root $_target/*
}

sync_rootfs()
{
	local _target="$1"
	mkdir -pv $_target/etc/{init.d,rc0.d,rc1.d,rc2.d,rc6.d,dhcp}
	mkdir -pv $_target/lib/modules/3.4.13/extra
	mkdir -pv $_target/usr/local/lib
	cp -fRav rootfs/* "$_target"/

	chown -fvR root:root $_target/*
	chmod -fv 440 $_target/etc/sudoers
}

tar_pkg()
{
	local _target="$1"
	_f="/tmp/apps-$(date +%Y%m%d-%H%M%S).tar.bz2"
	cd "$_target"
	tar jcf $_f ./*
	[ $? -eq 0 ] && echo "Package $_f created!"
}


target="/tmp/.pkg"
rm -fr $_target

sync_apps "$target"
[ "$1" = "--with-rootfs" ] && sync_rootfs "$target"
tar_pkg "$target"
