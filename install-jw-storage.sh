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
echo "Check shared lib ..."
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

# check python2.6
echo "Check python2.6 ..."
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

echo "Install package: $storage_pkg ..."
pkg_tmp=/tmp/.pkg
rm -rf $pkg_tmp
mkdir $pkg_tmp
cd $pkg_tmp
tar xfj $PKG_DIR/$storage_pkg
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

echo "Store config file ..."
cd /opt/jw-conf/system
echo "BASIC-PLATFORM" >./software-type
echo "$hw_type" >./hardware-type
ln -sfn sysmon-conf.xml.$hw_type sysmon-conf.xml

cd /opt/jw-conf/disk
ln -sfn ata2slot.xml.$hw_type ata2slot.xml

# config init.d script
echo "Config init.d script ..."
cd /etc/init.d
update-rc.d -f jw-driver remove >/dev/null 2>&1
update-rc.d -f jw-log remove >/dev/null 2>&1
update-rc.d -f jw-led remove >/dev/null 2>&1
update-rc.d -f jw-buzzer remove >/dev/null 2>&1
update-rc.d -f jw-sysmon remove >/dev/null 2>&1
update-rc.d -f jw-us remove >/dev/null 2>&1
update-rc.d -f jw-md remove >/dev/null 2>&1

update-rc.d jw-driver defaults 01 20 >/dev/null 2>&1
update-rc.d jw-log defaults 01 20 >/dev/null 2>&1
update-rc.d jw-led defaults 01 20 >/dev/null 2>&1
update-rc.d jw-buzzer defaults 01 20 >/dev/null 2>&1
update-rc.d jw-sysmon defaults 02 19 >/dev/null 2>&1
update-rc.d jw-us defaults 03 18 >/dev/null 2>&1
update-rc.d jw-md defaults 04 17 >/dev/null 2>&1

cd $PKG_DIR

echo ""
echo -e "\033[0;35;1mPackge install OK, please reboot.\033[0m"
echo ""
