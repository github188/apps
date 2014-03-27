#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys
import os
import re

os.chdir(os.path.dirname(sys.argv[0]))

from libnetwork import *

class IArgs:
	def __init__(self):
		self.mode = ''
		self.list_set = False
		self.default_set = False
		self.ifconfig_set = False
		self.bond_set = False
		self.dns_set = False
		self.status_set = False
		self.val_set = ''
		self.iface_set = ''
		self.intbond_set = False
		self.default_gw_set = False
		self.ip_set = ''
		self.ip_state = False
		self.mask_set = ''
		self.mask_state = False
		self.gw_set = ''
		self.gw_state = False
		self.niccoun_set = False
		self.nic_set = ''
		self.nic_state = False
		self.remove_set = False
		self.dhcp_set = False
		self.mode_set = '1'
		self.filter_set = False

	def setMode(self, mode):
		if self.mode == '':
			self.mode = mode

OP_MODE = ['--list', '--ifconfig', '--bond', '--dns', '--default', '--niccoun', '--status']
long_opt = ['list', 'filter', 'ifconfig', 'bond', 'dns', 'default', 'status', 'iface=', 'dhcp', 'ip=', 'mask=', 'gw=', 'nic=', 'mode=', 'val=', 'remove', 'intbond', 'niccoun', 'default_gw']

ipre_str = r'^([1]?\d\d?|2[0-4]\d|25[0-5])\.([1]?\d\d?|2[0-4]\d|25[0-5])\.([1]?\d\d?|2[0-4]\d|25[0-5])\.([1]?\d\d?|2[0-4]\d|25[0-4])$'

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', long_opt)
	except getopt.GetoptError, e:
		AUsage(e)

	iArgs = IArgs()
	for opt,arg in opts:
		if opt in OP_MODE:
			iArgs.setMode(opt)

		if opt == '--list':
			iArgs.list_set = True
		elif opt == '--ifconfig':
			iArgs.ifconfig_set = True
		elif opt == '--bond':
			iArgs.bond_set = True
		elif opt == '--dns':
			iArgs.dns_set = True
		elif opt == '--status':
			iArgs.status_set = True
		elif opt == '--val':
			iArgs.val_set = arg
		elif opt == '--iface':
			iArgs.iface_set = arg
		elif opt == '--dhcp':
			iArgs.dhcp_set = True
		elif opt == '--ip':
			if not re.match(ipre_str, arg):
				Export(False, 'ip地址格式不正确')
				sys.exit(-1)
			iArgs.ip_set = arg
			iArgs.ip_state = True
		elif opt == '--mask':
			if not re.match(r'^(254|252|248|240|224|192|128|0)\.0\.0\.0$|^(255\.(254|252|248|240|224|192|128|0)\.0\.0)$|^(255\.255\.(254|252|248|240|224|192|128|0)\.0)$|^(255\.255\.255\.(254|252|248|240|224|192|128|0))$', arg):
				Export(False, '子网掩码格式不正确,末尾输入范围应该为：254|252|248|240|224|192|128|0')
				sys.exit(-1)
			iArgs.mask_set = arg
			iArgs.mask_state = True
		elif opt == '--gw':
			if not re.match(ipre_str, arg):
				Export(False, '网关地址格式不正确')
				sys.exit(-1)
			iArgs.gw_set = arg
			iArgs.gw_state = True
		elif opt == '--mode':
			iArgs.mode_set = arg
		elif opt == '--nic':
			iArgs.nic_set = arg
			iArgs.nic_state = True
		elif opt == '--remove':
			iArgs.remove_set = True
		elif opt == '--intbond':
			iArgs.intbond_set = True
		elif opt == '--niccoun':
			iArgs.niccoun_set = True
		elif opt == '--filter':
			iArgs.filter_set = True
		elif opt == '--default':
			iArgs.default_set = True
		elif opt == '--default_gw':
			iArgs.default_gw_set = True

	if iArgs.gw_set != "":
		Gw_Check(iArgs)

	if iArgs.list_set == True:
		NIC_List(iArgs)			##输出网络列表
	elif iArgs.default_set == True:
		Default(iArgs.iface_set)			##恢复默认
	elif iArgs.niccoun_set == True:
		NIC_INT_Count()			##网络接口数量
	elif iArgs.ifconfig_set == True:
		NIC_Set(iArgs) 			##IP设置
	elif iArgs.bond_set == True:
		BOND_Set(iArgs) 		##BOND接口设置
	elif iArgs.dns_set == True:
		DNS_Set(iArgs)			##DNS设置
	elif iArgs.status_set == True:
		NIC_Status_List()
	else:
		AUsage()

if __name__ == '__main__':
	main()

