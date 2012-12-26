#!/usr/bin/env sh

JW_CONF_DIR="/opt/jw-conf"

make_default_conf()
{
	# nfs
	cat /dev/null > /etc/exports

	# jw
	mkdir -pv "$JW_CONF_DIR"/{disk,iscsi,nas,system}
	cat /dev/null > "$JW_CONF_DIR"/nas/self-load.sh
	chmod +x "$JW_CONF_DIR"/nas/self-load.sh

	# clear log
	find /var/log/ -type f | xargs -x rm
	mkdir -pv /opt/log
	rm -f /opt/log/jw-log.db
}

pkg_root_preprocess()
{
	# be sure /etc/sudoers has right privilege
	chown root:root /etc/sudoers
	chmod 440 /etc/sudoers
}

pkg_root()
{
	pkg_root_preprocess

	# check if mounted /
	echo "Checking rootfs mounted..."
	mount | grep \/media\/sda1 > /dev/null
	if [ $? -ne 0 ]; then
		echo "rootfs not mount! mounting now ...."
		mkdir -p /media/sda1
		mount /dev/sda1 /media/sda1
	fi

	# check again
	mount | grep \/media\/sda1 > /dev/null
	[ $? -ne 0 ] && echo "rootfs not mounted!" && exit -1
	
	echo "mount rootfs OK! package start ..."
	rm -f /media/root.tgz
	cd /media/sda1
	tar zcf ../root.tgz ./*
	cd -
	echo "root.tgz packaged OK!"
}

pkg_opt()
{
	echo "opt.tgz package start ..."
	cd /opt/
	tar zcf /media/opt.tgz ./*
	cd -
	echo "opt.tgz packaged OK!"
}

pkg_local()
{
	echo "local.tgz package start ..."
	cd /usr/local/
	tar zcf /media/local.tgz ./*
	cd -
	echo "local.tgz packaged OK!"
}

make_default_conf
pkg_root
pkg_local
pkg_opt

