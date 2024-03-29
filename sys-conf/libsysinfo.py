#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import json
import re
import time
import os
import commands

from libcommon import *

ERROR_VALUE = 'error-occurs'
VER_SEP = ':'
NCT_ROOT = '/sys/devices/platform/nct6106.656'
NCT_LINK = '/opt/jw-conf/system'

def __get_cpu_info(mod):
	_item = {}
	_item['item'] = mod
	try:
		_item['value'] = re.findall('model name\t: (.*)', read_file('/proc/cpuinfo'))[0]
	except:
		_item['value'] = ERROR_VALUE
	return _item

CPU_UTIL_DIR = '/var/run/cpu_util'
def __get_cpu_util(mod):
	_item = {}
	_item['item'] = mod

	try:
		_cpu_stat = re.findall('cpu (.*)', read_file('/proc/stat'))[0].split()
		_user = int(_cpu_stat[0])
		_nice = int(_cpu_stat[1])
		_system = int(_cpu_stat[2])
		_idle = int(_cpu_stat[3])
		_iowait = int(_cpu_stat[4])
		_irq = int(_cpu_stat[5])
		_softirq = int(_cpu_stat[6])
		_total = _user + _nice + _system + _idle + _iowait + _irq + _softirq
		
		_last_total = 0
		_last_idle = 0
		if not os.path.isdir(CPU_UTIL_DIR):
			os.mkdir(CPU_UTIL_DIR)
			fs_attr_write(CPU_UTIL_DIR + '/total', '0')
			fs_attr_write(CPU_UTIL_DIR + '/idle', '0')
		else:
			val = fs_attr_read(CPU_UTIL_DIR + '/total')
			if val.isdigit():
				_last_total = int(val)
			val = fs_attr_read(CPU_UTIL_DIR + '/idle')
			if val.isdigit():
				_last_idle = int(val)
			
			fs_attr_write(CPU_UTIL_DIR + '/total', str(_total))
			fs_attr_write(CPU_UTIL_DIR + '/idle', str(_idle))
		
		_cpu_ratio = 100 - 100 * float(_idle - _last_idle) / (_total - _last_total)
		_item['value'] = '%.1f%%' % _cpu_ratio
	except:
		_item['value'] = ERROR_VALUE
	return _item

def __read_value(path, fil):
	content = ''
	try:
		f = open('%s/%s' % (path, fil))
		content = f.readline()
		f.close
	except:
		pass
	return content.strip()

def __get_temp(mod):
	_item = {}
	_item['item'] = mod
	try:
		_item['value'] = ''
		temp = __read_value(NCT_LINK, 'temp_cpu')
		if temp != '':
			_item['value'] = _item['value'] + '[ CPU温度: %d ]' % (int(temp)/1000)
		temp = __read_value(NCT_ROOT, 'temp18_input')
		if temp != '':
			_item['value'] = _item['value'] + ' [ 机箱温度: %d ]' % (int(temp)/1000)
		#temp = __read_value(NCT_ROOT, 'temp20_input')
		#if temp != '':
		#	_item['value'] = _item['value'] + ' [ 环境温度: %d ]' % (int(temp)/1000)
	except:
		_item['value'] = ERROR_VALUE
	return _item

def __get_fan_speed(mod):
	_item = {}
	_item['item'] = mod
	try:
		_item['value'] = ''
		temp = __read_value(NCT_ROOT, 'fan1_input')
		if temp != '' and temp != 'good':
			_item['value'] = _item['value'] + '[ 机箱风扇1: %s RPM ]' % temp
		temp = __read_value(NCT_ROOT, 'fan3_input')
		if temp != '' and temp != 'good':
			_item['value'] = _item['value'] + '  [ 机箱风扇2: %s RPM ]' % temp
		#temp = __read_value(NCT_ROOT, 'fan2_input')
		#if temp != '' and temp != 'good':
		#	_item['value'] = _item['value'] + '  [ CPU风扇: %s RPM ]' % temp
	except:
		_item['value'] = ERROR_VALUE
	return _item

def __calc_mem(mem_kb):
	# check kb
	_tmp1 = mem_kb / 1000
	if _tmp1 < 1.0:
		return '%d KB' % int(round(mem_kb))
	_tmp2 = _tmp1 / 1000
	if _tmp2 < 1.0:
		return '%d MB' % int(round(_tmp1))
	_tmp1 = _tmp2 / 1000
	if _tmp1 < 1.0:
		return '%d GB' % int(round(_tmp2))
	_tmp2 = _tmp1 / 1000
	if _tmp2 < 1.0:
		return '%d TB' % int(round(_tmp1))
	return ''

def __get_mem_util(mod):
	_item = {}
	_item['item'] = mod
	try:
		mem_info = read_file('/proc/meminfo')
		mem_total = float(re.findall('MemTotal: (.*) kB', mem_info)[0])
		mem_free = float(re.findall('MemFree: (.*) kB', mem_info)[0])
		mem_used = mem_total - mem_free
		_item['value'] = '%.2f%%  [ 总内存 %s ]' % (mem_used/mem_total*100, __calc_mem(mem_total))
	except:
		_item['value'] = ERROR_VALUE
	return _item

def __get_runtime(mod):
	_item = {}
	_item['item'] = mod
	try:
		run_secs = int(float(re.findall('(.*) ', read_file('/proc/uptime'))[0]))
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
		run_secs = float(re.findall('(.*) ', read_file('/proc/uptime'))[0])
		_item['value'] = time.ctime(time.time() - run_secs)
	except:
		_item['value'] = ERROR_VALUE
	return _item

# 单片机版本
def __mcu_ver():
	try:
		ret,msg = commands.getstatusoutput('/usr/local/bin/pic-version')
		if 0 == ret:
			return msg
	except:
		pass
	return 'nopic'

# 内核版本
def __kernel_ver():
	import platform
	return platform.uname()[2] + '-' + platform.machine()

# rootfs版本
def __rootfs_ver():
	return '1.0'

# 存储软件版本
def __apps_ver():
	try:
		ret,msg = commands.getstatusoutput('sys-manager version')
		if 0 == ret:
			return msg.split(':')[1].strip()
	except:
		pass
	return 'apps'

# web版本
def __web_ver():
	try:
		ret,msg = commands.getstatusoutput('cat /var/www/version')
		if 0 == ret:
			return msg
	except:
		pass
	return 'noweb'

# 编译日期
def __build_date():
	try:
		ret,msg = commands.getstatusoutput('sys-manager version -d')
		if 0 == ret:
			return msg.split('\n')[-1]
	except:
		pass
	return ''

def __get_sys_version():
	return __apps_ver() + VER_SEP + __kernel_ver() + VER_SEP + __mcu_ver() + VER_SEP + __web_ver() + ' ' + __build_date()

def __get_version(mod):
	_item = {}
	_item['item'] = mod
	_item['value'] = __get_sys_version()
	return _item

_info_list = {'cpu-info':__get_cpu_info,
		'cpu-util': __get_cpu_util,
		'temp': __get_temp,
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

ALARM_DIR='/var/run/sys-mon/alarm'

def AttrRead(dir_path, attr_name):
	value = ''
	full_path = dir_path + os.sep + attr_name
	try:
		f = open(full_path)
		value = f.readline()
	except:
		return value
	else:
		f.close()
	return value.strip()

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
				_stat['value'] = _stat['value'] + '槽位号%s的磁盘故障 ' % str(_disk['slot'])
	except:
		pass
		_stat['value'] = '无法获取'
	if _stat['value'] == '':
		_stat['value'] = 'good'
	return _stat

def __get_stat_vg(mod):
	_stat = {}
	_stat['item'] = mod
	_stat['value'] = ''

	# 通过外部命令获取
	try:
		_vg_list = json.loads(commands.getoutput('sys-manager vg --list'))
		for _vg in _vg_list['rows']:
			if _vg['raid_state'] == 'fail':
				_stat['value'] = _stat['value'] + '卷组%s失效 ' % str(_vg['name'])
			elif _vg['raid_state'] == 'degrade':
				_stat['value'] = _stat['value'] + '卷组%s降级 ' % str(_vg['name'])
			elif _vg['raid_state'] == 'rebuild':
				_stat['value'] = _stat['value'] + '卷组%s重建 ' % str(_vg['name'])
	except:
		pass
		_stat['value'] = '无法获取'
	if _stat['value'] == '':
		_stat['value'] = 'good'
	return _stat

def __get_stat_power(mod):
	_stat = {}
	_stat['item'] = mod
	_val = AttrRead(ALARM_DIR, 'power')
	if _val != '' and _val != 'good':
		_stat['value'] = _val
	else:
		_stat['value'] = 'good'
	return _stat

def __get_stat_fan(mod):
	_stat = {}
	_stat['item'] = mod
	_tmp = AttrRead(ALARM_DIR, 'case-fan1')
	_value = ''
	if _tmp != '' and _tmp != 'good':
		_value = _value + '[机箱风扇1告警: %s] ' % _tmp
	_tmp = AttrRead(ALARM_DIR, 'case-fan2')
	if _tmp != '' and _tmp != 'good':
		_value = _value + '[机箱风扇2告警: %s] ' % _tmp
	#_tmp = AttrRead(ALARM_DIR, 'cpu-fan')
	#if _tmp != '' and _tmp != 'good':
	#	_value = _value + '[CPU风扇告警: %s]' % _tmp
	if _value != '':
		_stat['value'] = _value
	else:
		_stat['value'] = 'good'
	return _stat

def __get_stat_buzzer(mod):
	_stat = {}
	_stat['item'] = mod
	_stat['value'] = 'good'
	ret,msg = commands.getstatusoutput('buzzer-ctl -g')
	if ret == 0:
		if 'on' in msg:
			_stat['value'] = '蜂鸣器告警'
		elif 'force off' in msg:
			_stat['value'] = '蜂鸣器告警, 声音已关闭'
	else:
		_stat['value'] = '蜂鸣器状态获取失败'
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
	sys.exit(0)
