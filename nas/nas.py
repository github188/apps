#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys
import os
import getopt
import json

from libcommon import *
from libnas import *

def usage():
	print """
nas --list [--volume <name>] [--state formatting|mounted|all] [--not-fail]
    --map --udv <name> [--filesystem xfs|ext3|ext4] [--mount-point <dir>]
    --unmap --volume <name>
    --misc --update-cfg
    --misc --restore-cfg
"""
	sys.exit(-1)

OP_MODE = ['--list', '--map', '--unmap', '--misc']
nas_long_opt = ['list', 'volume=', 'state=', 'not-fail', 'map', 'udv=', 'unmap', 'filesystem=', 'mount-point=', 'misc', 'update-cfg', 'restore-cfg']

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', nas_long_opt)
	except getopt.GetoptError, e:
		comm_exit(False, '未识别的命令参数: %s' % e)

	arg_op_mode = ''
	arg_volume = ''
	arg_state = 'all'
	arg_udv = ''
	arg_fs = 'ext4'
	arg_mount_point = ''
	arg_update = False
	arg_restore = False
	arg_not_fail = False
	for opt,arg in opts:
		if opt in OP_MODE:
			arg_op_mode = opt
			continue
		if opt == '--volume':
			arg_volume = arg
		elif opt == '--state':
			arg_state = arg
		elif opt == '--udv':
			arg_udv = arg
		elif opt == '--filesystem':
			arg_fs = arg
		elif opt == '--mount-point':
			arg_mount_point = arg
		elif opt == '--update-cfg':
			arg_update = True
		elif opt == '--restore-cfg':
			arg_restore = True
		elif opt == '--not-fail':
			arg_not_fail = True

	if arg_op_mode == '--list':
		CommOutput(get_nasvol_list(arg_volume, arg_state, arg_not_fail))
	elif arg_op_mode == '--map':
		ret,msg = nas_vol_add(arg_udv, '', arg_fs, arg_mount_point)
		log_insert('NAS', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)
	elif arg_op_mode == '--unmap':
		ret,msg = nas_vol_remove(arg_volume)
		log_insert('NAS', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)
	elif arg_op_mode == '--misc':
		if arg_update:
			comm_exit(False, 'not support')
		elif arg_restore:
			ret,msg = nas_conf_load()
			comm_exit(ret, msg)

	usage()

if __name__ == '__main__':
	main()
