#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import xml
import os, commands
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from xml.dom import minidom

from libcommon import *

ALARM_EMAIL_CONF = CONF_ROOT_DIR + '/system/alarm-email-conf.xml'
ALARM_EMAIL_CONF_DEF = """<?xml version="1.0" encoding="UTF-8"?>
<alarm_email/>
"""
"""
 <alarm_email switch="enable" receiver="xxx@xxx.com" smtp_host="smtp.xxx.com"
smtp_port="25" ssl="disable" auth_user="xxx@xxx.com" auth_password="xxx" />
"""

class AlarmEmailConf:
	def __init__(self):
		self.switch = 'off'
		self.receiver = None
		self.smtp_host = None
		self.smtp_port = 0
		self.ssl = None
		self.auth_user = None
		self.auth_password = None

def check_alarm_email_conf():
	if not os.path.isfile(ALARM_EMAIL_CONF):
		dirname = os.path.dirname(ALARM_EMAIL_CONF)
		if not os.path.isdir(dirname):
			os.makedirs(dirname)

		fd = open(ALARM_EMAIL_CONF, 'w')
		fd.write(ALARM_EMAIL_CONF_DEF)
		fd.close()

def alarm_email_get():
	alarm_email = AlarmEmailConf()
	check_alarm_email_conf()
	doc = xml_load(ALARM_EMAIL_CONF)
	if None == doc:
		return None

	root = doc.documentElement
	alarm_email.switch = root.getAttribute('switch')
	alarm_email.receiver = root.getAttribute('receiver')
	alarm_email.smtp_host = root.getAttribute('smtp_host')
	smtp_port = root.getAttribute('smtp_port')
	if smtp_port.isdigit():
		alarm_email.smtp_port = int(smtp_port)
	alarm_email.ssl = root.getAttribute('ssl')
	alarm_email.auth_user = root.getAttribute('auth_user')
	alarm_email.auth_password = root.getAttribute('auth_password')
	
	return alarm_email

def alarm_email_set(alarm_email):
	err_msg = '设置邮件告警'
	
	check_alarm_email_conf()
	if alarm_email.switch is None:
		return False, '缺少--set参数!'

	if alarm_email.switch != 'enable':
		alarm_email.switch = 'disable'
		
	if alarm_email.ssl != 'enable':
		alarm_email.ssl = 'disable'

	doc = xml_load(ALARM_EMAIL_CONF)
	if None == doc:
		return False, err_msg + '失败, 打开配置文件 %s 失败' % ALARM_EMAIL_CONF

	root = doc.documentElement
	root.setAttribute('switch', alarm_email.switch)
	if alarm_email.switch != 'disable':
		root.setAttribute('receiver', alarm_email.receiver)
		root.setAttribute('smtp_host', alarm_email.smtp_host)
		root.setAttribute('smtp_port', alarm_email.smtp_port)
		root.setAttribute('ssl', alarm_email.ssl)
		root.setAttribute('auth_user', alarm_email.auth_user)
		root.setAttribute('auth_password', alarm_email.auth_password)
	
	if not xml_save(doc, ALARM_EMAIL_CONF):
		return False, err_msg + '失败, 保存配置文件 %s 失败' % ALARM_EMAIL_CONF

	return True, err_msg + '成功'

# send mail with smtplib
def alarm_email_send(subject, content):
	err_msg = '发送邮件'
	ret = 900
	msg = ''
	alarm_email = alarm_email_get()
	if 'off' == alarm_email.switch:
		return True, "没有配置邮件告警"

	try:
		smtp = smtplib.SMTP(timeout = 10)
		ret, msg = smtp.connect(alarm_email.smtp_host, alarm_email.smtp_port)
		if ret > 400:
			raise Exception(msg)
	
		ret, msg = smtp.docmd("EHLO server")
		if ret != 250:
			raise Exception(msg)
		
		if msg.find('STARTTLS') > 0:
			ret, msg = smtp.starttls()
			if ret != 220:
				raise Exception(msg)
	
		ret, msg = smtp.login(alarm_email.auth_user, alarm_email.auth_password)
		if ret != 235:
			raise Exception(msg)
		
		hostname = commands.getoutput('hostname')
		ipaddr = commands.getoutput("ifconfig eth0 | grep 'inet addr:' | awk -F ':' '{print $2}' | awk '{print $1}'")
		_content = '设备: %s %s\r\n事件: %s\r\n信息: %s' % (hostname, ipaddr, subject, content)
	
		to = alarm_email.receiver.split(';')
		email_msg = MIMEText(_content, 'plain', 'utf-8')
		email_msg['From'] = Header(alarm_email.auth_user, 'utf-8')
		email_msg['To'] = Header(alarm_email.receiver, 'utf-8')
		email_msg['Subject'] = Header(subject, 'utf-8')
	
		smtp.sendmail(alarm_email.auth_user, to, email_msg.as_string())
		smtp.quit()
		return True, err_msg + "成功"

	except Exception, e:
		try:
			smtp.quit()
		except:
			pass
		return False, err_msg + "失败 " + e.args[0]

# send test mail
def alarm_email_test():
	subject = "测试邮件 %s" % time.ctime()
	content = subject
	ret, msg = alarm_email_send(subject, content)
	if not ret:
		return False, msg

	return True, "发送测试邮件成功"

if __name__ == '__main__':
	sys.exit(0)
