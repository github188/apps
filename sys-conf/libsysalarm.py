#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import xml
import os
import random
import smtplib
import mimetypes

from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

from xml.dom import minidom

ALARM_CONF_FILE = '/opt/jw-conf/system/alarm-conf.xml'
ALARM_CONF_DFT_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<alarm>
<category name="email" switch="disable"/>
<module buzzer="enable" email="disable" name="power" switch="enable" sys-led="enable"/>
<module buzzer="enable" email="disable" name="disk" switch="enable" sys-led="enable"/>
<module buzzer="enable" email="disable" name="vg" switch="enable" sys-led="enable"/>
<module buzzer="enable" email="disable" name="temperature" switch="enable" sys-led="enable"/>
<module buzzer="enable" email="disable" name="fan" switch="enable" sys-led="enable"/>
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

	__check_alarm_conf()

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
		else:
			_email.ssl = 'disable'

		_auth = __get_xmlnode(node, 'auth')
		if _auth:
			_email.auth = __get_attrvalue(_auth[0], 'switch')
			_email.auth_user = __get_attrvalue(_auth[0], 'user')
			_email.auth_password = __get_attrvalue(_auth[0], 'password')
		else:
			_email.auth = 'disable'
			_email.auth_user = ''
			_email.auth_password = ''
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

	if email.switch is None:
		return False, '缺少--set参数!'

	if email.switch != 'enable' and email.switch != 'disable':
		return False, '--set参数的取值只能是enable或者disable'

	"""
	if email.switch == 'enable':
		if email.receiver is None:
			return False, '缺少--receiver参数!'
		if email.smtp_host is None:
			return False, '缺少--smtp-host参数!'
		if email.smtp_port is None:
			return False, '缺少--smtp-port参数!'
		if email.auth:
			if email.auth != 'enable' and email.auth != 'disable':
				return False, '--auth参数取值只能是enable或者disable'
			if email.auth == 'enable':
				if email.auth_user is None:
					return False, '缺少--auth-user参数!'
				if email.auth_pass is None:
					return False, '缺少--auth-pass参数!'
	"""

	root = doc.documentElement

	_email = None
	for _category in __get_xmlnode(doc, 'category'):
		if __get_attrvalue(_category, 'name') == 'email':
			_email = _category
			break

	if _email is None:
		_email = __add_xmlnode(root, 'category')
		__set_attrvalue(_email, 'name', 'email')
	__set_attrvalue(_email, 'switch', email.switch)

	if email.receiver:
		for _tmp in __get_xmlnode(_email, 'receiver'):
			_email.removeChild(_tmp)
		for recv in email.receiver.split(';'):
			_recv = __add_xmlnode(_email, 'receiver')
			__set_attrvalue(_recv, 'value', recv)

	if email.smtp_host and email.smtp_port:
		_tmp = __get_xmlnode(_email, 'smtp')
		if _tmp == []:
			_smtp = __add_xmlnode(_email, 'smtp')
		else:
			_smtp = _tmp[0]
		__set_attrvalue(_smtp, 'host', email.smtp_host)
		__set_attrvalue(_smtp, 'port', email.smtp_port)

	if email.ssl:
		if email.ssl != 'enable' and email.ssl != 'disable':
			return False, 'ssl参数的取值只能是enable或者disable'
		_tmp = __get_xmlnode(_email, 'ssl')
		if _tmp == []:
			_ssl = __add_xmlnode(_email, 'ssl')
		else:
			_ssl = _tmp[0]
		__set_attrvalue(_ssl, 'switch', email.ssl)

	if email.auth:
		if email.auth != 'enable' and email.auth != 'disable':
			return False, 'auth参数的取值只能是enable或者disable'
		_tmp = __get_xmlnode(_email, 'auth')
		if _tmp == []:
			_auth = __add_xmlnode(_email, 'auth')
		else:
			_auth = _tmp[0]
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

#send mail with smtplib
def alarm_email_send(subject, content):
	setting = email_conf()
	ret, setting = alarm_email_get()
	if not ret:
		return False, "获取邮件配置失败!"
	
	host = setting.smtp_host.encode("utf8")
	port = setting.smtp_port.encode("utf8")
	user = ''
	smtp = smtplib.SMTP()
	ret, msg = smtp.connect(host, port)
	if ret > 400:
		smtp.quit()
		return False, "连接SMTP服务器%s失败!" % smtp
	ret, msg = smtp.docmd("EHLO server")
	if ret != 250:
		smtp.quit()
		return False, "发送EHLO命令到SMTP服务器%s失败!" % smtp

	if msg.find("STARTTLS") >= 0:
		smtp.starttls()
		smtp.ehlo()
		smtp.esmtp_features['auth'] = 'LOGIN DIGEST-MD5 PLAIN'
	if setting.auth_user:
		user = setting.auth_user.encode('utf8')
		password = setting.auth_password.encode('utf8')
		ret, msg = smtp.login(user, password)
		if ret != 235:
			smtp.quit()
			return False, "登陆SMTP服务器%s失败! 返回消息%s" % (smtp, msg)

	receiver = setting.receiver.encode("utf8")
	to = receiver.split(';')
	body = MIMEMultipart('related')
	body['Subject'] = subject
	body['From'] = user
	body['To'] = receiver
	body.preamble = 'This is a multi-part message in MIME format.'
	content = MIMEText(content, 'html', 'utf-8')
	alternative = MIMEMultipart('alternative')
	body.attach(alternative)
	alternative.attach(content)
	msg = body.as_string()
	ret, msg = smtp.sendmail(user, to, msg)
	if ret > 300:
		smtp.quit()
		return False, "发送邮件到%s失败!" % receiver
	smtp.quit()

# send test mail
def alarm_email_test():
	rd = random.randint(1, 100000)
	title = "随机测试邮件%d" % rd
	content = "随机发送测试邮件%d." % rd
	#title = "bbb test mail"
	#content = "bbb send test mail."
	ret,msg = alarm_email_send(title, content)
	if not ret:
		return False, msg

	return True, "电子邮件配置测试成功."

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

	__check_alarm_conf()

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
