#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import commands
#os.chdir(os.path.dirname(__file__))

from libiscsicommon import *
from uuid import uuid1
from libmd import get_mdattr_all

JW_ISCSI = '/opt/jw-conf/iscsi'
JW_ISCSI_DFT_TARGET = 'default-target'

class TargetAttr:
	"""
	Target属性
	"""
	def __init__(self):
		self.NopInInterval = 30
		self.NopInTimeout = 30
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
	tgt_attr.RspTimeout = int(AttrRead(tgt_full_path, 'RspTimeout'))
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

def iSCSICreateTarget(tgt):
	if not AttrWrite(SCST.TARGET_DIR, 'mgmt', 'add_target %s' % tgt):
		return False
	if not AttrWrite(SCST.TARGET_DIR, 'enabled', '1'):
		return False
	if not AttrWrite('%s/%s' % (SCST.TARGET_DIR, tgt), 'enabled', '1'):
		return False
	return True

def __getDefaultTarget():
	return AttrRead(JW_ISCSI, JW_ISCSI_DFT_TARGET)

def __genDefaultTarget():
	_random = str(uuid1()).split('-')[0]
	_tgt = 'iqn.2012-12.com.jwele:tgt-%s' % _random
	if not os.path.isdir(JW_ISCSI):
		os.makedirs(JW_ISCSI)
	AttrWrite(JW_ISCSI, JW_ISCSI_DFT_TARGET, _tgt)
	return __getDefaultTarget()

# Automatically generated by SCST Configurator v2.2.0.
#
#
# TARGET_DRIVER iscsi {
#	enabled 1
#
#		TARGET iqn.2012-12.com.jwele:tgt-7280ad0e {
#				enabled 1
#						rel_tgt_id 1
#							}
#							}
def __genDefaultCfg(fname, tgt):
	try:
		d,f = os.path.split(fname)
		if not os.path.isdir(d):
			os.makedirs(d)
		fd = open(fname, 'w')
		fd.write('#automatically generated by __genDefaultCfg()\n\n\n')
		fd.write('TARGET_DRIVER iscsi {\n')
		fd.write('    enabled 1\n\n')
		fd.write('    TARGET %s {\n' % tgt)
		fd.write('        enabled 1\n')
		fd.write('        rel_tgt_id 1\n')
		fd.write('    }\n')
		fd.write('}\n')
		fd.close()
	except:
		return False
	return True

def iSCSISetDefaultTarget(force = False):
	_tgt = __genDefaultTarget() if __getDefaultTarget() == '' else __getDefaultTarget()
	
	# check & set default scst.conf
	if force or not os.path.exists(SCST.CFG):
		return __genDefaultCfg(SCST.CFG, _tgt)
	return True

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

# 将SCST配置文件中的md节点名称替换为UUID
def iSCSI_SCST_cfg_convert():
	try:
		f = open(SCST.CFG)
		xx = f.read()
		f.close()

		mddev_list = re.findall('\/dev\/md\d+', xx)
		if len(mddev_list) == 0:
			return
		for mdinfo in md_info_mddevs()['rows']:
			if mdinfo['dev'] in mddev_list:
				xx = xx.replace(mdinfo['dev'], mdinfo['raid_uuid'])
		f = open(SCST.CFG, 'w')
		f.write(xx)
		f.close()

		os.rename(tmp_file, SCST.CFG)
	except:
		pass
	return

# 将SCST配置文件中的UUID名称转换为节点名称
# 并且检查对应的分区是否存在，如果不存在，则记录日志删除对应的配置
def iSCSI_SCST_cfg_restore():
	tmp_file = '/tmp/.iscsi-scst-conf'
	try:
		f = open(SCST.CFG)
		xx = f.read()
		f.close()

		uuid_list = re.findall('\w{8}:\w{8}:\w{8}:\w{8}', xx)
		if len(uuid_list) == 0:
			return
		for mdinfo in md_info_mddevs()['rows']:
			if mdinfo['raid_uuid'] in uuid_list:
				xx = xx.replace(mdinfo['raid_uuid'], mdinfo['dev'])

		f = open(tmp_file, 'w')
		f.write(xx)
		f.close()
	except:
		pass
	return tmp_file

def iSCSIUpdateCFG():
	try:
		_cmd = 'scstadmin -write_config %s' % SCST.CFG
		ret,msg = commands.getstatusoutput(_cmd)
		if ret == 0:
			iSCSI_SCST_cfg_convert()
			return True, '写入配置文件成功'
		else:
			return False, msg
	except:
		return False, '写入配置文件失败，未知原因'

def iSCSIRestoreCFG():
	try:
		_cmd = 'scstadmin -config %s' % iSCSI_SCST_cfg_restore()
		ret,msg = commands.getstatusoutput(_cmd)
		if ret == 0:
			return True, '加载iSCSI配置成功'
		# 设置默认配置，保证target能启动
		iSCSISetDefaultTarget(force = True)
		_cmd = 'scstadmin -config %s' % SCST.CFG
		ret,msg = commands.getstatusoutput(_cmd)
		if ret == 0:
			return True, 'Load iSCSI Conf OK!'
		else:
			return False, 'Fail to Load iSCSI Conf!'
	except:
		return False, 'Fail to Load iSCSI Conf! Some exception raised!'

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
