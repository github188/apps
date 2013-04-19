#!/usr/bin/env bash

PKG_STORE_DIR=/home
JW_CONF_DIR=/opt/jw-conf

conf_backup()
{
	rm -rf conf_bak
	mkdir conf_bak
	cp /opt/* conf_bak/ -a
}

conf_restore()
{
	cp conf_bak/* /opt/ -a
	rm -rf conf_bak
}

make_default_conf()
{
	# nfs
	cat /dev/null > /etc/exports

	# jw
	mkdir -pv $JW_CONF_DIR/{disk,iscsi,nas,system}
	cat /dev/null > "$JW_CONF_DIR"/nas/self-load.sh
	chmod +x "$JW_CONF_DIR"/nas/self-load.sh

	# net
	network --default

	# clear log
	find /var/log/ -type f -exec rm -f {} \;
	mkdir -pv /opt/log
	rm -f /opt/log/jw-log.db
}

pkg_root_preprocess()
{
	# be sure /etc/sudoers has right privilege
	chown root:root /etc/sudoers
	chmod 440 /etc/sudoers
	
	rm -f /etc/udev/rules.d/70-persistent-net.rules
}

pkg_root()
{
	pkg_root_preprocess

	# check if mounted /
	echo "Checking rootfs mounted..."
	mount | grep $PKG_STORE_DIR\/sda1 > /dev/null
	if [ $? -ne 0 ]; then
		echo "rootfs not mount! mounting now ...."
		mkdir -p $PKG_STORE_DIR/sda1
		mount /dev/sda1 $PKG_STORE_DIR/sda1
	fi

	# check again
	mount | grep $PKG_STORE_DIR\/sda1 > /dev/null
	[ $? -ne 0 ] && echo "rootfs not mounted!" && exit -1
	
	echo "mount rootfs OK! package start ..."
	cd $PKG_STORE_DIR/sda1
	tar zcf $PKG_STORE_DIR/root.tgz ./
	cd $PKG_STORE_DIR
	umount sda1 && rm -rf sda1
	echo "root.tgz packaged OK!"
}

pkg_opt()
{
	echo "opt.tgz package start ..."
	cd /opt
	tar zcf $PKG_STORE_DIR/opt.tgz ./
	cd -
	echo "opt.tgz packaged OK!"
}

pkg_local()
{
	echo "local.tgz package start ..."
	cd /usr/local
	tar zcf $PKG_STORE_DIR/local.tgz ./
	cd -
	echo "local.tgz packaged OK!"
}

cd $PKG_STORE_DIR
rm -rf root.tgz local.tgz opt.tgz
conf_backup
make_default_conf
pkg_root
pkg_local
pkg_opt
conf_restore
