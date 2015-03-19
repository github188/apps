#!/usr/bin/env sh
set -e

if [ "$LOGNAME" != "root" ]; then
	echo -e "\033[0;31;1mNeed root Permission.\033[0m"
	exit 1
fi

storage_pkg=`ls jw-storage-*.tar.bz2 2>/dev/null`
if [ "$storage_pkg" = "" ]; then
	echo -e "\033[0;31;1mNot found jw-storage package, please check OS platform.\033[0m"
	exit 1
fi

python_pkg=`ls python2.6-*.tar.bz2 2>/dev/null`

PKG_DIR=`pwd`

echo "Install package: $storage_pkg ..."
cd /
bzip2 -c -d $PKG_DIR/jw-storage-*.tar.bz2 | tar xf -

if [ "$python_pkg" != "" ]; then
	echo "Install package: $python_pkg ..."
	bzip2 -c -d $PKG_DIR/python2.6-*.tar.bz2 | tar xf -
fi
cd - >/dev/null

source /etc/profile >/dev/null
if ! echo $PATH | grep -q '/usr/local/bin'; then
	echo 'export PATH=/usr/local/bin:$PATH' >>/etc/profile
fi

if ! echo $PATH | grep -q '/usr/local/sbin'; then
	echo 'export PATH=/usr/local/sbin:$PATH' >>/etc/profile
fi

if ! echo $LD_LIBRARY_PATH | grep -q '/usr/local/lib'; then
	echo 'export LD_LIBRARY_PATH=/usr/local/lib:$/usr/local/lib' >>/etc/profile
fi

if ! echo $PYTHONHOME | grep -q '/usr/local/lib/python2.6'; then
	echo 'export PYTHONHOME=/usr/local/lib/python2.6' >>/etc/profile
	echo 'export PYTHONPATH=.:$PYTHONHOME:$PYTHONHOME/site-packages' >>/etc/profile
fi

echo ""
echo -e "\033[0;35;1mPackge install OK, please reboot.\033[0m"
echo ""
