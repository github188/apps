#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import os, commands

from libcommon import *

def __set_hostname(value):
	try:
		ret,msg = commands.getstatusoutput('/bin/hostname %s' % value)
		if ret == 0:
			f = open('/etc/hostname', 'w')
			f.write(value)
			f.close()
			return True, '设置主机名称为 %s 操作成功' % value
	except:
		pass
	return False, '设置主机名称操作失败!'

def __set_fan_speed(value):
	return False, '目前不支持设置风扇操作'

def __set_http_port(value):
	return False, '暂时不支持设置http端口操作'

def __set_buzzer(value):
	op = ''
	if 'inc' == value or 'on' == value:
		op = 'on'
	elif 'dec' == value or 'off' == value:
		op = 'off'
	elif 'mute' == value:
		op = 'foff'
	else:
		return False, '设置蜂鸣器失败, 不支持 %s' % value
	
	if op != '':
		ret = os.system('buzzer-ctl -s %s' % op)
	else:
		ret = 0

	if ret == 0:
		return True, '设置蜂鸣器成功'
	return False, '设置蜂鸣器失败'

_param_list = {'hostname': __set_hostname,
		'fan-speed': __set_fan_speed,
		'http-port': __set_http_port,
		'buzzer': __set_buzzer}

def get_param_item():
	return str(_param_list.keys())

def sys_param_set(param=None, value=None):
	if not param:
		return False, '请输入需要设置的系统参数'
	for para,func in _param_list.items():
		if para == param:
			return func(value)
	return False, '不支持设置 %s 操作' % param
