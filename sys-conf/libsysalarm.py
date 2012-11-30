#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import xml
import os
from xml.dom import minidom

ALARM_CONF_FILE = '/opt/sys/alarm-conf.xml'
ALARM_CONF_DFT_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<alarm>
</alarm>
"""

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

def __add_xmlnode(root, name):
	_impl = minidom.getDOMImplementation()
	_dom = _impl.createDocument(None, name, None)
	_node = _dom.createElement(name)
	root.appendChild(_node)
	return _node

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
	_root = doc.documentElement

	for node in __get_xmlnode(_root, 'category'):

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
	return True,_email

def __check_alarm_conf():
	if not os.path.isfile(ALARM_CONF_FILE):
		d,f = os.path.split(ALARM_CONF_FILE)
		os.makedirs(d) if not os.path.isdir(d) else None
		fd = open(ALARM_CONF_FILE, 'w')
		fd.write(ALARM_CONF_DFT_CONTENT)
		fd.close()
	return

def alarm_email_set(email=email_conf()):

	__check_alarm_conf()

	ret,doc = __load_xml(ALARM_CONF_FILE)
	if not ret:
		return ret,doc

	root = doc.documentElement

	_email = None
	for _category in __get_xmlnode(doc, 'category'):
		if __get_attrvalue(_category, 'name') == 'email':
			#root.removeChild(_category)
			_email = _category
			break

	if _email is None:
		_email = __add_xmlnode(root, 'category')
		__set_attrvalue(_email, 'name', 'email')

	# update node
	if email.switch:
		if email.switch != 'enable' and email.switch != 'disable':
			return False, '--set参数的取值只能是enable或者disable'
		__set_attrvalue(_email, 'switch', email.switch)
	else:
		__set_attrvalue(_email, 'switch', 'disable')

	if email.receiver:
		for recv in email.receiver.split(';'):
			_recv = __add_xmlnode(_email, 'receiver')
			__set_attrvalue(_recv, 'value', recv)

	if email.smtp_host and email.smtp_port:
		_smtp = __add_xmlnode(_email, 'smtp')
		__set_attrvalue(_smtp, 'host', email.smtp_host)
		__set_attrvalue(_smtp, 'port', email.smtp_port)

	if email.ssl:
		if email.ssl != 'enable' and email.ssl != 'disable':
			return False, 'ssl参数的取值只能是enable或者disable'
		_ssl = __add_xmlnode(_email, 'ssl')
		__set_attrvalue(_ssl, 'switch', email.ssl)

	if email.auth:
		if email.auth != 'enable' and email.auth != 'disable':
			return False, 'auth参数的取值只能是enable或者disable'
		_auth = __add_xmlnode(_email, 'auth')
		__set_attrvalue(_auth, 'switch', email.auth)
		__set_attrvalue(_auth, 'user', email.auth_user)
		__set_attrvalue(_auth, 'password', email.auth_password)

	try:
		f = open(ALARM_CONF_FILE, 'w')
		doc.writexml(f, encoding='utf-8')
		f.close()
	except:
		return False, '设置电子邮件参数出错,写入配置文件失败!'
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

def alarm_set(module, switch=None, category=None):

	if module not in _alarm_module:
		return False, '告警模块 %s 不存在，请检查输入参数!' % module

	if switch is None:
		return False, '缺少switch参数!'
	elif switch != 'enable' and switch != 'disable':
		return False, 'switch参数只能是enable或者disable!'

	if category and category not in _alarm_category:
		return False, '告警方式 %s 不正确，请检查输入参数!'

	__check_alarm_conf()
	ret,doc = __load_xml(ALARM_CONF_FILE)
	if ret is False:
		return False, '加载配置文件失败!'

	_module = None
	_root = doc.documentElement

	for _node in __get_xmlnode(_root, 'module'):
		if __get_attrvalue(_node, 'name') == module:
			_module = _node
			break

	if _module is None:
		_module = __add_xmlnode(_root, 'module')
		__set_attrvalue(_module, 'name', module)
		__set_attrvalue(_module, 'switch', 'disable')
		__set_attrvalue(_module, 'buzzer', 'disable')
		__set_attrvalue(_module, 'sys-led', 'disable')
		__set_attrvalue(_module, 'email', 'disable')

	if category is None:
		__set_attrvalue(_module, 'switch', switch)
	#elif category == 'sys-led':
	#	__set_attrvalue(_module, 'sys_led', switch)
	else:
		__set_attrvalue(_module, category, switch)

	try:
		f = open(ALARM_CONF_FILE, 'w')
		doc.writexml(f, encoding='UTF-8')
		f.close()
	except:
		return False, '更新配置文件失败!'

	return True, '修改告警设置成功!'

def alarm_get(module=None):

	ret,doc = __load_xml(ALARM_CONF_FILE)
	if ret is False:
		return False, '加载配置文件失败!'

	_root = doc.documentElement
	_mod_list = []
	for _node in __get_xmlnode(_root, 'module'):
		_mod = {}
		_mod['module'] = __get_attrvalue(_node, 'name')
		_mod['status'] = __get_attrvalue(_node, 'switch')
		_mod['buzzer'] = __get_attrvalue(_node, 'buzzer')
		_mod['sys-led'] = __get_attrvalue(_node, 'sys-led')
		_mod['email'] = __get_attrvalue(_node, 'email')
		_mod_list.append(_mod)

	return True, _mod_list

if __name__ == '__main__':
	import sys
	print alarm_email_get()
	sys.exit(0)
	email = email_conf()
	email.switch = 'enable'
	email.receiver = 'abc@gmail.com;def@gmail.com;slash@163.com'
	email.smtp_host = 'smtp.test.com'
	email.smtp_port = '25'
	email.ssl = 'disable'
	email.auth = 'enable'
	email.auth_user = 'auth-test@user.com'
	email.auth_password = 'auth-test-password'
	print alarm_email_set(email)
