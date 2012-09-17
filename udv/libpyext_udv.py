#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

def getMdNameMap(md_dev):
	md_map = {}
	try:
		md_map['dev'] = '/dev/%s' % md_dev
		f = os.popen('mdadm -D %s' % md_map['dev'])
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
			y = x.split('md')
			if len(y) == 2 and y[0]=='' and len(y[1].split('p'))==1:
				md_attr = getMdNameMap(x)
				if md_attr:
					md_list.append(md_attr)
	except:
		pass
	return md_list

def getVGDevByName(vg_name):
	md_dev = ''
	try:
		md_list = getMdList()
		for x in md_list:
			if x['name'] == vg_name:
				md_dev = x['dev']
	except:
		pass
	finally:
		return md_dev

if __name__ == '__main__':
	vg_dev = getVGDevByName(sys.argv[1])
	print 'VG: slash-server, DEV: ', vg_dev
