#!/usr/bin/env bash
set -e

sync_apps()
{
	echo "copy all app files ..."

	DISK_BIN="us/us_d us/us_cmd us/script/* us/md-auto-resume/md-assemble.sh \
			us/md-auto-resume/mdscan/mdinfo pic_ctl/utils/disk_reset"
	UDV_BIN="udv/*"
	WEBIFACE_BIN="web-iface/sys-manager"
	SYSCONF_BIN="sys-conf/* sys-conf/.build-date"
	COMMON_BIN="common/*"
	MON_BIN="monitor/sys-mon"
	MISC_BIN="led-ctl/daemon/led-ctl-daemon led-ctl/cmd/tools-test-led"
	
	# sync list
	BIN_LIST="$DISK_BIN $UDV_BIN $WEBIFACE_BIN $SYSCONF_BIN $COMMON_BIN \
			$MON_BIN $WEB_BIN $MISC_BIN"

	local target=$TARGET/usr/local/bin
	mkdir -p $target

	rsync -av --exclude Makefile --exclude *.h --exclude *.c --exclude *.a \
			--exclude *.o $BIN_LIST  $target/
	
	# 编译python脚本
	echo "compile python source ..."
	./compile-python $target/ >/dev/null
	
	# 删除程序源码, 中间文件, 配置文件
	echo "remove source ..."
	rm -f $target/*.py
	chmod +x $target/*
	chmod -x $target/*.pyc
	
	#  删除其他脚本
	rm -f $target/*adminmanage*
	rm -f $target/userconf
	rm -f $target/license
	rm -f $target/configbak
}

sync_conf()
{
	echo "copy conf ..."

	local target=$TARGET/opt/jw-conf

	mkdir -p $target/system
	cp -fa monitor/sysmon-conf.xml* $target/system/
	
	mkdir -p $target/disk
	cp -fa us/ata2slot.xml* $target/disk/
}

sync_init_script()
{
	echo "copy init script ..."

	SCRIPT_LIST="/etc/init.d/jw-driver /etc/init.d/jw-log /etc/init.d/jw-md \
		/etc/init.d/jw-sysmon /etc/init.d/jw-us"

	local target=$TARGET/etc/init.d
	mkdir -p $target
	cp -fa $SCRIPT_LIST $target/
}

tar_pkg()
{
	echo "pakaging ..."

	cd "$TARGET"
	chown -fR root:root ./*
	tar jcf $PKG_TAR ./*
	rm -rf $TARGET
}

usage()
{
	echo "usage:"
	echo "`basename $0` <version>"
	echo ""
}

VERSION=$1
if [ "$VERSION" = "" ]; then
	usage
	exit 1
fi

if [ `arch` = "x86_64" ]; then
	ARCH="64bit"
else
	ARCH="32bit"
fi
PKG_PREFIX="jw-storage"
PKG_TAR="/tmp/${PKG_PREFIX}-${VERSION}-${ARCH}.tar.bz2"

TARGET="/tmp/.pkg"
rm -fr $TARGET
mkdir $TARGET
rm -f $PKG_TAR

make clean
make isolated-storage=1
sync_apps
sync_conf
sync_init_script
tar_pkg
