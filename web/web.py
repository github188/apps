#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys
import os
import getopt
import json
os.chdir(os.path.dirname(sys.argv[0]))

from libweb import *

def DictDump(row_list):
	return row_list

def DefaultDump(row_list):
	rows = []
	for row in row_list:
		rows.append(row.__dict__)
	return rows

class UniOutput:
	def __init__(self, row_list, dump = DefaultDump):
		self.total = 0
		self.rows = []
		self.rows = dump(row_list)
		self.total = len(self.rows)

		print json.dumps(self.__dict__, encoding="utf-8", ensure_ascii=False, sort_keys = False)
		sys.exit(0)

def web_service_exit(ret = True, msg = ''):
	ret_msg = {'status':True, 'msg':''}
	ret_msg['status'] = ret
	ret_msg['msg'] = msg
	print json.dumps(ret_msg, encoding="utf-8", ensure_ascii=False)
	if ret:
		sys.exit(0)
	sys.exit(-1)

def web_service_usage():
	print """
web --create --site-name <name>
    --modify --site-name <name> [--set-doc <document_root>] [--set-idx <index_file>] [--set-port <port number>]
    --remove --site-name <name>
    --default
    --list [--site-name <name>]
"""
	sys.exit(-1)

OP_MODE = ['--create', '--modify', '--remove', '--list', '--remove', '--default']
web_service_long_opt = ['create', 'site-name=', 'modify', 'set-doc=', 'set-idx=', 'set-port=','list', 'remove', 'default']

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', web_service_long_opt)
	except getopt.GetoptError, e:
		web_service_exit(False, '未识别的命令参数：%s' % e)
	arg_op_mode = ''
	site_name = ''
	arg_doc_root= ''
	arg_index_file = ''
	arg_port = ''
	for opt,arg in opts:
		if opt in OP_MODE:
			arg_op_mode = opt
			continue
		if opt == '--site-name':
			site_name = arg 
		elif opt == '--set-doc':
			arg_doc_root = arg
		elif opt == '--set-idx':
			arg_index_file = arg
		elif opt == '--set-port':
			arg_port = arg

	if arg_op_mode == '--list':
		UniOutput(get_web_service_list(site_name))
	elif arg_op_mode == '--create':
		ret,msg = create_web_service(site_name)
		web_service_exit(ret, msg)
	elif arg_op_mode == '--modify':
		ret = True
		msg = ''
		if arg_doc_root != '':
			ret,msg = modify_web_service(site_name, OPT_DOC, arg_doc_root)
			if not ret:
				web_service_exit(ret, msg)
		if ret and arg_index_file != '':
			ret,msg = modify_web_service(site_name, OPT_IDX, arg_index_file)
			if not ret:
				web_service_exit(ret, msg)
		if ret and arg_port != '':
			ret,msg = modify_web_service(site_name, OPT_PORT, arg_port)
			if not ret:
				web_service_exit(ret, msg)
		ret, msg = restart_lighttpd_service()
		if ret:
			web_service_exit(ret, msg)
		web_service_exit(True, "设置站点%s属性成功." % (site_name))
	elif arg_op_mode == '--remove':
		ret,msg = remove_web_service(site_name)
		if not ret:
			web_service_exit(ret, msg)
		ret, msg = restart_lighttpd_service()
		if ret:
			web_service_exit(ret, msg)
		web_service_exit(True, "删除站点%s成功." % (site_name))
	elif arg_op_mode == '--default':
		restore_web_service()
		restart_lighttpd_service()
		sys.exit(0)

	web_service_usage()
	
if __name__ == '__main__':
	main()
