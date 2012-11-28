#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import time
from libsyscommon import *

ERROR_VALUE = 'error-occurs'
VER_SEP = '.'

def __get_cpu_info(mod):
	_item = {}
	_item['item'] = mod
	try:
		_item['value'] = re.findall('model name\t: (.*)', get_sys_file('/proc/cpuinfo'))[0]
	except:
		_item['value'] = ERROR_VALUE
	return _item

def __get_cpu_util(mod):
	_item = {}
	_item['item'] = mod
	try:
		_cpu_stat = re.findall('cpu (.*)', get_sys_file('/proc/stat'))[0].split()
		_user = int(_cpu_stat[0])
		_nice = int(_cpu_stat[1])
		_system = int(_cpu_stat[2])
		_idle = int(_cpu_stat[3])
		_irq = int(_cpu_stat[5])
		_cpu_ratio = 100 * (_user + _nice + _system) / (_user + _nice + _system + _idle)
		_item['value'] = '%d%%' % _cpu_ratio
	except:
		_item['value'] = ERROR_VALUE
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
	try:
		mem_info = get_sys_file('/proc/meminfo')
		mem_total = float(re.findall('MemTotal: (.*) kB', mem_info)[0])
		mem_free = float(re.findall('MemFree: (.*) kB', mem_info)[0])
		mem_used = mem_total - mem_free
		_item['value'] = '%.2f%%' % (mem_used/mem_total*100)
	except:
		_item['value'] = ERROR_VALUE
	return _item

def __get_runtime(mod):
	_item = {}
	_item['item'] = mod
	try:
		run_secs = int(float(re.findall('(.*) ', get_sys_file('/proc/uptime'))[0]))
		_run_days = int(run_secs / 86400)
		_run_hours = int((run_secs - _run_days*86400) / 3600)
		_run_mins = int((run_secs - _run_days*86400 - _run_hours*3600) / 60)
		_run_secs = int(run_secs - _run_days*86400 - _run_hours*3600 - _run_mins*60)
		_item['value'] = ''
		if _run_days != 0:
			_item['value'] = _item['value'] + '%d天' % _run_days
		if _run_hours != 0:
			_item['value'] = _item['value'] + '%d小时' % _run_hours
		if _run_mins != 0:
			_item['value'] = _item['value'] + '%d分钟' % _run_mins
		if _run_secs != 0:
			_item['value'] = _item['value'] + '%d秒' % _run_secs
	except:
		_item['value'] = ERROR_VALUE
	return _item

def __get_lastrun(mod):
	_item = {}
	_item['item'] = mod
	try:
		run_secs = float(re.findall('(.*) ', get_sys_file('/proc/uptime'))[0])
		_item['value'] = time.ctime(time.time() - run_secs)
	except:
		_item['value'] = ERROR_VALUE
	return _item

# 主板硬件版本
def __mab_ver():
	return 'Rev1.0'

# 背板硬件版本
def __bkp_ver():
	return '01'

# 单片机版本
def __mcu_ver():
	return '0.9'

# 内核版本
def __kernel_ver():
	return '3.04'

# rootfs版本
def __rootfs_ver():
	return '1.0'

# 存储软件版本
def __apps_ver():
	return '0.91'

# web版本
def __web_ver():
	return '1.0'

# 附加版本
def __attch_ver():
	return '0'

# 编译日期
def __build_date():
	return 'Build Date: 2012-11-28 15:25'

def __get_sys_version():
	return __mab_ver() + VER_SEP + __bkp_ver() + VER_SEP + __mcu_ver() + VER_SEP + __kernel_ver() + VER_SEP + __rootfs_ver() + VER_SEP + __apps_ver() + VER_SEP + __web_ver() + VER_SEP + __attch_ver() + '  ' + __build_date()

def __get_version(mod):
	_item = {}
	_item['item'] = mod
	_item['value'] = __get_sys_version()
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
	_stat['value'] = ''

	# 通过外部命令获取状态
	try:
		_disk_list = json.loads(commands.getoutput('sys-manager disk --list'))
		for _disk in _disk_list['rows']:
			if _disk['state'] == 'Fail':
				_stat['value'] = _stat['value'] + '槽位号%s的磁盘故障 ' % _disk['slot']
	except:
		pass
	if _stat['value'] == '':
		_stat['value'] = 'good'
	return _stat

def __get_stat_vg(mod):
	_stat = {}
	_stat['item'] = mod
	_stat['value'] = 'good'

	# 通过外部命令获取
	try:
		_vg_list = json.loads(commands.getoutput('sys-manager vg --list'))
		for _vg in _vg_list['rows']:
			if _vg['state'] == 'fail':
				_stat['value'] = _stat['value'] + '卷组%s失效 ' % _vg['name']
			if _vg['state'] == 'degrade':
				_stat['value'] = _stat['value'] + '卷组%s降级 ' % _vg['name']
	except:
		pass
	if _stat['value'] == '':
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
	#print json.dumps(sys_global(get_sys_stat('disk')))
	#print json.dumps(sys_global(get_sys_stat()))
	#print __get_cpu_info('cpu-info')
	#print __get_mem_util('mem-util')
	#print __get_version('version')
	#print __get_lastrun('last-run')
	#print __get_runtime('runtime')
	#print __get_cpu_util('cpu-util')
	#print __get_stat_disk('disk')
	print __get_stat_vg('vg')
