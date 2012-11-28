#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from libsyscommon import sys_global

def __get_cpu_info(mod):
	_item = {}
	_item['item'] = mod
	_item['value'] = 'cpu-info'
	return _item

def __get_cpu_util(mod):
	_item = {}
	_item['item'] = mod
	return _item

def __get_cpu_temp(mod):
	_item = {}
	_item['item'] = mod
	return _item

def __get_fan_speed(mod):
	_item = {}
	_item['item'] = mod
	return _item

def __get_mem_util(mod):
	_item = {}
	_item['item'] = mod
	return _item

def __get_runtime(mod):
	_item = {}
	_item['item'] = mod
	return _item

def __get_lastrun(mod):
	_item = {}
	_item['item'] = mod
	return _item

def __get_version(mod):
	_item = {}
	_item['item'] = mod
	return _item

_info_list = {'cpu-info':__get_cpu_info,
		'cpu-util': __get_cpu_util,
		'cpu-temp': __get_cpu_temp,
		'fan-speed': __get_fan_speed,
		'mem-util': __get_mem_util,
		'runtime': __get_runtime,
		'last-run': __get_lastrun,
		'version': __get_version}

def get_info_item():
	return str(_info_list.keys())

def get_sys_info(item=None):
	global _info_list
	_info_rows = []
	try:
		for mod,func in _info_list.items():
			if not item:
				_info_rows.append(func(mod))
			elif item == mod:
				_info_rows.append(func(mod))
				break
	except:
		pass
	return _info_rows

#------------------------------------------------------------------------------

"""
获取状态函数返回值约定：
1. 状态正常返回 'good'
2. 状态异常返回异常原因字符串
"""

def __get_stat_disk(mod):
	_stat = {}
	_stat['item'] = mod
	_stat['value'] = 'good'
	return _stat

def __get_stat_vg(mod):
	_stat = {}
	_stat['item'] = mod
	_stat['value'] = 'good'
	return _stat

def __get_stat_power(mod):
	_stat = {}
	_stat['item'] = mod
	_stat['value'] = 'good'
	return _stat

def __get_stat_fan(mod):
	_stat = {}
	_stat['item'] = mod
	_stat['value'] = 'good'
	return _stat

def __get_stat_buzzer(mod):
	_stat = {}
	_stat['item'] = mod
	_stat['value'] = 'good'
	return _stat

_stat_list = {'disk': __get_stat_disk,
		'vg': __get_stat_vg,
		'power': __get_stat_power,
		'fan': __get_stat_fan,
		'buzzer': __get_stat_buzzer}

def get_stat_item():
	return str(_stat_list.keys())

def get_sys_stat(item=None):
	global _stat_list
	_stat_rows = []
	try:
		for mod,func in _stat_list.items():
			if not item:
				_stat_rows.append(func(mod))
			elif item == mod:
				_stat_rows.append(func(mod))
				break
	except:
		pass
	return _stat_rows

if __name__ == '__main__':
	#print json.dumps(sys_global(get_sys_info('cpu-info')))
	#print json.dumps(sys_global(get_sys_info()))
	print json.dumps(sys_global(get_sys_stat('disk')))
	#print json.dumps(sys_global(get_sys_stat()))
