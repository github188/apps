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

# ??????
PKG_TAR="/tmp/jwipsan-upgrade-$(date +%Y%m%d).tar.bz2"
PKG_BIN="/tmp/jwipsan-upgrade-$(date +%Y%m%d).bin"

sync_apps()
{
	local _target="$1"
	mkdir -p $_target/usr/local/bin

	echo "copy all app files ..."
	cp -fa $BIN_LIST  "$_target"/usr/local/bin/
	
	# ????python?ű?
	echo "compile python source ..."
	./compile-python "$_target"/usr/local/bin/ >/dev/null
	
	# ɾ??????Դ??, ?м??ļ?, ?????ļ?
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

	chmod -f 440 $_target/etc/sudoers
}

sync_conf()
{
	local _target="$1"
	
	echo "copy conf ..."
	mkdir -p $_target/opt/jw-conf/system/
	cp -fa monitor/conf-example.xml "$_target"/opt/jw-conf/system/sysmon-conf.xml
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
	openssl enc -des3 -salt -a -pass file:/sys/kernel/vendor -in $PKG_TAR -out $PKG_BIN
	[ $? -eq 0 ] && echo "Package $PKG_BIN create ok"
	#rm -f $PKG_TAR
}

target="/tmp/.pkg"
rm -fr $target
mkdir $target
rm -f $PKG_TAR
rm -f $PKG_BIN

sync_apps "$target"
sync_rootfs "$target"
sync_conf "$target"
if [ "x$1" = "x--kernel" ]; then
	sysnc_kernel "$target"
fi
tar_pkg "$target"
encode_pkg
