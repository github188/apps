#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys, commands
import getopt

from libmd import *

disk_long_opt = ['list', 'slot-id=', 'get-detail=',
	'set=', 'type=', 'vg=']


class diskArgs():
	def __init__(self):
		self.list_mode = False
		self.detail_mode = False
		self.slot_id = ''
		self.set_mode = False
		self.slot_list = [] # for --set use
		self.type_set = ''
		self.vg_name = ''

def diskExit(ret = True, msg = ''):
	ret_msg = {'status':True, 'msg':''}
	ret_msg['status'] = ret
	ret_msg['msg'] = msg
	print json.dumps(ret_msg, encoding="utf-8", ensure_ascii=False)
	if ret:
		sys.exit(0)
	sys.exit(-1)

def listORdetailProc(arg = diskArgs()):
	# pass through to us_cmd
	if arg.list_mode:
		cmd_us = "us_cmd disk --list %s" % arg.slot_id
	elif arg.detail_mode:
		os.system("us_cmd disk update %s smart" % arg.slot_id)
		cmd_us = "us_cmd disk --get-detail %s" % arg.slot_id
	sts,output = commands.getstatusoutput(cmd_us)
	if (sts == 0):
		print output;
	else:
		print json.dumps({"total": 0, "rows":[]})
	sys.exit(0)

def diskListProc(arg = diskArgs()):
	if not arg.list_mode:
		return
	listORdetailProc(arg)

def diskDetailProc(arg = diskArgs()):
	if not arg.detail_mode:
		return
	listORdetailProc(arg)

def diskSetProc(arg = diskArgs()):
	if not arg.set_mode:
		return
	f_lock = lock_file(RAID_REBUILD_LOCK)
	if None == f_lock:
		diskExit(False, '系统异常: 文件 %s 加锁失败' % RAID_REBUILD_LOCK)

	for slot in arg.slot_list:
		ret,msg = disk_set_type(slot, arg.type_set, arg.vg_name)
		if ret != True:
			unlock_file(f_lock)
			diskExit(ret, msg)

	unlock_file(f_lock)
	
	# 尝试重建
	for mdattr in get_mdattr_all():
		# 降级 且 没有事件触发重建 时, 执行重建
		if mdattr.raid_state == 'degrade' and mdattr.disk_cnt < mdattr.disk_total:
			if get_md_rebuilder_cnt(basename(mdattr.dev)) > 0:
				continue
			
			md_rebuild(mdattr)

	diskExit(True, '设置磁盘 %s 为%s成功' % (str(arg.slot_list), DISK_TYPE_MAP[arg.type_set]))

def diskUsage():
	print """
disk --list [--slot-id <id>]
     --get-detail <slot_id>
     --set <slot_id>[,<slot_id>...] --type <Special|Global|Free> [--vg <name>]
"""

def disk_main(argv):
	try:
		opts,args = getopt.gnu_getopt(argv, '', disk_long_opt)
	except getopt.GetoptError, e:
		diskExit(False, '%s' % e)

	disk_arg = diskArgs()
	for opt,arg in opts:
		if opt == '--list':
			disk_arg.list_mode = True
		elif opt == '--slot-id':
			disk_arg.slot_id = arg
		elif opt == '--get-detail':
			disk_arg.detail_mode = True
			disk_arg.slot_id = arg
		elif opt == '--set':
			disk_arg.set_mode = True
			disk_arg.slot_list = arg.split(',')
		elif opt == '--type':
			disk_arg.type_set = arg
		elif opt == '--vg':
			disk_arg.vg_name = arg

	diskListProc(disk_arg)
	diskDetailProc(disk_arg)
	diskSetProc(disk_arg)

	diskUsage()

def main():
	disk_main(sys.argv[1:]) 

def usage():
    help_str="""
Usage:
        --list [slot]
        --get-detail <slot>
        --set-spare md_name <slots>
        --set-free <slots>
        info [slot]
        name <slot>
        slot <name>
"""
    #return False,help_str
    print help_str

if __name__ == "__main__":
	disk_main(sys.argv[1:])
