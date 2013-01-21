#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from libiscsicommon import *
from libtarget import iSCSIUpdateCFG

def _chap_sysfs_user_add(tgt, user, pwd):
	return True, ''

def _chap_sysfs_user_remove(tgt, user):
	return True, ''

def _chap_conf_user_add(tgt, user, pwd):
	return True, ''
	ret,doc = __load_xml(ISCSI_CHAP)
	if not ret:
		return False, doc
	_root = doc.documentElement
	
	user_add = False
	for node in __get_xmlnode(_root, 'target'):
		if __get_attrvalue(node, 'name') != tgt:
			continue
		chap = __get_xmlnode(node, 'chap')
		incoming = __add_xmlnode(chap, 'incoming')
		__set_attrvalue(incoming, 'user', user)
		__set_attrvalue(incoming, 'password', pwd)
		__set_attrvalue(incoming, 'switch', 'enable')

		if __get_attrvalue(chap, 'switch') != 'enable':
			__set_attrvalue(chap, 'switch', 'enable')
		user_add = True
	
	try:
		if user_add:
			f = open(ISCSI_CHAP, 'w')
			doc.writexml(f, encoding='utf-8')
			f.close()
	except:
		return False, '增加iSCSI CHAP Incoming用户出错，写入配置文件失败!'
	return True, '增加iSCSI CHAP Incoming用户到配置文件成功!'

def _chap_conf_user_remove(tgt, user):
	return True, ''

def _chap_conf_user_get(tgt, user):
	return iSCSICHAPIncoming()

def _chap_conf_user_enable(tgt, user, set_all = False):
	return True, ''

def _chap_conf_user_disable(tgt, user, set_all = False):
	return True, ''

def _chap_user_exist(tgt, user):
	return True

# -----------------------------------------------------------------------------------------

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

def iSCSIChapList(tgt = ''):
	return []

def iSCSIChapAddUser(tgt, user, pwd):
	if _chap_user_exist(tgt, user):
		return False, '增加CHAP用户失败，用户 %s 已经存在!' % user
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
	ret,msg = _chap_sysfs_user_remove(tgt, user, pwd)
	if not ret:
		return ret,msg
	ret,msg = _chap_conf_user_remove(tgt, user, pwd)
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
		for x in iSCSIChapList(tgt)['incoming']:
			_chap_sysfs_user_add(tgt, x.user, x.password)
		_chap_conf_user_enable(tgt, 'all', True)
	except AttributeError, e:
		return False, '打开CHAP认证失败, 未配置CHAP认证用户!'
	except:
		return False, '打开CHAP认证失败，未知错误!'
	return True, '打开CHAP认证成功!'

def iSCSIChapDisable(tgt):
	try:
		for x in iSCSIChapList(tgt).incoming:
			_chap_sysfs_user_remove(tgt, x.user)
		_chap_conf_user_disable(tgt, 'all', True)
	except AttributeError, e:
		return False, '禁用CHAP认证失败，未配置CHAP认证用户!'
	except:
		return False, '禁用CHAP认证失败，未知错误!'
	return True, '禁用CHAP成功!'
