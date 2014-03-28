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

BUZZER_DIR = '/tmp/.buzzer'
BUZZER_CNT = BUZZER_DIR + '/counter'
BUZZER_LOCK = BUZZER_DIR + '/lock'
def inc_buzzer_cnt():
	if not os.path.isdir(BUZZER_DIR):
		os.mkdir(BUZZER_DIR)

	cnt = 1
	f_lock = lock_file(BUZZER_LOCK)
	if os.path.isfile(BUZZER_CNT):
		val = fs_attr_read(BUZZER_CNT)
		if val.isdigit():
			cnt = int(val) + 1
	
	fs_attr_write(BUZZER_CNT, str(cnt))
	unlock_file(f_lock)
	return cnt

def dec_buzzer_cnt():
	if not os.path.isdir(BUZZER_DIR):
		os.mkdir(BUZZER_DIR)

	cnt = 0
	f_lock = lock_file(BUZZER_LOCK)
	if os.path.isfile(BUZZER_CNT):
		val = fs_attr_read(BUZZER_CNT)
		if val.isdigit() and int(val) > 0:
			cnt = int(val) - 1
	
	fs_attr_write(BUZZER_CNT, str(cnt))
	unlock_file(f_lock)
	return cnt

def __set_buzzer(value):
	op = ''
	if 'inc' == value or 'on' == value:
		op = 'on'
	elif 'dec' == value:
		op = 'off'
	elif 'mute' == value or 'off' == value:
		op = foff
	else:
		return False, '设置蜂鸣器失败, 不支持 %s' % value
	
	if op != '':
		ret = os.system('/usr/local/bin/buzzer-ctl -d %s' % op)
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
