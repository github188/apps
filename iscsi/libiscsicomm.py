#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import commands
import json

from libcommon import *

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
		self.CFG_DIR = CONF_ROOT_DIR + '/iscsi'
		self.CFG = self.CFG_DIR + '/scst.conf'
		os.makedirs(self.CFG_DIR) if not os.path.isdir(self.CFG_DIR) else None

SCST = SCST_CONFIG()

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
		self.IncomingChap = "disable"

def _iscsi_find_incoming(tgt_path):
	chap_switch = 'disable'
	try:
		for x in os.listdir(tgt_path):
			if x.find('IncomingUser') == 0:
				chap_switch = 'enable'
				break
	except:
		pass
	return chap_switch

def getISCSIProto(tgt_name):
	tgt_full_path = SCST.ROOT_DIR + '/targets/iscsi/' + tgt_name
	proto = iSCSI_Protocol()
	proto.HeaderDigest = fs_attr_read(tgt_full_path + '/HeaderDigest')
	proto.DataDigest = fs_attr_read(tgt_full_path + '/DataDigest')
	proto.ImmediateData = fs_attr_read(tgt_full_path + '/ImmediateData')
	
	val = fs_attr_read(tgt_full_path + '/FirstBurstLength')
	if val != '' and val.isdigit():
		proto.FirstBurstLength = int(val)

	val = fs_attr_read(tgt_full_path + '/MaxBurstLength')
	if val != '' and val.isdigit():
		proto.MaxBurstLength = int(val)

	proto.InitialR2T = fs_attr_read(tgt_full_path + '/InitialR2T')

	val = fs_attr_read(tgt_full_path + '/MaxOutstandingR2T')
	if val != '' and val.isdigit():
		proto.MaxOutstandingR2T = int(val)

	val = fs_attr_read(tgt_full_path + '/MaxRecvDataSegmentLength')
	if val != '' and val.isdigit():
		proto.MaxRecvDataSegmentLength = int(val)

	val = fs_attr_read(tgt_full_path + '/MaxXmitDataSegmentLength')
	if val != '' and val.isdigit():
		proto.MaxXmitDataSegmentLength = int(val)

	proto.IncomingChap = _iscsi_find_incoming(tgt_full_path)
	return proto

if __name__ == "__main__":
	sys.exit(0)
