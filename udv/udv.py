#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, json
import getopt

from libnas import is_nasvolume
from libudv import *

reload(sys)
sys.setdefaultencoding('utf-8')

class UdvInfo:
	def __init__(self):
		self.name = ''
		self.capacity = 0
		self.state = 'raw'
		self.vg = ''
		self.combin = ''
		self.dev = ''

def udv_list(udvargs):
	udvinfo_list = []
	finished = False
	
	if not udvargs.raw_set and not udvargs.iscsi_set and not udvargs.nas_set:
		udvargs.raw_set = udvargs.iscsi_set = udvargs.nas_set = True
	
	for mdattr in get_mdattr_all():
		if mdattr.raid_state == 'fail':
			continue
		
		if not udvargs.name_set and udvargs.vg_set:
			if mdattr.name == udvargs.vg_str:
				finished = True
			else:
				continue

		md = basename(mdattr.dev)
		sysdir_md = '/sys/block/' + md
		for entry in list_child_dir(sysdir_md):
			if entry[:len(md)] != md:
				continue
		
			sysdir_part = sysdir_md + os.sep + entry
			udvinfo = UdvInfo()
			udvinfo.vg = mdattr.name
			udvinfo.dev = '/dev/' + entry
		
			udvinfo.name = fs_attr_read(sysdir_part + '/volname')
			val = fs_attr_read(sysdir_part + '/size')
			if val.isdigit():
				udvinfo.capacity = int(val)*512
			
			udvinfo.combin = udvinfo.name + '|' + str(udvinfo.capacity)
			
			if get_iscsivolname_bydev(udvinfo.dev) != '':
				udvinfo.state = 'iscsi'
			elif is_nasvolume(udvinfo.name):
				udvinfo.state = 'nas'
			
			if udvargs.name_set:
				if udvargs.name_str != udvinfo.name:
					continue
				else:
					udvinfo_list.append(udvinfo)
					finished = True
					break
			else:
				if not udvargs.raw_set and 'raw' == udvinfo.state:
					continue
				elif not udvargs.iscsi_set and 'iscsi' == udvinfo.state:
					continue
				elif not udvargs.nas_set and 'nas' == udvinfo.state:
					continue
			
			udvinfo_list.append(udvinfo)
		
		if finished:
			break

	CommOutput(udvinfo_list)

def output_dev_byudvname(udvargs):
	part_name = udvargs.get_dev_byname_str
	part_dev = get_dev_byudvname(part_name)
	if '' == part_dev:
		comm_exit(False, '用户数据卷不存在')
	
	print '{"status":true,"udv_name":"%s","udv_dev":"%s"}' % (part_name, part_dev)
	sys.exit(0)

def output_udvname_bydev(udvargs):
	part_dev = udvargs.get_name_bydev_str
	if '' == part_dev or os.system('[ -b %s ]' % part_dev) != 0:
		comm_exit(False, part_dev + '不是分区设备文件')
	
	part_name = get_udvname_bydev(part_dev)
	print '{"status":true,"udv_name":"%s","udv_dev":"%s"}' % (part_name, part_dev)
	sys.exit(0)

def duplicate_check(udvargs):
	part_name = udvargs.duplicate_check_str
	part_dev = get_dev_byudvname(part_name)
	if '' == part_dev:
		print '{"udv_name":"%s","duplicate":false}' % part_name
	else:
		print '{"udv_name":"%s","duplicate":true}' % part_name
	sys.exit(0)

class UdvArgs:
	def __init__(self):
		self.mode = ''
		self.list_set = False
		self.get_dev_byname_set = False
		self.get_dev_byname_str = ''
		self.get_name_bydev_set = False
		self.get_name_bydev_str = ''
		self.duplicate_check_set = False
		self.duplicate_check_str = ''
		self.raw_set = False
		self.iscsi_set = False
		self.nas_set = False
		self.name_set = False
		self.name_str = ''
		self.vg_set = False
		self.vg_str = ''
		
	
	def setMode(self, mode):
		if self.mode == '':
			self.mode = mode

def udv_usage():
	print """
udv:   --list [[--raw | --iscsi | --nas] | --name <udv_name>] [--vg <vg_name>]
       --get-dev-byname <name>
       --get-name-bydev <dev>
       --duplicate-check <udv_name>
"""
	sys.exit(-1)

OP_MODE = ['--list', '--get-dev-byname', '--get-name-bydev', '--duplicate-check']

udv_long_opt = ['list', 'raw', 'iscsi', 'nas', 'name=', 'vg=',
			'get-dev-byname=', 'get-name-bydev=', 'duplicate-check=']

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', udv_long_opt)
	except getopt.GetoptError, e:
		comm_exit(False, '%s' % e)

	udvargs = UdvArgs()
	for opt,arg in opts:
		# mode set
		if opt in OP_MODE:
			udvargs.setMode(opt)

		# args proc
		if opt == '--list':
			udvargs.list_set = True
		elif opt == '--raw':
			udvargs.raw_set = True
		elif opt == '--iscsi':
			udvargs.iscsi_set = True
		elif opt == '--nas':
			udvargs.nas_set = True
		elif opt == '--name':
			udvargs.name_set = True
			udvargs.name_str = arg
		elif opt == '--vg':
			udvargs.vg_set = True
			udvargs.vg_str = arg
		elif opt == '--get-dev-byname':
			udvargs.get_dev_byname_set = True
			udvargs.get_dev_byname_str = arg
		elif opt == '--get-name-bydev':
			udvargs.get_name_bydev_set = True
			udvargs.get_name_bydev_str = arg
		elif opt == '--duplicate-check':
			udvargs.duplicate_check_set = True
			udvargs.duplicate_check_str = arg

	if '--list' == udvargs.mode:
		udv_list(udvargs)
	elif '--get-dev-byname' == udvargs.mode:
		output_dev_byudvname(udvargs)
	elif '--get-name-bydev' == udvargs.mode:
		output_udvname_bydev(udvargs)
	elif '--duplicate-check' == udvargs.mode:
		duplicate_check(udvargs)
	else:
		udv_usage()

if __name__ == "__main__":
	main()
