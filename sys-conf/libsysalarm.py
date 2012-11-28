#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml
from xml.dom import minidom
import json

ALARM_CONF_FILE = '/opt/sys/alarm-conf.xml'

# ----------------------------------------
# xml操作
# ----------------------------------------

def __load_xml(filename):
	try:
		doc = minidom.parse(filename)
	except IOError,e:
		return False, '读取配置分区出错！%s' % e
	except xml.parsers.expat.ExpatError, e:
		return False, '磁盘配置文件格式出错！%s' % e
	except e:
		return False, '无法解析磁盘配置文件！%s' % e
	except:
		return False, '加载配置文件失败，未知错误!'
	return True,doc

def __get_xmlnode(node, name):
	return node.getElementsByTagName(name) if node else None

def __get_attrvalue(node, attrname):
	return node.getAttribute(attrname) if node else None

def __set_attrvalue(node, attr, value):
	return node.setAttribute(attr, value)

def __remove_attr(node, attr):
	return node.removeAttribute(attr)

# ----------------------------------------
# 设置电子邮件告警方式
# ----------------------------------------
class email_conf:
	def __init__(self):
		self.switch = None
		self.receiver = None
		self.smtp_host = None
		self.smtp_port = None
		self.ssl = None
		self.auth = None
		self.auth_user = None
		self.auth_password = None

def alarm_email_get():
	ret,doc = __load_xml(ALARM_CONF_FILE)
	if not ret:
		return ret,doc

	_email = email_conf()
	for node in __get_xmlnode(doc, 'category'):
		if __get_attrvalue(node, 'name') != 'email':
			continue
		# load conf
		_email.switch = __get_attrvalue(node, 'switch')
		for _recv in __get_xmlnode(node, 'receiver'):
			if not _email.receiver:
				_email.receiver = __get_attrvalue(_recv, 'value')
			else:
				_email.receiver = _email.receiver + ';' + __get_attrvalue(_recv, 'value')
		_smtp = __get_xmlnode(node, 'smtp')
		if _smtp:
			_email.smtp_host = __get_attrvalue(_smtp[0], 'host')
			_email.smtp_port = __get_attrvalue(_smtp[0], 'port')

		_ssl = __get_xmlnode(node, 'ssl')
		if _ssl:
			_email.ssl = __get_attrvalue(_ssl[0], 'switch')

		_auth = __get_xmlnode(node, 'auth')
		if _auth:
			_email.auth = __get_attrvalue(_auth[0], 'switch')
			_email.auth_user = __get_attrvalue(_auth[0], 'user')
			_email.auth_password = __get_attrvalue(_auth[0], 'password')
		break
	_email_dict = {}
	_email_dict['alarm'] = 'email'
	_email_dict['value'] = _email.switch
	if _email.switch:
		_email_attr = {}
		_email_attr['receiver'] = _email.receiver
		_email_attr['smtp_host'] = _email.smtp_host
		_email_attr['smtp_port'] = _email.smtp_port
		_email_attr['with_ssl'] = _email.ssl
		if _email.auth == 'enable':
			_attr_auth = {}
			_attr_auth['user'] = _email.auth_user
			_attr_auth['password'] = _email.auth_password
			_email_attr['auth'] = _attr_auth
		_email_dict['attrs'] = _email_attr

	#print json.dumps(_email_dict, indent = 4)

	return True,_email_dict

def alarm_email_set(email=email_conf()):
	return True,'设置电子邮件参数成功'

def alarm_email_test():
	return True,'电子邮件配置测试成功'

# ---------------------------------------
# 设置不同模块告警开关
# ---------------------------------------
_alarm_module = ['power', 'disk', 'vg', 'temperature', 'fan']
_alarm_category = ['buzzer', 'sys-led', 'email']

def get_alarm_module():
	return str(_alarm_module)

def get_alarm_category():
	return str(_alarm_category)

def alarm_set(module, switch, category):
	return True, ''

if __name__ == '__main__':
	print alarm_email_get()
