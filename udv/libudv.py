#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys

from libmd import *

reload(sys)
sys.setdefaultencoding('utf-8')
	
def get_dev_byudvname(udv_name):
	part_dev = ''
	for md in md_list():
		sysdir_md = '/sys/block/' + md
		for entry in list_child_dir(sysdir_md):
			if entry[:len(md)] != md:
				continue
			
			sysdir_part = sysdir_md + os.sep + entry
			if fs_attr_read(sysdir_part + '/volname') == udv_name:
				part_dev = '/dev/' + entry
				break
		if part_dev != '':
			break
	
	return part_dev

def get_vgname_bydev(part_dev):
	part = basename(part_dev)
	try:
		md = part[:part.index('p')]
	except:
		return ''
	return fs_attr_read('/sys/block/' + md + os.sep + 'md/array_name')
	
def get_udvname_bydev(part_dev):
	part = basename(part_dev)
	try:
		md = part[:part.index('p')]
	except:
		return ''
	return fs_attr_read('/sys/block/' + md + os.sep + part + '/volname')

def get_iscsivolname_bydev(part_dev):
	part = basename(part_dev)
	try:
		md = part[:part.index('p')]
	except:
		return ''
	return fs_attr_read('/sys/block/' + md + os.sep + part + '/iscsi_volname')

def set_iscsivolname_fordev(part_dev, iscsi_volname):
	part = basename(part_dev)
	try:
		md = part[:part.index('p')]
	except:
		return
	fs_attr_write('/sys/block/' + md + os.sep + part + '/iscsi_volname', iscsi_volname)

def clean_iscsivolname_fordev(part_dev):
	part = basename(part_dev)
	try:
		md = part[:part.index('p')]
	except:
		return
	fs_attr_write('/sys/block/' + md + os.sep + part + '/iscsi_volname', '--clean')

if __name__ == "__main__":
	sys.exit(0)
