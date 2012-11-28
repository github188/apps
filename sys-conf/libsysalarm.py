#!/usr/bin/env python
# -*- coding: utf-8 -*-

class email_conf:
	def __init__(self):
		self.switch = None
		self.receiver_list = []
		self.smtp_host = None
		self.smtp_port = None
		self.ssl = False
		self.auth = False
		self.auth_user = None
		self.auth_password = None

def alarm_email_get():
	return None

def alarm_email_set(email=email_conf()):
	return True,'设置电子邮件参数成功'

def alarm_email_test():
	return True,'电子邮件配置测试成功'

_alarm_module = ['power', 'disk', 'vg', 'temperature', 'fan']
_alarm_category = ['buzzer', 'sys-led', 'email']

def get_alarm_module():
	return str(_alarm_module)

def get_alarm_category():
	return str(_alarm_category)

def alarm_set(module, switch, category):
	return True, ''
