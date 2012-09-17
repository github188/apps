#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('/usr/local/bin')

from libmd import md_info

def getVGDevByName(vg_name):
	md_dev = ''
	try:
		mdinfo = md_info()
		if mdinfo['total'] > 0:
			for md in mdinfo['rows']:
				if md['name'] == vg_name:
					md_dev = md['dev']
					break
	except:
		pass
	finally:
		return md_dev

if __name__ == '__main__':
	vg_dev = getVGDevByName('slash-server')
	print 'VG: slash-server, DEV: ', vg_dev
