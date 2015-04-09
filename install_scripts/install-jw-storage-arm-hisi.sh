#!/usr/bin/env sh
set -e

if [ "$LOGNAME" != "root" ]; then
	echo -e "\033[0;31;1mNeed root Permission.\033[0m"
	exit 1
fi

storage_pkg=`ls usr/jw-storage-*.tar.bz2 2>/dev/null`
if [ "$storage_pkg" = "" ]; then
	echo -e "\033[0;31;1mNot found jw-storage package, please check OS platform.\033[0m"
	exit 1
fi

python_pkg=`ls usr/python2.6-*.tar.bz2 2>/dev/null`

PKG_DIR=`pwd`

echo "Install package: $storage_pkg ..."
cd /
bzip2 -c -d $PKG_DIR/$storage_pkg | tar xf -

while true
do
        echo ""
        echo "Please choose hardware type"
        echo " 1 TDWY-2U8"
        echo " 2 TDWY-JW-2U8"
        echo " 3 TDWY-JW-3U16"
        read -p "Enter the hardware number: " hw_no
        if [ "x$hw_no" = "x1" -o "x$hw_no" = "x2" -o "x$hw_no" = "x3" ]; then
                break
        fi
done

cd /opt/jw-conf/disk
if [ "x$hw_no" = "x1" ]; then
	ln -sfn ata2slot.xml.TDWY-2U8 ata2slot.xml
elif [ "x$hw_no" = "x2" ]; then
	ln -sfn ata2slot.xml.TDWY-JW-2U8 ata2slot.xml
elif [ "x$hw_no" = "x3" ]; then
	ln -sfn ata2slot.xml.TDWY-JW-3U16 ata2slot.xml
fi
cd $PKG_DIR

if [ "$python_pkg" != "" ]; then
	cd /
	echo "Install package: $python_pkg ..."
	bzip2 -c -d $PKG_DIR/$python_pkg | tar xf -
	cd $PKG_DIR
fi

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

if [ -d "kernel/modules" ]; then
	echo "Install kernel modules ..."
	cp -fa kernel/modules /usr/local
fi

echo ""
echo -e "\033[0;35;1mPackge install OK.\033[0m"
echo -e "\033[0;35;1mPlease reboot, and then run script: jw-arm-hisi-start.sh startup raid management system.\033[0m"
echo ""
