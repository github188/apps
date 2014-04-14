#!/usr/bin/env bash
set -e

if [ "$LOGNAME" != "root" ]; then
	echo -e "\033[0;31;1mNeed root Permission.\033[0m"
	exit 1
fi

# filename: jw-kernel-ubuntu-12.04-3.2.42-64bit.tar.bz2

if arch | grep -q "64"; then
	ARCH="64bit"
else
	ARCH="32bit"
fi

# check OS version and arch
LINUX_DIST_ID=`lsb_release -si | tr "[:upper:]" "[:lower:]"`
LINUX_DIST_RELEASE=`lsb_release -sr`

kernel_pkg=`ls jw-kernel-${LINUX_DIST_ID}-${LINUX_DIST_RELEASE}-*-${ARCH}.tar.bz2 2>/dev/null`
if [ "$kernel_pkg" = "" ]; then
	echo -e "\033[0;31;1mThis package not support ${LINUX_DIST_ID} ${LINUX_DIST_RELEASE} ${ARCH}\033[0m"
	exit 1
fi

echo -e "\033[0;35;1mInstall kernel: $kernel_pkg ...\033[0m"
kernel_pkg_path=`pwd`/$kernel_pkg
cd /
tar xfj $kernel_pkg_path
cd - >/dev/null

echo -e "\033[0;35;1mConfig grub ...\033[0m"
jw_kernel_version=`echo $kernel_pkg | awk -F '-' '{ print $5 }'`
echo -e "\033[0;35;1mAdd jw kernel to grub ...\033[0m"
update-grub
grub_default=`grep "${jw_kernel_version}-jwstor'" /boot/grub/grub.cfg | grep menuentry | head -n 1 | awk -F \' '{ print $2 }'`
cp /etc/default/grub /etc/default/grub.bak
echo -e "\033[0;35;1mOriginal /etc/default/grub backup to /etc/default/grub.bak\033[0m"
echo -e "\033[0;35;1mset /etc/default/grub default boot the jw kernel\033[0m"
sed -i '/GRUB_DEFAULT/d' /etc/default/grub
if grep "menuentry" /boot/grub/grub.cfg | head -n 1 | grep -q "${jw_kernel_version}\-jwstor"; then
	echo "GRUB_DEFAULT=\"$grub_default\"" >> /etc/default/grub
elif grep -q "Previous Linux versions" /boot/grub/grub.cfg; then
	echo "GRUB_DEFAULT=\"Previous Linux versions>$grub_default\"" >> /etc/default/grub
else
	echo "GRUB_DEFAULT=\"$grub_default\"" >> /etc/default/grub
fi
update-grub

echo ""
echo -e "\033[0;35;1mjw kernel install OK, grub default boot the jw kernel. Please reboot.\033[0m"
echo ""
