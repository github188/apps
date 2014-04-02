#!/usr/bin/env bash
set -e

sync_apps()
{
	echo "copy all app files ..."

	local disk_bin="us/us_d us/us_cmd us/script/* us/md-auto-resume/md-assemble.sh \
			us/md-auto-resume/mdscan/mdinfo pic_ctl/utils/disk_reset"
	local udv_bin="udv/* nas/libnas.py"
	local webiface_bin="web-iface/sys-manager"
	local sysconf_bin="sys-conf/* sys-conf/.build-date"
	local common_bin="common/*"
	local mon_bin="monitor/sys-mon monitor/libsysmon.py"
	local misc_bin="led-ctl/daemon/led-ctl-daemon led-ctl/cmd/led-ctl \
			buzzer-ctl/daemon/buzzer-ctl-daemon buzzer-ctl/cmd/buzzer-ctl"
	
	# sync list
	local bin_list="$disk_bin $udv_bin $webiface_bin $sysconf_bin $common_bin \
			$mon_bin $web_bin $misc_bin"

	local tmp_dir=$TMP_DIR_STORAGE/usr/local/bin
	mkdir -p $tmp_dir

	rsync -a --exclude Makefile --exclude *.h --exclude *.c --exclude *.a \
			--exclude *.o $bin_list  $tmp_dir/
	
	# 编译python脚本
	echo "compile python source ..."
	./compile-python $tmp_dir/ >/dev/null
	
	# 删除程序源码, 中间文件, 配置文件
	echo "remove source ..."
	rm -f $tmp_dir/*.py
	chmod +x $tmp_dir/*
	chmod -x $tmp_dir/*.pyc
	
	#  删除其他脚本
	rm -f $tmp_dir/*adminmanage*
	rm -f $tmp_dir/userconf
	rm -f $tmp_dir/license
	rm -f $tmp_dir/configbak
	
	mkdir $TMP_DIR_STORAGE/usr/local/sbin
	cp /tmp/mdadm $TMP_DIR_STORAGE/usr/local/sbin
}

sync_conf()
{
	echo "copy conf ..."

	local tmp_dir=$TMP_DIR_STORAGE/opt/jw-conf

	mkdir -p $tmp_dir/system
	cp -fa monitor/sysmon-conf.xml* $tmp_dir/system/
	
	mkdir -p $tmp_dir/disk
	cp -fa us/ata2slot.xml* $tmp_dir/disk/
}

sync_init_script()
{
	echo "copy init script ..."

	local script_list="rootfs/etc/init.d/jw-driver rootfs/etc/init.d/jw-log \
			 rootfs/etc/init.d/jw-led rootfs/etc/init.d/jw-buzzer \
			 rootfs/etc/init.d/jw-sysmon rootfs/etc/init.d/jw-us \
			 rootfs/etc/init.d/jw-md"

	local tmp_dir=$TMP_DIR_STORAGE/etc/init.d
	mkdir -p $tmp_dir
	cp -fa $script_list $tmp_dir/
}

sync_shared_lib()
{
	echo "copy shared library ..."

	local shared_lib="/usr/lib/libparted*so* /usr/lib/libev*so*"
	local tmp_dir=$TMP_DIR_STORAGE/usr/lib
	mkdir -p $tmp_dir
	
	cp -fa $shared_lib $tmp_dir/
}

pkg_isolated_storage()
{
	echo "packaging isolated storage ..."

	local pkg_dir=$PKG_DIR/usr
	mkdir -p $pkg_dir
	cp install-jw-storage.sh $pkg_dir/
	chmod +x $pkg_dir/install-jw-storage.sh

	cd "$TMP_DIR_STORAGE"
	chown -fR root:root ./*
	
	tar jcf $pkg_dir/$PKG_STORAGE ./*
	cd - >/dev/null
	rm -rf $TMP_DIR_STORAGE
}

pkg_python()
{
	echo "packaging python2.6 ..."
	
	if [ "`which python2.6`" = "" ]; then
		echo -e "\033[0;33;1mWarning: Not found python2.6\033[0m"
		local val
		read -p "Continue? [y/n]: " val
		if [ "val" != "y" ]; then
			exit 1
		else
			return
		fi
	fi

	local pkg_dir=$PKG_DIR/usr
	mkdir -p $pkg_dir

	local python_bin="/usr/bin/pydoc2.6 /usr/bin/pygettext2.6 /usr/bin/python2.6"
	local python_lib="/usr/lib/python2.6"

	mkdir -p $TMP_DIR_PYTHON/usr/bin
	mkdir -p $TMP_DIR_PYTHON/usr/lib
	
	cp -fa $python_bin $TMP_DIR_PYTHON/usr/bin/
	cp -fa $python_lib $TMP_DIR_PYTHON/usr/lib/

	cd $TMP_DIR_PYTHON
	tar jcf $pkg_dir/$PKG_PYTHON ./*
	cd - >/dev/null
	rm -rf $TMP_DIR_PYTHON
}

pkg_kernel()
{
	local pkg_dir=$PKG_DIR/kernel
	mkdir -p $pkg_dir
	cp install-jw-kernel.sh $pkg_dir/
	chmod +x $pkg_dir/install-jw-kernel.sh
	
	local pkg_kernel=`ls /tmp/jw-kernel-*-${ARCH}.tar.bz2 2>/dev/null`
	if [ "$pkg_kernel" = "" ]; then
		echo -e "\033[0;31;1mNot found jw kernel package in /tmp dir.\033[0m"
		exit 1
	fi
	
	local val
	read -p "Confirm kernel package: \"$pkg_kernel\" [y/n]: " val
	if [ "$val" != "y" ]; then
		exit 1
	fi
	
	mv $pkg_kernel $pkg_dir/
}

pkg_all()
{
	echo "packging all ..."
	cp jw-storage-install-guide.txt $PKG_DIR/
	cd /tmp
	tar jcf /tmp/$PKG_STORAGE ./jw-storage-${VERSION}
	rm -fr ./jw-storage-${VERSION}
}

usage()
{
	echo "usage:"
	echo "`basename $0` <version> [kernel]"
	echo ""
}

VERSION=$1
if [ "$VERSION" = "" ]; then
	usage
	exit 1
fi

KERNEL=$2

if [ `arch` = "x86_64" ]; then
	ARCH="64bit"
else
	ARCH="32bit"
fi

PKG_STORAGE="jw-storage-${VERSION}-${ARCH}.tar.bz2"
PKG_PYTHON="python2.6-${ARCH}.tar.bz2"

PKG_DIR="/tmp/jw-storage-${VERSION}"
rm -fr $PKG_DIR
mkdir $PKG_DIR

TMP_DIR_STORAGE=/tmp/.storage
rm -fr $TMP_DIR_STORAGE
mkdir $TMP_DIR_STORAGE

TMP_DIR_PYTHON=/tmp/.python
rm -fr $TMP_DIR_PYTHON
mkdir $TMP_DIR_PYTHON

make clean
make isolated-storage=1 no-disk-prewarn=1
sync_apps
sync_conf
sync_init_script
sync_shared_lib
pkg_isolated_storage
pkg_python

if [ "$KERNEL" = "kernel" ]; then
	pkg_kernel
fi

pkg_all

echo ""
echo -e "\033[0;35;1mPackaged completed successfully.\033[0m"
echo ""
