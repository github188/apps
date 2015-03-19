#!/usr/bin/env bash
set -e

sync_apps()
{
	echo "copy all app files ..."

	local disk_bin="us/us_d us/us_cmd us/script/* us/md-auto-resume/md-assemble.sh \
			us/md-auto-resume/mdscan/mdinfo"
	local udv_bin="udv/* nas/libnas.py"
	local webiface_bin="web-iface/sys-manager"
	local sysconf_bin="sys-conf/.build-date sys-conf/libsysinfo.py sys-conf/libsysalarm.py"
	local mon_bin="monitor/libsysmon.py"
	local common_bin="common/*"
	
	# sync list
	local bin_list="$disk_bin $udv_bin $webiface_bin $sysconf_bin $mon_bin $common_bin $web_bin jw-other-start.sh"

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
	
	# raid配置工具mdadm
	mkdir $TMP_DIR_STORAGE/usr/local/sbin
	cp /tmp/mdadm $TMP_DIR_STORAGE/usr/local/sbin
}

sync_conf()
{
	echo "copy conf ..."

	local tmp_dir=$TMP_DIR_STORAGE/opt/jw-conf

	mkdir -p $tmp_dir/disk
	cp -fa us/ata2slot.xml.TDWY-3U16 $tmp_dir/disk/ata2slot.xml
}

sync_tools()
{
	echo "copy tools ..."
	local tools="parted"
	local tmp_dir=$TMP_DIR_STORAGE/usr/local/bin
	mkdir -p $tmp_dir

	cd $ARM_HISI_BIN_DIR
	cp -fa $tools $tmp_dir/
	cd - >/dev/null
}

sync_shared_lib()
{
	echo "copy shared library ..."
	
	local shared_lib="libatasmart.so* libdevmapper.so* libev.so* libintl.so* libjson.so* libparted.so* libreadline.so* libsqlite3.so* libudev.so* libuuid.so* libxml2.so* libz.so*"
	local tmp_dir=$TMP_DIR_STORAGE/usr/local/lib
	mkdir -p $tmp_dir
	
	cd $ARM_HISI_LIB_DIR
	cp -fa $shared_lib $tmp_dir/
	cd - >/dev/null
}

pkg_isolated_storage()
{
	echo "packaging isolated storage ..."

	local pkg_dir=$PKG_DIR/usr
	mkdir -p $pkg_dir
	cp install-jw-storage-other.sh $pkg_dir/
	chmod +x $pkg_dir/install-jw-storage-*.sh

	cd "$TMP_DIR_STORAGE"
	chown -fR root:root ./*
	
	tar jcf $pkg_dir/$PKG_STORAGE ./*
	cd - >/dev/null
	rm -rf $TMP_DIR_STORAGE
}

pkg_python()
{
	echo "packaging python2.6 ..."
	
	local pkg_dir=$PKG_DIR/usr/
	mkdir -p $pkg_dir

	local python_bin="$ARM_HISI_LIB_DIR/../bin/python2.6"
	local python_lib="$ARM_HISI_LIB_DIR/python2.6"

	mkdir -p $TMP_DIR_PYTHON/usr/local/bin
	mkdir -p $TMP_DIR_PYTHON/usr/local/lib
	cd $TMP_DIR_PYTHON/usr/local/
	
	cp -fa $python_bin ./bin/
	cp -fa $python_lib ./lib/
	rm -rf ./lib/python2.6/lib-dynload
	rm -f ./lib/python2.6/config/*.o
	rm -f ./lib/python2.6/config/*.a
	find ./lib/python2.6/ -name test | xargs rm -rf
	find ./lib/python2.6/ -name tests | xargs rm -rf
	cd - >/dev/null

	cd $TMP_DIR_PYTHON
	tar jcf $pkg_dir/$PKG_PYTHON ./*
	cd - >/dev/null
	rm -rf $TMP_DIR_PYTHON
}

pkg_kernel()
{
	local pkg_dir=$PKG_DIR/kernel
	mkdir -p $pkg_dir
	
	local pkg_kernel=`ls /tmp/uImage 2>/dev/null`
	if [ "$pkg_kernel" = "" ]; then
		echo -e "\033[0;31;1mNot found jw kernel package in /tmp dir.\033[0m"
		exit 1
	fi
	
	local val
	file $pkg_kernel
	read -p "Confirm kernel package: \"$pkg_kernel\" [y/n]: " val
	if [ "$val" != "y" ]; then
		exit 1
	fi
	cp $pkg_kernel $pkg_dir/
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

if [ "`git status -s`" != "" ]; then
	git status -s
	read -p "Continue?[y/n]: " val
	if [ "$val" != "y" ]; then
		exit
	fi
fi

ARCH="arm_hisi"

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

if [ ! -x /tmp/mdadm ]; then
	echo -e "\033[0;31;1m/tmp/mdadm dose not exist or is not executable.\033[0m"
	exit 1
fi

ARM_HISI_LIB_DIR=`arm-hisiv100nptl-linux-gcc --print-file-name libc.a`
ARM_HISI_LIB_DIR=`dirname $ARM_HISI_LIB_DIR`
ARM_HISI_BIN_DIR=`dirname $ARM_HISI_LIB_DIR`/bin

make clean other-hardware=1 isolated-storage=1 no-disk-prewarn=1
make CROSS_COMPILE=arm-hisiv100nptl-linux- isolated-storage=1 no-disk-prewarn=1 other-hardware=1
sync_apps
sync_conf
sync_tools
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
