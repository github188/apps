#!/usr/bin/env bash

. /usr/local/lib/jw-functions

PKG_STORE_DIR=/home
USER_CONF_DIR=/opt/etc

conf_backup()
{
	rm -rf conf_bak
	mkdir conf_bak
	cp /opt/* conf_bak/ -a

	mv /root/.ssh conf_bak
	
	HOSTNAME=`hostname`
}

conf_restore()
{
	mv -f conf_bak/.ssh /root

	cp conf_bak/* /opt/ -a
	rm -rf conf_bak
}

service_stop()
{
	/etc/init.d/lighttpd stop
	/etc/init.d/jw-iscsi stop
	/etc/init.d/samba stop
	/etc/init.d/jw-us stop
	/etc/init.d/jw-sysmon stop
	/etc/init.d/jw-log stop
}

service_start()
{
	echo -e "\n\n--- Please reboot system! ---\n"
}

make_default_conf()
{
	# nfs
	cat /dev/null > /etc/exports

	# disk iscsi nas
	rm -rf $USER_CONF_DIR/disk
	rm -rf $USER_CONF_DIR/iscsi
	rm -rf $USER_CONF_DIR/nas
	rm -rf $USER_CONF_DIR/system
	rm -rf /mnt/*
	
	# defualt hostname
	sysconfig --hosts JW-Linux
	web --default
	usermanage --default
	nasconf --default
	adminmanage --default
	
	if [ `system_type` -eq $SYSTYPE_BASIC_PLATFORM ]; then
    	echo -e "123456\n123456" | passwd root
	fi

	# clear log
	find /var/log/ -type f -exec rm -f {} \;
	mkdir -pv /opt/log
	rm -f /opt/log/jw-log.db
	
	rm -f /opt/etc/fingerprint
}

pkg_root_preprocess()
{
	# be sure /etc/sudoers has right privilege
	chown root:root /etc/sudoers
	chmod 440 /etc/sudoers
	
	rm -f /etc/udev/rules.d/70-persistent-net.rules

	upload_dir=/var/www/Upload
	[ ! -d $upload_dir ] && mkdir $upload_dir
	chmod a+w $upload_dir
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
	
	rm -rf usr/local/*
	mkdir usr/local/bin
	mkdir usr/local/sbin
	cp /usr/local/bin/sys-manager usr/local/bin
	cp /usr/local/bin/libcommon.pyc usr/local/bin
	cp /usr/local/bin/*adminmanage* usr/local/bin
	cp /usr/local/bin/*network* usr/local/bin
	cp /usr/local/bin/license usr/local/bin
	cp /usr/local/sbin/apply_license usr/local/sbin
	cp /usr/local/sbin/generate_uuid usr/local/sbin
	cp /usr/local/sbin/import_license usr/local/sbin
	cp /usr/local/sbin/license_client usr/local/sbin

	cat << EOF > bin/set_network_default
#!/bin/sh
network --default
EOF
	chmod +x bin/set_network_default
	
	mv -f boot/grub/.grub.bak* /tmp

	tar zcf $PKG_STORE_DIR/root.tgz ./
	
	rm bin/set_network_default
	mv /tmp/.grub.bak* boot/grub/

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

	cat << EOF > ./bin/set_misc_default
#!/bin/sh
upload_dir=/var/www/Upload
[ ! -d \$upload_dir ] && mkdir \$upload_dir
chmod a+w \$upload_dir
EOF
	chmod +x ./bin/set_misc_default

	tar zcf /tmp/local.tgz ./
	rm -f ./bin/set_misc_default
	openssl enc -aes256 -salt -a -pass file:/sys/kernel/vendor -in /tmp/local.tgz -out ./local.bin >/dev/null 2>&1
	if [ $? -ne 0 ]; then
		echo "encode local pkg failed."
		exit 1
	fi

	tar zcf $PKG_STORE_DIR/local.tgz ./local.bin
	rm -f ./local.bin /tmp/local.tgz
	cd -
	echo "local.tgz packaged OK!"
}

if [ -z $1 ]; then
	echo "input release version"
	exit 1
fi

echo -n "Confirm system info: "
cat /sys/kernel/vendor
echo ""
echo -n "input \"yes\" confirm: "
read input
if [ "x$input" != "xyes" ]; then
	exit 0
fi

echo "JW-Linux GNU/Linux $1 \n \l" >/etc/issue

cd $PKG_STORE_DIR
rm -rf root.tgz local.tgz opt.tgz
service_stop
conf_backup
make_default_conf
pkg_root
pkg_local
pkg_opt
conf_restore
service_start
