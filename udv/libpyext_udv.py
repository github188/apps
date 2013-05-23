#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from libmd import get_mdattr_by_mddev
from libmd import get_md_by_name

# -----------------------------------------------------------------------------
def getVGNameByDev(mddev):
	mdattr = None
	try:
		mdattr = get_mdattr_by_mddev(mddev)
	except:
		return 'N/A'
	return mdattr.name

def getVGDevByName(vg_name):
	md = get_md_by_name(vg_name)
	if md != '':
		return '/dev/' + md
	else:
		return ''

# -----------------------------------------------------------------------------

def getMdNameMap(md_dev):
	md_map = {}
	try:
		md_map['dev'] = '/dev/%s' % md_dev
		f = os.popen('mdadm -D %s 2>&1' % md_map['dev'])
		x = f.readlines()
		for y in x:
			a = y.split('           Name : ')
			if a[0] == '' and md_map.keys():
				md_map['name'] = a[1].split(':')[0]
				return md_map
	except:
		pass
	return md_map


def getMdList():
	md_list = []
	try:
		for x in os.listdir('/dev'):
			if len(x) < 3:
				continue
			y = x.split('md')
			if len(y) == 2 and y[0]=='' and len(y[1].split('p'))==1:
				md_attr = getMdNameMap(x)
				if md_attr:
					md_list.append(md_attr)
	except:
		pass
	return md_list

# -----------------------------------------------------------------------------

VDISK_PATH = '/sys/kernel/scst_tgt/handlers/vdisk_blockio'

def getVdiskList():
	vd_list = []
	try:
		for x in os.listdir(VDISK_PATH):
			dev_path = '%s/%s/filename' % (VDISK_PATH, x)
			if os.path.isfile(dev_path) == False:
				continue
			f = open(dev_path)
			dev = f.readline().strip()
			vd_list.append(dev)
			f.close()
	except:
		pass
	return vd_list

def isISCSIVolume(udv_dev):
	try:
		for x in getVdiskList():
			if x == udv_dev:
				return True
	except:
		pass
	return False

if __name__ == '__main__':
	vg_dev = getVGDevByName(sys.argv[1])
	print 'VG: %s' % vg_dev
	sys.exit(0)
	print getVdiskList()
	print isISCSIVolume(sys.argv[1])
