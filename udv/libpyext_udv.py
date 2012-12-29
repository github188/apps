#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from libmd import md_info
from libdisk import md_get_mddev

# -----------------------------------------------------------------------------
"""
def getVGNameByDev(md_dev):
	x = None
	try:
		x = md_info(md_dev)['rows'][0]
	except:
		return 'N/A'
	return x['name']
"""

def getVGDevByName(vg_name):
	mddev = md_get_mddev(vg_name)
	return mddev if mddev != None else ''

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
	print isISCSIVolume(sys.argv[1])
	sys.exit(0)
	vg_dev = getVGDevByName(sys.argv[1])
	print 'VG: slash-server, DEV: ', vg_dev

	print getVdiskList()
	print isISCSIVolume(sys.argv[1])
