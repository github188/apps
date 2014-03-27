#!/usr/bin/env bash
set -e

# check OS version
LINUX_DISTRO=`lsb_release -si`

if [ "$LINUX_DISTRO" != "Debian" -a "$LINUX_DISTRO" != "Ubuntu" ];	then
	echo "Not support OS $LINUX_DISTRO"
	exit 1
fi

# check kernel version
JW_FLAG=`uname -r | awk -F '-' '{ print $NF }'`
if [ "$JW_FLAG" != "jwstor" ]; then
	echo "Kernel version not match."
	echo "Please install jwstor kernel, and reboot system, boot the jwstor kernel."
	exit 1
fi

# check OS platform
if arch | grep -q "64"; then
	ARCH="64bit"
else
	ARCH="32bit"
fi

storage_pkg=`ls jw-storage-*-${ARCH}.tar.bz2 2>/dev/null`
if [ "$storage_pkg" = "" ]; then
	echo "Not found $ARCH jw-storage package, please check OS platform."
	exit 1
fi

# check package
DPKG_FILE=/tmp/dpkg
dpkg -l >/tmp/dpkg
pkgs="libatasmart4 libsqlite3 libudev0 libxml2 libjson0"
not_installed_pkgs=""
for pkg in $pkgs
do
	if ! grep -q $pkg $DPKG_FILE; then
		not_installed_pkgs="$not_installed_pkgs $pkg"
	fi
done

if [ "$not_installed_pkgs" != "" ]; then
	echo Packages: "$not_installed_pkgs" are not installed.
	echo Please install them via "apt-get install <package>", then restart this installation script.
	exit 1
fi

PKG_DIR=`pwd`

which python2.6 >/dev/null
if [ $? -ne 0 ]; then
	echo "Install python2.6 ..."
	if ls python2.6-${ARCH}.tar.bz2 2>/dev/null; then
		echo "Not found package python2.6-${ARCH}.tar.bz2"
		exit 1
	fi
	python_tmp=/tmp/.python2.6
	rm -rf $python_tmp
	mkdir $python_tmp
	cd $python_tmp
	tar xfj $PKG_DIR/python2.6-${ARCH}.tar.bz2
	cp -fa * /
	cd $PKG_DIR
	rm -rf $python_tmp
fi

pkg_tmp=/tmp/.pkg
rm -rf $pkg_tmp
mkdir $pkg_tmp
cd $pkg_tmp
tar xfj $PKG_DIR/jw-storage-*-${ARCH}.tar.bz2
cp -fa * /
cd $PKG_DIR
rm -rf $pkg_tmp

# generate config file
while true
do
	echo ""
	echo "Please choose hardware type"
	echo " 1 3U16-STANDARD"
	echo " 2 3U16-SIMPLE"
	echo " 3 2U8-STANDARD"
	echo " 4 2U8-ATOM"
	read -p	"Enter the hardware number: " hw_no
	if [ "x$hw_no" = "x1" -o "x$hw_no" = "x2" -o "x$hw_no" = "x3" -o \
			"x$hw_no" =	"x4" ];	then
		break
	fi
done

if [ "x$hw_no" = "x1" ]; then
	hw_type="3U16-STANDARD"
elif [ "x$hw_no" = "x2"	]; then
	hw_type="3U16-SIMPLE"
elif [ "x$hw_no" = "x3"	]; then
	hw_type="2U8-STANDARD"
elif [ "x$hw_no" = "x4"	]; then
	hw_type="2U8-ATOM"
fi

cd /opt/jw-conf/system
echo "BASIC-PLATFORM" >./software-type
echo "$hw_type" >./hardware-type
ln -sfn sysmon-conf.xml.$hw_type sysmon-conf.xml

cd /opt/jw-conf/disk
ln -sfn ata2slot.xml.$hw_type ata2slot.xml

cd $PKG_DIR

echo "Packge install OK, please reboot."