#!/usr/bin/env python
# -*- coding: utf-8 -*-

def sys_global(item_list=[]):
	_global = {}
	_global['rows'] = item_list
	_global['total'] = len(_global['rows'])
	return _global
