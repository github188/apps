#!/usr/bin/env bash

update_sys_version()
{
	build_date=$(date)
	sed "s/return 'Build Date:'/return 'Build Date: $build_date'/" sys-conf/libsysinfo.py > sys-conf/libsysinfo.py.tmp
	mv sys-conf/libsysinfo.py.tmp sys-conf/libsysinfo.py
}

update_sys_version
