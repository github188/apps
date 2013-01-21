#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re

from xml.dom import minidom
import xml

from libiscsicommon import *
from libtarget import iSCSIUpdateCFG
from libtarget import isTargetExist
from libtarget import iSCSIGetTargetList

ISCSI_CHAP_CONF = '/opt/jw-conf/iscsi/iscsi-chap-conf.xml'

class iSCSICHAPIncoming:
	def __init__(self):
		self.user = ''
		self.password = ''
		self.active = ''

class iSCSICHAP:
	def __init__(self):
		self.target_name = ''
		self.active = ''
		self.incoming = []

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


def _chap_sysfs_user_add(tgt, user, pwd):
	if not isTargetExist(tgt):
		return False, '增加CHAP用户失败，Target %s 不存在!' % tgt
	try:
		cmd = 'add_target_attribute %s IncomingUser %s %s' % (tgt, user, pwd)
		AttrWrite(SCST.TARGET_DIR, 'mgmt', cmd)
	except:
		return False, '增加CHAP用户 %s 失败，写入iSCSI命令错误!'
	return True, ''

def _chap_sysfs_user_remove(tgt, user):
	if not isTargetExist(tgt):
		return False, '删除CHAP用户失败，Target %s 不存在!' % tgt
	cmd = 'del_target_attribute %s IncomingUser %s' % (tgt, user)
	if not AttrWrite(SCST.TARGET_DIR, 'mgmt', cmd):
		return False, '删除CHAP用户 %s 失败，写入iSCSI命令错误!'
	return True, '删除CHAP用户 %s 成功!'

def _chap_conf_check():
	if os.path.isfile(ISCSI_CHAP_CONF):
		return
	try:
		_dir = os.path.split(ISCSI_CHAP_CONF)[0]
		if not os.path.exists(_dir):
			os.makedirs(_dir)
		doc = minidom.Document()
		root = doc.createElement('iscsi')
		doc.appendChild(root)

		f = open(ISCSI_CHAP_CONF, 'w')
		#f.write(doc.toprettyxml(newl='', indent='', encoding='UTF-8'))
		f.write(doc.toxml(encoding='UTF-8'))
		f.close()
	except:
		return
	return

def _chap_conf_user_add(tgt, user, pwd):
	_chap_conf_check()

	ret,doc = __load_xml(ISCSI_CHAP_CONF)
	if not ret:
		return False, doc
	root = doc.documentElement
	
	# find target node
	target = None
	for x in __get_xmlnode(root, 'target'):
		if __get_attrvalue(x, 'name') == tgt:
			target = x
			break
	if target is None:
		target = doc.createElement('target')
		__set_attrvalue(target, 'name', tgt)
		__set_attrvalue(target, 'chap', 'enable')
		root.appendChild(target)
	

	# add new incoming user
	incoming = doc.createElement('incoming')
	__set_attrvalue(incoming, 'user', user)
	__set_attrvalue(incoming, 'password', pwd)
	__set_attrvalue(incoming, 'active', 'enable')
	target.appendChild(incoming)

	try:
		f = open(ISCSI_CHAP_CONF, 'w')
		#f.write(doc.toprettyxml(newl='', indent='', encoding='UTF-8'))
		f.write(doc.toxml(encoding='UTF-8'))
		f.close()
	except:
		return False, '增加iSCSI CHAP Incoming用户出错，写入配置文件失败!'
	return True, '增加iSCSI CHAP Incoming用户到配置文件成功!'

def _chap_conf_user_remove(tgt, user):
	_chap_conf_check()

	ret,doc = __load_xml(ISCSI_CHAP_CONF)
	if not ret:
		return False,doc
	root = doc.documentElement

	target_found = False
	incoming_found = False
	for target in __get_xmlnode(root, 'target'):
		if __get_attrvalue(target, 'name') != tgt:
			continue
		target_found = True
		for incoming in __get_xmlnode(target, 'incoming'):
			if __get_attrvalue(incoming, 'user') != user:
				continue
			target.removeChild(incoming)
			incoming_found = True
			break
	
	if not target_found:
		return False, '删除CHAP用户 %s 失败，未找到Target %s' % (user,tgt)
	elif not incoming_found:
		return False, '删除CHAP用户 %s 失败，未找到用户配置!' % user
	
	try:
		f = open(ISCSI_CHAP_CONF, 'w')
		#f.write(doc.toprettyxml(newl='', indent='', encoding='UTF-8'))
		f.write(doc.toxml(encoding='UTF-8'))
		f.close()
	except:
		return '删除CHAP用户 %s 失败，写入配置文件出错!' % user
	return True, '删除CHAP用户 %s 成功!' % user

def _chap_conf_user_get(tgt, user):
	_chap_conf_check()

	ret,doc = __load_xml(ISCSI_CHAP_CONF)
	if not ret:
		return None
	root = doc.documentElement

	for target in __get_xmlnode(root, 'target'):
		if __get_attrvalue(target, 'name') != tgt:
			continue
		for incoming in __get_xmlnode(target, 'incoming'):
			if __get_attrvalue(incoming, 'user') != user:
				continue
			tmp = iSCSICHAPIncoming()
			tmp.user = __get_attrvalue(incoming, 'user')
			tmp.password = __get_attrvalue(incoming, 'password')
			tmp.active = __get_attrvalue(incoming, 'active')
			return tmp
	return None

def _chap_conf_user_enable(tgt, user, set_all = False):
	_chap_conf_check()

	ret,doc = __load_xml(ISCSI_CHAP_CONF)
	if not ret:
		return ret,doc
	root = doc.documentElement

	for target in __get_xmlnode(root, 'target'):
		if __get_attrvalue(target, 'name') != tgt:
			continue
		target_found = True
		for incoming in __get_xmlnode(target, 'incoming'):
			if not set_all:
				if __get_attrvalue(incoming, 'user') != user:
					continue
			incoming_found = True
			__set_attrvalue(incoming, 'active', 'enable')
	
	if not target_found:
		return False, '打开CHAP用户%s配置失败，Target % 不存在!' % (user, tgt)
	elif not incoming_found:
		return False, '打开CHAP用户%s配置失败，用户不存在!' % user

	try:
		f = open(ISCSI_CHAP_CONF, 'w')
		#f.write(doc.toprettyxml(newl='', indent='', encoding='UTF-8'))
		f.write(doc.toxml(encoding='UTF-8'))
		f.close()
	except:
		return False, '打开CHAP用户%s配置失败，写入配置文件错误!' % user
	return True, '打开CHAP用户%s配置成功!' % user

def _chap_conf_user_disable(tgt, user, set_all = False):
	_chap_conf_check()

	ret,doc = __load_xml(ISCSI_CHAP_CONF)
	if not ret:
		return ret,doc
	root = doc.documentElement

	for target in __get_xmlnode(root, 'target'):
		if __get_attrvalue(target, 'name') != tgt:
			continue
		target_found = True
		for incoming in __get_xmlnode(target, 'incoming'):
			if not set_all:
				if __get_attrvalue(incoming, 'user') != user:
					continue
			incoming_found = True
			__set_attrvalue(incoming, 'active', 'disable')
	
	if not target_found:
		return False, '禁用CHAP用户%s配置失败，Target % 不存在!' % (user, tgt)
	elif not incoming_found:
		return False, '禁用CHAP用户%s配置失败，用户不存在!' % user

	try:
		f = open(ISCSI_CHAP_CONF, 'w')
		#f.write(doc.toprettyxml(newl='', encoding='UTF-8'))
		f.write(doc.toxml(encoding='UTF-8'))
		f.close()
	except:
		return False, '禁用CHAP用户%s配置失败，写入配置文件错误!' % user
	return True, '禁用CHAP用户%s配置成功!' % user
	
	return True, ''

def _chap_user_exist(tgt, user):
	for x in iSCSIChapList(tgt):
		for y in x.incoming:
			if y['user'] == user:
				return True
	return False

# -----------------------------------------------------------------------------------------

def iSCSIChapList(tgt = ''):
	chap_list = []

	# get all target conf
	for x in iSCSIGetTargetList(tgt):
		chap = iSCSICHAP()
		chap.target_name = x.name
		chap.active = 'enable'

		_dir = '%s/%s' % (SCST.TARGET_DIR, x.name)
		for y in os.listdir(_dir):
			if re.match('^IncomingUser*', y) is None:
				continue
			z = iSCSICHAPIncoming()
			tmp = AttrRead(_dir, y)
			z.user = tmp.split()[0]
			z.password = tmp.split()[1]
			z.active = 'enable'
			chap.incoming.append(z.__dict__)
		chap_list.append(chap)

	ret,doc = __load_xml(ISCSI_CHAP_CONF)
	if not ret:
		return []
	root = doc.documentElement

	for x in __get_xmlnode(root, 'target'):
		chap = None
		for y in chap_list:
			if y.target_name == __get_attrvalue(x, 'name'):
				chap = y
				break
		if chap is None:
			chap = iSCSICHAP()
			chap.target_name = __get_attrvalue(x, 'name')
			chap.active = 'disable'
			chap_list.append(chap)
		for y in __get_xmlnode(x, 'incoming'):
			if __get_attrvalue(y, 'active') != 'disable':
				continue
			incoming = iSCSICHAPIncoming()
			incoming.user = __get_attrvalue(y, 'user')
			incoming.password = __get_attrvalue(y, 'passwrod')
			incoming.active = 'disable'
			chap.incoming.append(incoming.__dict__)
	final_list = []
	for x in chap_list:
		if tgt != '' and x.target_name != tgt:
			continue
		final_list.append(x)
	return final_list

def iSCSIChapAddUser(tgt, user, pwd):
	if _chap_user_exist(tgt, user):
		return False, '增加CHAP用户失败，用户 %s 已经存在!' % user
	if len(pwd) < 12:
		return False, '增加CHAP用户 %s 失败，密码长度至少为12个英文或数字!'
	ret,msg = _chap_sysfs_user_add(tgt, user, pwd)
	if not ret:
		return ret,msg
	ret,msg = _chap_conf_user_add(tgt, user, pwd)
	if not ret:
		return ret,msg
	ret,msg = iSCSIUpdateCFG()
	if not ret:
		return ret,msg
	return True, '增加CHAP用户 %s 成功!' % user

def iSCSIChapRemoveUser(tgt, user):
	if not _chap_user_exist(tgt, user):
		return False, '删除CHAP用户失败， 用户 %s 不存在!' % user
	ret,msg = _chap_sysfs_user_remove(tgt, user)
	if not ret:
		return ret,msg
	ret,msg = _chap_conf_user_remove(tgt, user)
	if not ret:
		return ret,msg
	ret,msg = iSCSIUpdateCFG()
	if not ret:
		return ret,msg
	return True, '删除CHAP用户 %s 成功!' % user

def iSCSIChapDisableUser(tgt, user):
	if not _chap_user_exist(tgt, user):
		return False, '禁用CHAP用户失败，用户 %s 不存在!' % user
	ret,msg = _chap_sysfs_user_remove(tgt, user)
	if not ret:
		return ret,msg
	ret,msg = _chap_conf_user_disable(tgt, user)
	if not ret:
		return ret,msg
	ret,msg = iSCSIUpdateCFG()
	if not ret:
		return ret,msg
	return True, '禁用CHAP用户 %s 成功!' % user

def iSCSIChapEnableUser(tgt, user):
	if not _chap_user_exist(tgt, user):
		return False, '启用CHAP用户失败，用户 %s 不存在!' % user
	incoming = _chap_conf_user_get(tgt, user)
	if incoming is None:
		return False, '启用CHAP用户失败，用户 %s 配置无法获取!' % user
	ret,msg = _chap_sysfs_user_add(tgt, incoming.user, incoming.password)
	if not ret:
		return ret,msg
	ret,msg = _chap_conf_user_enable(tgt, user)
	if not ret:
		return ret,msg
	ret,msg = iSCSIUpdateCFG()
	if not ret:
		return ret,msg
	return True, '启用CHAP用户 %s 成功!' % user

def iSCSIChapEnable(tgt):
	try:
		for x in iSCSIChapList(tgt):
			for y in x.incoming:
				_chap_sysfs_user_add(tgt, y['user'], y['password'])
		_chap_conf_user_enable(tgt, 'all', True)
	except AttributeError, e:
		return False, '打开CHAP认证失败, 未配置CHAP认证用户!'
	except:
		return False, '打开CHAP认证失败，未知错误!'
	return True, '打开CHAP认证成功!'

def iSCSIChapDisable(tgt):
	try:
		for x in iSCSIChapList(tgt):
			for y in x.incoming:
				_chap_sysfs_user_remove(tgt, y['user'])
		_chap_conf_user_disable(tgt, 'all', True)
	except AttributeError, e:
		return False, '禁用CHAP认证失败，未配置CHAP认证用户!'
	except:
		return False, '禁用CHAP认证失败，未知错误!'
	return True, '禁用CHAP成功!'

if __name__ == '__main__':
	#_chap_conf_user_add('abc', 'u123', '123456')
	#_chap_conf_user_add('def', 'u123', '123456')
	#_chap_conf_user_remove('def', 'u123')
	#x = _chap_conf_user_get('abc', 'u123')
	#print x.__dict__
	#print _chap_conf_user_enable('abc', 'u123')
	#print _chap_conf_user_disable('abc', 'u123')
	#print _chap_user_exist('abc', 'u123')
	#print iSCSIChapList()
	#_chap_sysfs_user_add('iqn.2012-12.com.jwele:tgt-2eb526c4', 'abc', '111111111111')
	#_chap_sysfs_user_remove('iqn.2012-12.com.jwele:tgt-2eb526c4', 'abc')
	#print iSCSIChapAddUser('iqn.2012-12.com.jwele:tgt-2eb526c4', 'jxa1', '111111111111')
	#print iSCSIChapRemoveUser('iqn.2012-12.com.jwele:tgt-2eb526c4', 'jxa1')
	#print iSCSIChapDisableUser( 'iqn.2012-12.com.jwele:tgt-2eb526c4', 'jxa1')
	#print iSCSIChapEnableUser( 'iqn.2012-12.com.jwele:tgt-2eb526c4', 'jxa1')
	#print iSCSIChapEnable('iqn.2012-12.com.jwele:tgt-2eb526c4')
	print iSCSIChapDisable('iqn.2012-12.com.jwele:tgt-2eb526c4')
