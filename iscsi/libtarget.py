#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libiscsicommon import *

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
		self.proto = iSCSI_Protocol()
		self.attr = TargetAttr()
		self.stat = TargetStat()

def isTargetExist(tgt_name):
	isExist = False
	try:
		if (os.path.isdir(SCST.ROOT_DIR + os.sep + 'targets/iscsi' + tgt_name)):
			isExist = True
		else:
			isExist = False
	except IOError,e:
		raise e
	return isExist

def getTargetAttr(tgt_name):
	tgt_full_path = SCST.ROOT_DIR + '/targets/iscsi/' + tgt_name
	tgt_attr = TargetAttr()
	tgt_attr.NopInInterval = AttrRead(tgt_full_path, 'NopInInterval')
	tgt_attr.NopInTimeout = AttrRead(tgt_full_path, 'NopInTimeout')
	tgt_attr.RspTimeOut = AttrRead(tgt_full_path, 'RspTimeout')
	tgt_attr.MaxSessions = AttrRead(tgt_full_path, 'MaxSessions')
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
	tgt.attr = getTargetAttr(tgt_name)
	tgt.proto = getISCSIProto(tgt_name)
	tgt.stat = getTargetStat(tgt_name)
	return tgt

def getTargetList():
	target_list = []
	target_dir = SCST.ROOT_DIR + os.sep + 'targets/iscsi'
	for tgt in  os.listdir(target_dir):
		tgt_full_path = target_dir + os.sep + tgt
		if os.path.isdir(tgt_full_path):
			target_list.append(getTargetInfo(os.path.basename(tgt_full_path)))

	return target_list

def setTargetAttr(tgt_name, attr, value):
	return

# 测试代码
if __name__ == '__main__':
	# 获取Target列表
	tgt_list = getTargetList()
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
