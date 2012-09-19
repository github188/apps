#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, commands
import getopt

from libdisk import *
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
	print json.dumps(ret_msg, encoding="UTF-8", ensure_ascii=False)
	if ret:
		sys.exit(0)
	sys.exit(-1)

def listORdetailProc(arg = diskArgs()):
	# pass through to us_cmd
	if arg.list_mode:
		cmd_us = "us_cmd disk --list %s" % arg.slot_id
	elif arg.detail_mode:
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
	if arg.type_set != 'free':
		diskExit(False, '目前暂不支持此操作!')

	ret,msg = set_slots_free(arg.slot_list)
	diskExit(ret, msg)

def diskUsage():
	print """
disk --list [--slot-id <id>]
     --get-detail <slot_id>
     --set <slot_id>[,<slot_id>...] --type <special-spare|global-spare|free> [--vg <name>]
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
			disk_arg.slot_list.append(arg)
		elif opt == '--type':
			disk_arg.type_set = arg
		elif opt == '--vg':
			disk_arg.vg_name = arg
	if disk_arg.set_mode:
		disk_arg.slot_list = disk_arg.slot_list + args

	diskListProc(disk_arg)
	diskDetailProc(disk_arg)
	diskSetProc(disk_arg)

	diskUsage()


"""
#argv: namd opt <slot>
def main(argv):
    if len(argv) < 2:
        return usage()

    cmd = argv[1]
    if cmd == "info":
        cmd = "--list"
        argv[1] = cmd
    res = ""

    if cmd == "--list" or cmd == "name" or cmd == "slot" or cmd == "--get-detail":
        # pass through to us_cmd
        cmd_us = "us_cmd disk " + " ".join(argv[1:])
        sts,output = commands.getstatusoutput(cmd_us)
        res = None
        if (sts == 0):
            print output;
        else:
            print json.dumps({"total": 0, "rows":[]})
            #是否需要返回错误信息
        #else:
        #res = output;
    elif cmd == "--set-spare" :
        if len(argv) < 4:
            usage()
        mdname = argv[2];
        slots = argv[3];
        res = set_spare(mdname, slots)
    elif cmd == "--set-free":
        if (len(argv)) < 3:
            usage()
	slots = argv[2:]
        res = set_slots_free(slots)
    else:
        res = usage()
    return res
"""

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
	#res = main(sys.argv)
	#debug_status(res)
	disk_main(sys.argv[1:])
