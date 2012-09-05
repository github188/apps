#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
