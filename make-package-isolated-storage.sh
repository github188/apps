#!/usr/bin/env bash
set -e

sync_apps()
{
	echo "copy all app files ..."

	local disk_bin="us/us_d us/us_cmd us/script/* us/md-auto-resume/md-assemble.sh \
			us/md-auto-resume/mdscan/mdinfo pic_ctl/utils/disk_reset"
	local udv_bin="udv/*"
	local webiface_bin="web-iface/sys-manager"
	local sysconf_bin="sys-conf/* sys-conf/.build-date"
	local common_bin="common/*"
	local mon_bin="monitor/sys-mon monitor/libsysmon.py"
	local misc_bin="led-ctl/daemon/led-ctl-daemon led-ctl/cmd/led-ctl \
			buzzer-ctl/daemon/buzzer-ctl-daemon buzzer-ctl/cmd/buzzer-ctl"
	
	# sync list
	local bin_list="$disk_bin $udv_bin $webiface_bin $sysconf_bin $common_bin \
			$mon_bin $web_bin $misc_bin"

	local target=$TARGET/usr/local/bin
	mkdir -p $target

	rsync -av --exclude Makefile --exclude *.h --exclude *.c --exclude *.a \
			--exclude *.o $bin_list  $target/
	
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

	local script_list="rootfs/etc/init.d/jw-driver rootfs/etc/init.d/jw-log \
			 rootfs/etc/init.d/jw-led rootfs/etc/init.d/jw-buzzer \
			 rootfs/etc/init.d/jw-sysmon rootfs/etc/init.d/jw-us \
			 rootfs/etc/init.d/jw-md"

	local target=$TARGET/etc/init.d
	mkdir -p $target
	cp -fa $script_list $target/
}

sync_shared_lib()
{
	echo "copy shared library ..."

	local shared_lib="/usr/lib/libparted*so* /usr/lib/libev*so*"
	local target=$TARGET/usr/lib
	mkdir -p $target
	
	cp -fa $shared_lib $target/
}

pkg_isolated_storage()
{
	echo "packaging isolated storage ..."

	cd "$TARGET"
	chown -fR root:root ./*
	tar jcf $PKG_TAR ./*
	rm -rf $TARGET
}

pkg_python()
{
	echo "packaging python2.6 ..."
	
	local python_pkg=/tmp/python2.6-${ARCH}.tar.bz2
	local target=/tmp/.python2.6
	local python_bin="/usr/bin/pydoc2.6 /usr/bin/pygettext2.6 /usr/bin/python2.6"
	local python_lib="/usr/lib/python2.6"

	rm -rf $target
	mkdir -p $target/usr/bin
	mkdir -p $target/usr/lib
	
	cp -fa $python_bin $target/usr/bin/
	cp -fa $python_lib $target/usr/lib/

	cd $target
	tar jcf $python_pkg ./*
	rm -rf $target
}

usage()
{
	echo "usage:"
	echo "`basename $0` <version> [python]"
	echo ""
}

VERSION=$1
if [ "$VERSION" = "" ]; then
	usage
	exit 1
fi

NEED_PYTHON=NO
if [ "$2" == "python" ]; then
	NEED_PYTHON=YES
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
make isolated-storage=1 no_disk_prewarn=1
sync_apps
sync_conf
sync_init_script
sync_shared_lib
pkg_isolated_storage

if [ "$NEED_PYTHON" = "YES" ]; then
	pkg_python
fi
