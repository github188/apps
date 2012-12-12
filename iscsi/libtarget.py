#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
#os.chdir(os.path.dirname(__file__))

from libiscsicommon import *
from uuid import uuid1

JW_ISCSI = '/opt/jw-conf/iscsi'
JW_ISCSI_DFT_TARGET = 'default-target'

class TargetAttr:
	"""
	Target属性
	"""
	def __init__(self):
		self.NopInInterval = 30
		self.NopInTimeOut = 30
		self.RspTimeout = 90
		self.MaxSessions = 1

class TargetStat:
	"""
	Target统计信息
	"""
	def __init__(self):
		self.QueuedCommands = 0

class Target:
	"""
_	Target对象
	"""
	def __init__(self):
		self.tid = ''
		self.name = ''
		self.state = 'disable'
		self.luns = 0
		self.sessions = 0
		self.iscsi_protocol = {}	# iSCSI_Protocol()
		self.attribute = {}		# TargetAttr()
		self.statistics = {}		# TargetStat()

def isTargetExist(tgt_name):
	return True if os.path.isdir(SCST.TARGET_DIR + os.sep + tgt_name) else False
	"""
	isExist = False
	try:
		if (os.path.isdir(SCST.TARGET_DIR + os.sep + tgt_name)):
			isExist = True
		else:
			isExist = False
	except IOError,e:
		return e
	return isExist
	"""

def getTargetAttr(tgt_name):
	tgt_full_path = SCST.ROOT_DIR + '/targets/iscsi/' + tgt_name
	tgt_attr = TargetAttr()
	tgt_attr.NopInInterval = int(AttrRead(tgt_full_path, 'NopInInterval'))
	tgt_attr.NopInTimeout = int(AttrRead(tgt_full_path, 'NopInTimeout'))
	tgt_attr.RspTimeOut = int(AttrRead(tgt_full_path, 'RspTimeout'))
	tgt_attr.MaxSessions = int(AttrRead(tgt_full_path, 'MaxSessions'))
	return tgt_attr

def getTargetStat(tgt_name):
	tgt_full_path = SCST.ROOT_DIR + '/targets/iscsi/' + tgt_name
	tgt_stat = TargetStat()
	tgt_stat.QueuedCommands = AttrRead(tgt_full_path, 'QueuedCommands')
	return tgt_stat

def getTargetState(tgt_name):
	tgt_mgmt_dir = SCST.ROOT_DIR + os.sep + 'targets/iscsi'
	tgt_dir = tgt_mgmt_dir + os.sep + tgt_name
	if AttrRead(tgt_mgmt_dir, 'enabled') != '0' and AttrRead(tgt_dir, 'enabled') != '0':
		return 'enable'
	return 'disable'

def getTargetInfo(tgt_name):
	tgt_full_path = SCST.ROOT_DIR + '/targets/iscsi/' + tgt_name
	tgt = Target()
	tgt.name = tgt_name
	tgt.tid = AttrRead(tgt_full_path, 'tid')
	tgt.state = getTargetState(tgt_name)
	tgt.luns = len(getDirList(tgt_full_path + os.sep + 'luns'))
	tgt.sessions = len(getDirList(tgt_full_path + os.sep + 'sessions'))
	tgt.attribute = getTargetAttr(tgt_name).__dict__
	tgt.iscsi_protocol = getISCSIProto(tgt_name).__dict__
	tgt.statistics = getTargetStat(tgt_name).__dict__
	return tgt

def __genDefaultTarget():
	_random = str(uuid1()).split('-')[0]
	_tgt = 'iqn.2012-12.com.jwele:tgt-%s' % _random
	if not os.path.isdir(JW_ISCSI):
		os.makedirs(JW_ISCSI)
	AttrWrite(JW_ISCSI, JW_ISCSI_DFT_TARGET, _tgt)
	return _tgt

def iSCSICreateTarget(tgt):
	return True if AttrWrite(SCST.TARGET_DIR, 'mgmt', 'add_target %s' % tgt) else False

def iSCSISetDefaultTarget():

	if iSCSIGetTargetList() != []:
		return True

	# check default target
	if not os.path.isfile('%s/%s' % (JW_ISCSI, JW_ISCSI_DFT_TARGET)):
		_tgt = __genDefaultTarget()
	else:
		_tgt = AttrRead(JW_ISCSI, JW_ISCSI_DFT_TARGET)

	if isTargetExist(_tgt):
		return True

	# make sure module loaded
	os.popen('modprobe scst')
	os.popen('modprobe iscsi-scst')
	os.popen('modprobe scst_vdisk')
	os.popen('iscsi-scstd')

	return iSCSICreateTarget(_tgt)

def iSCSIGetTargetList(tgt = ''):
	target_list = []
	target_dir = SCST.ROOT_DIR + os.sep + 'targets/iscsi'
	for t in getDirList(target_dir):
		tgt_full_path = target_dir + os.sep + t
		if len(tgt) and tgt != t:
			continue
		target_list.append(getTargetInfo(os.path.basename(tgt_full_path)))

	return target_list

def iSCSISetTargetAttr(tgt_name, attr, value):
	if attr != 'MaxSessions':
		return (False, '参数不正确，目前仅支持MaxSessions参数！')
	tgt_full_path = SCST.ROOT_DIR + '/targets/iscsi/' + tgt_name
	if AttrWrite(tgt_full_path, attr, value):
		if AttrRead(tgt_full_path, attr) == value:
			ret,msg = iSCSIUpdateCFG()
			if not ret:
				return True, 'Target属性设置成功!写配置文件失败! %s' % msg
			return (True, 'Target属性设置成功！')
	return (False, 'Target属性设置失败！')

# 测试代码
if __name__ == '__main__':
	print iSCSISetDefaultTarget()
	sys.exit(0)
	# 获取Target列表
	tgt_list = iSCSIGetTargetList()
	for tgt in tgt_list:
		print '----------------------------'
		print 'NAME: ', tgt.name
		print 'TID: ',tgt.tid
		print 'STATE: ',tgt.state
		print 'LUNS: ',tgt.luns
		print 'SESSIONS: ',tgt.sessions
		print dir(tgt)
		print dir(tgt.attr)
		print dir(tgt.proto)

		(isSetOK, msg) = iSCSISetTargetAttr(tgt.name, 'MaxSessions', '10')
		print 'isSetOK: ', isSetOK
		print 'msg: ', msg
