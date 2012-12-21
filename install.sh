#!/usr/bin/env sh

target_ip="$1"
target=""
[ ! -z "$target_ip" ] && target="root@$target_ip:"

# individual modules
DISK_BIN='us/us_d us/us_cmd us/mon_test us/script/* us/md-auto-resume/md-assume.sh us/md-auto-resume/mdscan/mdinfo'
UDV_LIB='udv/libudv.a'
UDV_BIN='udv/libpyext_udv.py'
WEBIFACE_BIN='web-iface/sys-manager'
ISCSI_BIN='iscsi/*'
NAS_BIN='nas/nas nas/nasconf nas/tr-simple nas/*.py nas/*.sh nas/usermanage'
SYSCONF_BIN='sys-conf/*'
COMMON_BIN='common/loglist common/log-daemon'
MON_BIN='monitor/sys-mon monitor/buzzer monitor/set-buzzer.sh'

# sync list
BIN_LIST="$DISK_BIN $UDV_BIN $WEBIFACE_BIN $ISCSI_BIN $NAS_BIN $SYSCONF_BIN $COMMON_BIN $MON_BIN"
LIB_LIST="$UDV_LIB"

sync_target()
{
	local _target="$1"
	chmod +x $BIN_LIST
	rsync -av $BIN_LIST  "$_target"/usr/local/bin
	rsync -av $LIB_LIST  "$_target"/usr/local/lib
	#rsync -av rootfs/* "$_target"/
}

update_ld()
{
	local _target="$1"
	[ -z "$target" ] && ldconfig
}

sync_target "$target"
update_ld "$target"
