#!/usr/bin/env bash

PKG_STORE_DIR=/home
USER_CONF_DIR=/opt/etc

conf_backup()
{
	rm -rf conf_bak
	mkdir conf_bak
	cp /opt/* conf_bak/ -a

	mv /root/.ssh conf_bak
	mv -f /boot/grub/.grub.bak* conf_bak
	
	HOSTNAME=`hostname`
}

conf_restore()
{
	mv -f conf_bak/.ssh /root
	mv -f conf_bak/.grub.bak* /boot/grub

	cp conf_bak/* /opt/ -a
	rm -rf conf_bak
	
	sysconfig --hosts $HOSTNAME
}

service_stop()
{
	/etc/init.d/lighttpd stop
	/etc/init.d/jw-iscsi stop
	/etc/init.d/jw-apps stop
}

service_start()
{
	/etc/init.d/rsyslog restart
	/etc/init.d/jw-apps start
	/etc/init.d/jw-iscsi start
	/etc/init.d/lighttpd start
}

make_default_conf()
{
	# nfs
	cat /dev/null > /etc/exports

	# disk iscsi nas
	rm -rf $USER_CONF_DIR/disk
	rm -rf $USER_CONF_DIR/iscsi
	rm -rf $USER_CONF_DIR/nas
	
	# defualt hostname
	sysconfig --hosts JW-Linux

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

	cat << EOF > ./bin/set_network_default
#!/bin/sh
network --default
EOF
	chmod +x ./bin/set_network_default
	cat ./bin/set_network_default

	cat << EOF > ./bin/set_misc_default
#!/bin/sh
PATH=/usr/local/bin:$PATH

upload_dir=/var/www/Upload
[ ! -d \$upload_dir ] && mkdir \$upload_dir
chmod a+w $upload_dir

usermanage --default
nasconf --default
web --default
EOF
	chmod +x ./bin/set_misc_default
	cat ./bin/set_misc_default

	tar zcf $PKG_STORE_DIR/local.tgz ./
	rm -f ./bin/set_network_default
	rm -f ./bin/set_misc_default
	cd -
	echo "local.tgz packaged OK!"
}

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
