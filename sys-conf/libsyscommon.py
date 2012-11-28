#!/usr/bin/env python
# -*- coding: utf-8 -*-

def get_sys_file(filename=None):
	_str = ''
	try:
		f = open(filename, 'r')
		_str = f.read()
		f.close()
	except:
		pass
	return _str

def sys_global(item_list=[]):
	_global = {}
	_global['rows'] = item_list
	_global['total'] = len(_global['rows'])
	return _global
