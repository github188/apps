#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys, commands, json
import getopt
import uuid
import time

from libmd import *

reload(sys)
sys.setdefaultencoding('utf-8')

def do_create(argv):
	opts = ["name=", "level=", "strip=", "disks="]
	try:
		pair = getopt.getopt(argv, '', opts)
	except:
		return False,"参数非法"

	name = None
	level = None
	strip = None
	disks = None
	for opt,arg in pair[0]:
		if opt == "--name":
			name = arg
		elif opt == "--level":
			level = arg
		elif opt == "--strip":
			strip = arg
		elif opt == "--disks":
			disks = arg
	if name == None:
		return False,"未指定名称"
	if level == None:
		return False,"未指定级别"
	if strip == None:
		return False,"未指定条带大小"
	if disks == None:
		return False,"未指定磁盘槽位"
	return md_create(name, level, strip, disks.replace(',', ' '))

def do_expand(argv):
	opts = ["name=", "disks="]
	try:
		pair = getopt.getopt(argv, '', opts)
	except:
		return False,"参数非法"
	
	name = None
	disks = None
	for opt,arg in pair[0]:
		if opt == "--name":
			name = arg
		elif opt == "--disks":
			disks = arg
	if name == None:
		return False,"未指定名称"
	if disks == None:
		return False,"未指定磁盘槽位"
	return md_expand(name, disks.replace(',', ' '))

def do_generate_name(suffix):
	if suffix == '':
		return False, '请输入获取卷组名称的前缀'
	rname_list = raid_name_list()
	check_max = 10
	while check_max > 0:
		ustr = str(uuid.uuid4()).split('-')
		tstr = suffix + ustr[2]
		if tstr not in rname_list:
			return True, tstr
		tstr = suffix + ustr[1]
		if tstr not in rname_list:
			return True, tstr
		check_max = check_max - 1
	return False, '无法生成卷组名称'

def do_duplicate_check(raid_name):
	if raid_name == '':
		return False, '请输入卷组名称'
	if raid_name in raid_name_list():
		return True, '卷组 %s 已经存在' % raid_name
	return False, '卷组 %s 不存在' % raid_name

SYNC_PRIO_CONF = CONF_ROOT_DIR + '/disk/sync_prio'
def do_set_sync_prio(prio = ''):
	prio_dict = {'high':'20000', 'middle':'10000', 'low':'1000'}
	if not prio_dict.has_key(prio):
		return False, '参数输入错误'

	fs_attr_write(SYNC_PRIO_CONF, prio_dict[prio])

	if fs_attr_write('/proc/sys/dev/raid/speed_limit_min', prio_dict[prio]):
		return True, '设置卷组初始化/重建优先级为 %s 成功' % prio
	else:
		return False, '设置卷组初始化/重建优先级为 %s 失败' % prio

def do_get_sync_prio():
	val = fs_attr_read('/proc/sys/dev/raid/speed_limit_min')
	if not val.isdigit():
		return True,''
	
	speed_limit_min = int(val)
	if speed_limit_min >= 20000:
		prio = 'high'
	elif speed_limit_min >= 10000:
		prio = 'middle'
	else:
		prio = 'low'
	
	return True, prio

def do_load_sync_prio():
	val = fs_attr_read(SYNC_PRIO_CONF)
	if not val.isdigit():
		return False,'读取初始化/重建优先级配置失败, 使用系统默认值'

	if fs_attr_write('/proc/sys/dev/raid/speed_limit_min', val):
		return True, '载入卷组初始化/重建优先级配置成功'
	else:
		return False, '载入卷组初始化/重建优先级配置失败'

def vg_main(argv):
	ret = ""
	if len(argv) < 2:
		usage()

	cmd = argv[1]
	res = ""
	if cmd == "--list":
		mdattr_output = []
		if len(argv) == 4:
			if argv[2] == '--vg':
				raid_name = argv[3]
				mdattr = get_mdattr_by_name(raid_name)
				if mdattr != None:
					mdattr_output.append(mdattr.__dict__)

			elif argv[2] == '--level':
				level_list = argv[3].upper().split(',')
				for mdattr in get_mdattr_all():
					if mdattr.raid_level in level_list:
						mdattr_output.append(mdattr.__dict__)

		elif len(argv) == 3 :
			if argv[2] == '--not-fail':
				for mdattr in get_mdattr_all():
					if mdattr.raid_state != 'fail':
						mdattr_output.append(mdattr.__dict__)
			elif argv[2] == '--expandable':
				for mdattr in get_mdattr_all():
					if mdattr.raid_state == 'normal' and mdattr.raid_level in ('5', '6'):
						mdattr_output.append(mdattr.__dict__)

		else:
			for mdattr in get_mdattr_all():
				mdattr_output.append(mdattr.__dict__)

		json_dump({"total": len(mdattr_output), "rows": mdattr_output})
		res = None
	elif cmd == "--create":
		res = do_create(argv[2:])
	elif cmd == "--expand":
		res = do_expand(argv[2:])
	elif cmd == "--delete":
		if len(argv) < 3:
			usage()
		else:
			raid_name = argv[2]
			res = md_del(raid_name)
	elif cmd == "--generate-name":
		res = do_generate_name(argv[2] if len(argv)==3 else '')
	elif cmd == "--duplicate-check":
		res = do_duplicate_check(argv[2] if len(argv)==3 else '')
	elif cmd == "--set-sync-prio":
		res = do_set_sync_prio(argv[2] if len(argv)==3 else '')
	elif cmd == "--get-sync-prio":
		res = do_get_sync_prio()
	elif cmd == "--load-sync-prio":
		res = do_load_sync_prio()
	else:
		usage()
	return res;

def main():
	res = vg_main(sys.argv)
	debug_status(res)

def usage():
	help_str="""
Usage:
	--create --name <vg_name> --level <0|1|5|6> --strip <64|128|256|512|1024> --disk <slot1>[,<slot2>,<slot3>...]
	--expand --name <vg_name> --disk <slot1>[,<slot2>,<slot3>...]
	--delete <vg_name>
	--list [--vg <vg_name> | --level <level1>[,<level2>,<level3>... | --not-fail | --expandable]
	--generate-name <suffix>
	--duplicate-check <vg_name>
	--set-sync-prio low|middle|high
	--get-sync-prio
	--load-sync-prio
"""
	#return False,help_str
	print help_str
	sys.exit(-1)

if __name__ == "__main__":
	res = main(sys.argv)
	debug_status(res)
