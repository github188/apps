#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, commands, json
import getopt
import uuid

from libdisk import *
from libmd import *

def do_create(argv):
	opts = ["name=", "level=", "strip=", "disk="]
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
		elif opt == "--disk":
			disks = arg
	if name == None:
		return False,"未指定名称"
	if level == None:
		return False,"未指定级别"
	if strip == None:
		return False,"未指定条带大小"
	if disks == None:
		return False,"未指定磁盘槽位"
	return md_create(name, level, strip, disks)

def __get_mdname_list():
	mdname_list = []
	try:
		mdinfo_devs = json.loads(md_info())
		for mdinfo in mdinfo_list['rows']:
			mdname_list.append(mdinfo['name'])
	except:
		pass
	return mdname_list

def do_generate_name(suffix):
	if suffix == '':
		return False, '请输入获取卷组名称的前缀!'
	md_list = __get_mdname_list()
	check_max = 10
	while check_max > 0:
		ustr = str(uuid.uuid4()).split('-')
		tstr = suffix + ustr[2]
		if tstr not in md_list:
			return True, tstr
		tstr = suffix + ustr[1]
		if tstr not in md_list:
			return True, tstr
		check_max = check_max - 1
	return False, '无法生成卷组名称!'

def main(argv):
	ret = ""
	if len(argv) < 2:
		usage()

	cmd = argv[1]
	res = ""
	if cmd == "--list":
		if len(argv) >= 3:
			mdname = argv[2]
		else:
			mdname = None
		ret = md_info(mdname)
		json_dump(ret)
		res = None
	elif cmd == "--create":
		res = do_create(argv[2:])
	elif cmd == "--delete":
		if len(argv) < 3:
			usage()
		else:
			mdname = argv[2]
			res = md_del(mdname)
	elif cmd == "--generate-name":
		#suffix = argv[2] if len(argv) == 3 else ''
		res = do_generate_name(argv[2] if len(argv)==3 else '')
	else:
		usage()
	return res;

def usage():
	help_str="""
Usage:
	--create --name=<vg_name> --level=<0|1|5|6> --strip=<64|128|256> --disk='<disk-slot-list>'
	--delete <vg_name>
	--list [vg_name]
	--generate-name <suffix>
"""
	#return False,help_str
	print help_str
	sys.exit(-1)

if __name__ == "__main__":
	res = main(sys.argv)
	debug_status(res)
