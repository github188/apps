#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import commands
import json

reload(sys)
sys.setdefaultencoding('utf8')

class SCST_CONFIG(object):
	"""
	定义SCST相关属性
	"""
	def __init__(self):
		self.ROOT_DIR = '/sys/kernel/scst_tgt'
		self.TARGET_DIR = '%s/targets/iscsi' % self.ROOT_DIR
		self.VDISK_DIR = '%s/handlers/vdisk_blockio' % self.ROOT_DIR

class iSCSI_Protocol:
	"""
	iSCSI协议相关属性定义
	"""

	def __init__(self):

		"""
		HeaderDigest  协议头校验方式
		        None - 无校验（默认）
			CRC32 - 使用CRC32校验（暂不支持）
		"""
		self.HeaderDigest = "None"

		"""
		DataDigest  数据校验方式
		        None - 无校验（默认）
			CRC32 - 使用CRC32校验（暂不支持）
		"""
		self.DataDigest = "None"

		self.ImmediateData = "Yes"
		self.FirstBurstLength = 1024
		self.MaxBurstLength = 4096
		self.InitialR2T = "No"
		self.MaxOutstandingR2T = 16
		self.MaxRecvDataSegmentLength = 1024
		self.MaxXmitDataSegmentLength = 1024

SCST = SCST_CONFIG()

# 公用函数
def AttrRead(dir_path, attr_name):
	value = ''
	full_path = dir_path + os.sep + attr_name
	try:
		f = open(full_path)
		value = f.readline()
	except IOError, e:
		value = e
	else:
		f.close()
	return value.strip()

def AttrWrite(dir_path, attr_name, value):
	full_path = dir_path + os.sep + attr_name
	try:
		f = open(full_path, 'w')
		f.write(value)
		f.close()
	except IOError,e:
		err_msg = e
		print err_msg
		return False
	else:
		return True

def getDirList(file_path):
	dir_list = []
	try:
		for td in os.listdir(file_path):
			if os.path.isdir(file_path + os.sep + td):
				dir_list.append(td)
	except IOError,e:
		err_msg = e
	finally:
		return dir_list

def getISCSIProto(tgt_name):
	tgt_full_path = SCST.ROOT_DIR + '/targets/iscsi/' + tgt_name
	proto = iSCSI_Protocol()
	proto.HeaderDigest = AttrRead(tgt_full_path, 'HeaderDigest')
	proto.DataDigest = AttrRead(tgt_full_path, 'DataDigest')
	proto.ImmediateData = AttrRead(tgt_full_path, 'ImmediateData')
	proto.FirstBurstLength = int(AttrRead(tgt_full_path, 'FirstBurstLength'))
	proto.MaxBurstLength = int(AttrRead(tgt_full_path, 'MaxBurstLength'))
	proto.InitialR2T = AttrRead(tgt_full_path, 'InitialR2T')
	proto.MaxOutstandingR2T = int(AttrRead(tgt_full_path, 'MaxOutstandingR2T'))
	proto.MaxRecvDataSegmentLength = int(AttrRead(tgt_full_path, 'MaxRecvDataSegmentLength'))
	proto.MaxXmitDataSegmentLength = int(AttrRead(tgt_full_path, 'MaxXmitDataSegmentLength'))
	return proto

def iscsiExit(ret = True, msg = ''):
	ret_msg = {'status':True, 'msg':''}
	ret_msg['status'] = ret
	ret_msg['msg'] = msg
	print json.dumps(ret_msg, encoding="UTF-8", ensure_ascii=False, indent=-1)
	if ret:
		sys.exit(0)
	sys.exit(-1)

if __name__ == "__main__":
	"""
	ss = AttrRead('/sys/kernel/scst_tgt/targets/iscsi/iqn.2012-abc', 'io_grouping_type')
	print ss
	xx = AttrWrite('/sys/kernel/scst_tgt/targets/iscsi/iqn.2012-abc/io_grouping_type', 'auto')
	print xx
	"""

	print 'udv2: ', getUdvDevByName('udv2')
	print '/dev/sdg1: ', getUdvNameByDev('/dev/sdg1')

	iscsiExit(True, '错误信息')
