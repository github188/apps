#!/usr/bin/env python
# -*- coding: utf-8 -*-

class SCST_CONFIG(object):
	"""
	定义SCST相关属性
	"""
	def __init__(self):
		self.ROOT_DIR = '/sys/kernel/scst_tgt'
		self.TARGET_DIR = '%s/target/iscsi' % self.ROOT_DIR
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

		self.ImmediateDate = "Yes"
		self.FristBurstLength = 1024
		self.MaxBurstLength = 4096
		self.InitialR2T = "No"
		self.MaxOutStandingR2T = 16
		self.MaxRecvDataSegmentLength = 1024
		self.MaxXmitDataSegmentLength = 1024

GlobalConfig = SCST_CONFIG()

if __name__ == "__main__":
	print GlobalConfig.ROOT_DIR
	print GlobalConfig.TARGET_DIR
	print GlobalConfig.VDISK_DIR
	print GlobalConfig.__dict__
	print GlobalConfig.__doc__
	print GlobalConfig.__module__
	print GlobalConfig.__class__
