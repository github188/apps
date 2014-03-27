#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import os
import sys
import re

from xml.dom import minidom
import xml

from libiscsicomm import *
from libiscsitarget import iSCSIUpdateCFG
from libiscsitarget import isTargetExist
from libiscsitarget import iSCSIGetTargetList

ISCSI_CHAP_CONF = SCST.CFG_DIR + '/iscsi-chap-conf.xml'

class iSCSICHAPIncoming:
	def __init__(self):
		self.user = ''
		self.password = ''
		self.active = ''

class iSCSICHAP:
	def __init__(self):
		self.target_name = ''
		self.incoming = []

def chap_sysfs_user_add(tgt, user, pwd):
	cmd = 'add_target_attribute %s IncomingUser %s %s' % (tgt, user, pwd)
	return fs_attr_write(SCST.TARGET_DIR + '/mgmt', cmd)

def chap_sysfs_user_remove(tgt, user):
	cmd = 'del_target_attribute %s IncomingUser %s' % (tgt, user)
	return fs_attr_write(SCST.TARGET_DIR + '/mgmt', cmd)

def chap_conf_check():
	if os.path.isfile(ISCSI_CHAP_CONF):
		return

	_dir = os.path.dirname(ISCSI_CHAP_CONF)
	if not os.path.exists(_dir):
		os.makedirs(_dir)

	doc = minidom.Document()
	root = doc.createElement('iscsi')
	doc.appendChild(root)

	xml_save(doc, ISCSI_CHAP_CONF)
	return

def chap_conf_user_add(tgt, user, pwd):
	chap_conf_check()

	doc = xml_load(ISCSI_CHAP_CONF)
	if None == doc:
		return False

	root = doc.documentElement
	
	# find target node
	target = None
	for item in root.getElementsByTagName('target'):
		if item.getAttribute('name') == tgt:
			target = item
			break
	if target is None:
		target = doc.createElement('target')
		target.setAttribute('name', tgt)
		root.appendChild(target)
	
	# add new incoming user
	incoming = doc.createElement('incoming')
	incoming.setAttribute('user', user)
	incoming.setAttribute('password', pwd)
	incoming.setAttribute('active', 'enable')
	target.appendChild(incoming)

	return xml_save(doc, ISCSI_CHAP_CONF)

def chap_conf_user_remove(tgt, user):
	chap_conf_check()

	doc = xml_load(ISCSI_CHAP_CONF)
	if None == doc:
		return False

	root = doc.documentElement
	
	# find target node
	target = None
	for item in root.getElementsByTagName('target'):
		if item.getAttribute('name') == tgt:
			target = item
			break
	if target is None:
		return False
	
	incoming = None
	for item in target.getElementsByTagName('incoming'):
		if item.getAttribute('user') == user:
			incoming = item
			break

	if incoming is None:
		return False

	target.removeChild(incoming)
	return xml_save(doc, ISCSI_CHAP_CONF)

def chap_conf_user_get(tgt, user):
	chap_conf_check()

	doc = xml_load(ISCSI_CHAP_CONF)
	if None == doc:
		return None

	root = doc.documentElement
	
	# find target node
	target = None
	for item in root.getElementsByTagName('target'):
		if item.getAttribute('name') == tgt:
			target = item
			break
	if target is None:
		return None
	
	incoming = None
	for item in target.getElementsByTagName('incoming'):
		if item.getAttribute('user') == user:
			tmp = iSCSICHAPIncoming()
			tmp.user = item.getAttribute('user')
			tmp.password = item.getAttribute('password')
			tmp.active = item.getAttribute('active')
			return tmp

	return None

def chap_conf_user_set(tgt, user, state):
	chap_conf_check()
	
	if state != 'enable':
		state = 'disable'

	doc = xml_load(ISCSI_CHAP_CONF)
	if None == doc:
		return False
	root = doc.documentElement
	
	# find target node
	target = None
	for item in root.getElementsByTagName('target'):
		if item.getAttribute('name') == tgt:
			target = item
			break
	if target is None:
		return False
	
	finished = False
	for item in target.getElementsByTagName('incoming'):
		if user != '':
			if item.getAttribute('user') != user:
				continue
			else:
				finished = True
		
		item.setAttribute('active', state)
		if finished:
			break
	
	return xml_save(doc, ISCSI_CHAP_CONF)

def iSCSIChapUserExist(tgt, user):
	if chap_conf_user_get(tgt, user) != None:
		return True
	return False

def iSCSIChapList(tgt = ''):
	chap_list = []

	doc = xml_load(ISCSI_CHAP_CONF)
	if None == doc:
		return chap_list

	root = doc.documentElement
	for target in root.getElementsByTagName('target'):
		chap = iSCSICHAP()
		for incoming in target.getElementsByTagName('incoming'):
			tmp = iSCSICHAPIncoming()
			tmp.user = incoming.getAttribute('user')
			tmp.password = incoming.getAttribute('password')
			tmp.active = incoming.getAttribute('active')
			chap.incoming.append(tmp.__dict__)

		chap_list.append(chap)

	return chap_list

def iSCSIChapAddUser(tgt, user, pwd):
	err_msg = '添加CHAP用户 %s ' % user
	
	if not isTargetExist(tgt):
		return False, err_msg + '失败, Target %s 不存在' % tgt

	if iSCSIChapUserExist(tgt, user):
		return False, err_msg + '失败, 用户已存在'

	if len(pwd) < 12:
		return False, err_msg + '失败, 密码长度至少为12个英文或数字'

	if not chap_sysfs_user_add(tgt, user, pwd):
		return False, err_msg + '失败, 系统错误'
	
	if not iSCSIUpdateCFG():
		chap_sysfs_user_remove(tgt, user, pwd)
		return False, err_msg + '失败, 保存配置文件失败'

	if not chap_conf_user_add(tgt, user, pwd):
		chap_sysfs_user_remove(tgt, user, pwd)
		iSCSIUpdateCFG()
		return False, err_msg + '失败, 保存CHAP配置文件失败'

	return True, err_msg + '成功'

def iSCSIChapRemoveUser(tgt, user):
	err_msg = '删除CHAP用户 %s ' % user

	if not isTargetExist(tgt):
		return False, err_msg + '失败, Target %s 不存在' % tgt

	if not iSCSIChapUserExist(tgt, user):
		return False, err_msg + '失败, 用户不存在'

	if not chap_conf_user_remove(tgt, user):
		return False, err_msg + '失败, 保存CHAP配置文件失败'

	chap_sysfs_user_remove(tgt, user)
	iSCSIUpdateCFG()

	return True, err_msg + '成功'

def iSCSIChapDisableUser(tgt, user):
	err_msg = '禁用CHAP用户 %s ' % user

	if not iSCSIChapUserExist(tgt, user):
		return False, err_msg + '失败, 用户不存在'

	if not chap_conf_user_set(tgt, user, 'disable'):
		return False, err_msg + '失败, 保存CHAP配置文件失败'
	
	if not chap_sysfs_user_remove(tgt, user):
		return ret, err_msg + '失败, 系统错误'

	if not iSCSIUpdateCFG():
		return  False, err_msg + '失败, 保存配置文件失败'

	return True, err_msg + '成功'

def iSCSIChapEnableUser(tgt, user):
	err_msg = '启用CHAP用户 %s ' % user

	incoming = chap_conf_user_get(tgt, user)
	if incoming is None:
		return False, err_msg + '失败, 用户不存在'
	
	if not chap_conf_user_set(tgt, user, 'enable'):
		return False, err_msg + '失败, 保存CHAP配置文件失败'

	if not chap_sysfs_user_add(tgt, incoming.user, incoming.password):
		return ret, err_msg + '失败, 系统错误'

	if not iSCSIUpdateCFG():
		return  False, err_msg + '失败, 保存配置文件失败'

	return True, '启用CHAP用户 %s 成功!' % user

def iSCSIChapEnable(tgt):
	for x in iSCSIChapList(tgt):
		for y in x.incoming:
			chap_sysfs_user_add(tgt, y['user'], y['password'])
	iSCSIUpdateCFG()
	if not chap_conf_user_set(tgt, '', 'enable'):
		return False, '打开CHAP认证失败, 保存CHAP配置文件失败'

	return True, '打开CHAP认证成功'

def iSCSIChapDisable(tgt):
	for x in iSCSIChapList(tgt):
		for y in x.incoming:
			chap_sysfs_user_remove(tgt, y['user'])

	iSCSIUpdateCFG()
	if not chap_conf_user_set(tgt, '', 'disable'):
		return False, '关闭CHAP认证失败, 保存CHAP配置文件失败'

	return True, '关闭CHAP认证成功'

if __name__ == '__main__':
	sys.exit(0)