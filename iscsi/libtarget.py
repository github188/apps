#!/usr/bin/env python
# -*- coding: utf-8 -*-

import libiscsicommon

class TargetAttr:
	"""
	Target属性
	"""
	def __init__(self):
		self.NopInInterval = 30
		self.NotInTimeOut = 30
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
	Target对象
	"""
	def __init__(self):
		self.tid = ''
		self.target_name = ''
		self.state = 'disable'
		self.luns = 0
		self.sessions = 0
		self.proto = iSCSI_Protocol()
		self.attr = TargetAttr()
		self.stat = TargetStat()
