#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import getopt
import json

from libiscsitarget import *
from libiscsivolume import *
from libiscsilun import *
from libiscsisession import *
from libiscsichap import *

class iSCSIArgs:
	def __init__(self):
		self.mode = ''
		self.list_set = False
		self.target_name_set = False
		self.target_name_str = ''
		self.modify_set = False
		self.attr_set = False
		self.attr_str = ''
		self.value_set = False
		self.value_str = ''
		self.add_set = False
		self.remove_set = False
		self.remove_str = ''
		self.name_set = False
		self.name_str = ''
		self.detail_set = False
		self.detail_set = ''
		self.udv_set = False
		self.udv_str = ''
		self.blocksize_set = False
		self.blocksize_str = ''
		self.lun_read_only_set = False
		self.lun_read_only_str = ''
		self.read_only_set = False
		self.read_only_str = ''
		self.wrth_str = 'wb'
		self.nv_cache_set = False
		self.nv_cache_str = ''
		self.map_set = False
		self.unmap_set = False
		self.lun_set = False
		self.lun_id_set = False
		self.lun_id_str = ''
		self.initor = '*'
		self.cur_initor = None
		self.fre_initor = None	# 修改LUN映射使用
		self.volume_name_set = False
		self.volume_name_str = ''
		self.udv_set = False
		self.udv_str = ''
		self.force_close_sid = None
		self.get_privilage_set = False
		self.update_cfg = False
		self.restore_cfg = True
		self.default_target = False
		self.chap_user_str = ''
		self.chap_pass_str = ''
		self.chap_set_str = ''	# enable, disable
		self.chap_type = ''	# incoming, outgoing
		self.chap_dup = False

	def setMode(self, mode):
		if self.mode == '':
			self.mode = mode

def DictDump(row_list):
	return row_list

# 处理Target相关参数
def iscsiTargetProc(args = iSCSIArgs()):
	if args.list_set:
		CommOutput(iSCSIGetTargetList(args.target_name_str))
	elif args.modify_set:
		if args.name_str == '':
			comm_exit(False, '请输入被操作的Target名称!')
		elif args.attr_str == '':
			comm_exit(False, '请输入设置的属性名称!')
		elif args.value_str == '':
			comm_exit(False, '请输入设置的属性取值!')
		else:
			ret,msg = iSCSISetTargetAttr(args.name_str, args.attr_str, args.value_str)
			log_insert('NAS', 'Auto', 'Info' if ret else 'Error', msg)
			comm_exit(ret, msg)
	elif args.add_set:
		comm_exit(False, '暂不支持添加Target操作!')
	elif args.remove_set:
		comm_exit(False, '暂不支持删除Target操作!')
	else:
		comm_exit(False, '缺少参数!')
	return

def iscsiAddVolume(args = iSCSIArgs()):
	if not len(args.udv_str):
		comm_exit(False, '请输入UDV名称!')
	try:
		blocksize = 512
		if len(args.blocksize_str):
			blocksize = int(args.blocksize_str)

		read_only = 'disable'
		if len(args.read_only_str):
			read_only = args.read_only_str
	except:
		pass

	return iSCSIVolumeAdd(args.udv_str, blocksize, read_only, args.wrth_str)

# 处理数据卷相关参数
def iscsiVolumeProc(args = iSCSIArgs()):
	if args.list_set:
		CommOutput(iSCSIVolumeGetList(args.volume_name_str, args.udv_str))
	elif args.add_set:
		ret,msg = iscsiAddVolume(args) 
		log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)
	elif args.remove_set:
		if not len(args.remove_str):
			comm_exit(False, '请设置需要删除的iSCSI数据卷名称!')
		else:
			ret,msg = iSCSIVolumeRemove(args.remove_str)
			log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
			comm_exit(ret, msg)
	else:
		comm_exit(False, '缺少参数!')

# 处理LUN相关参数
def iscsiLunProc(args = iSCSIArgs()):
	if args.list_set:
		if len(args.lun_id_str):
			comm_exit(False, '暂不支持获取指定LUN ID信息！')
		CommOutput(iSCSILunGetList(args.target_name_str), DictDump)

	elif args.map_set:
		if not len(args.target_name_str):
			comm_exit(False, '请输入Target名称!')
		elif not args.add_set and not len(args.volume_name_str):
			comm_exit(False, '请输入iSCSI数据卷名称!')
		elif not len(args.lun_id_str):
			comm_exit(False, '请输入LUN ID!')
		elif not len(args.lun_read_only_str):
			comm_exit(False, '请输入读写属性!')

		# check if add volume
		if args.add_set:
			ret,msg = iscsiAddVolume(args) 
			if not ret:
				log_insert('iSCSI', 'Auto', 'Error', msg)
				comm_exit(ret, msg)
			volume_name = getVolumeByUdv(args.udv_str)
			if not volume_name:
				comm_exit(False, '无法获取iSCSI数据卷名称!')
			args.volume_name_str = volume_name
		
		ret,msg = iSCSILunMap(args.target_name_str, args.volume_name_str,
				args.lun_id_str, args.lun_read_only_str, args.initor)
		if ret == False and args.add_set:
			iSCSIVolumeRemove(volume_name)
		log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)

	elif args.modify_set:
		ret,msg = iSCSILunModify(args.target_name_str, args.lun_id_str, args.cur_initor, args.fre_initor)
		log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)

	elif args.unmap_set:
		if not len(args.target_name_str):
			comm_exit(False, '请输入Target名称!')
		elif not len(args.lun_id_str):
			comm_exit(False, '请输入LUN ID!')
		try:
			ret,msg = iSCSILunUnmap(args.target_name_str, int(args.lun_id_str), args.initor)
			log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
			comm_exit(ret, msg)
		except:
			sys.exit(-1)

	elif args.get_privilage_set:
		if not len(args.udv_str):
			comm_exit(False, '请输入需要查询的用户数据卷名称')
		priv = iSCSILunGetPrivilage(args.udv_str)
		if priv != {}:
			print json.dumps(priv)
			sys.exit(0)
		else:
			comm_exit(False, '用户数据卷 %s 不是iscsi卷！' % args.udv_str)

	else:
		comm_exit(False, '缺少参数!')

# 处理Session相关参数
def iscsiSessionProc(args = iSCSIArgs()):
	if args.list_set:
		if args.target_name_set:
			CommOutput(iSCSIGetSessionList(args.target_name_str))
		else:
			CommOutput(iSCSIGetSessionList())

	if args.force_close_sid != None:
		ret,msg = iSCSIDeleteSession(args.force_close_sid)
		comm_exit(ret, msg)
	comm_exit(False, '请输入正确的session操作!')

def iscsiMiscProc(args = iSCSIArgs()):
	if args.update_cfg:
		ret = iSCSIUpdateCFG()
		comm_exit(ret, '更新配置文件%s' % '成功' if ret else '失败')
	if args.restore_cfg:
		ret,msg = iSCSIRestoreCFG()
		comm_exit(ret,msg)
	if args.default_target:
		ret = iSCSISetDefaultTarget()
		comm_exit(ret, '')

def iscsiChapProc(args = iSCSIArgs()):
	if not args.list_set and args.chap_type != 'incoming' and args.chap_type != 'outgoing':
		comm_exit(False, '请设置正确的CHAP认证方向(incoming 或者 outgoing)!')
	# chap add user
	if args.add_set:
		ret,msg = iSCSIChapAddUser(args.target_name_str, args.chap_user_str, args.chap_pass_str)
		log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)
	# chap remove user
	if args.remove_set:
		ret,msg = iSCSIChapRemoveUser(args.target_name_str, args.remove_str)
		log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)
	
	# chap dup
	if args.chap_dup:
		dup_ret = {}
		dup_ret['user'] = args.chap_user_str
		if iSCSIChapUserExist(args.target_name_str, args.chap_user_str):
			dup_ret['duplicate'] = True
		else:
			dup_ret['duplicate'] = False
		print json.dumps(dup_ret)
		sys.exit(0)

	# chap set user
	if args.chap_set_str == 'enable':
		if args.chap_user_str != '':
			ret,msg = iSCSIChapEnableUser(args.target_name_str, args.chap_user_str)
		else:
			ret,msg = iSCSIChapEnable(args.target_name_str)
		log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)
	elif args.chap_set_str == 'disable':
		if args.chap_user_str != '':
			ret,msg = iSCSIChapDisableUser(args.target_name_str, args.chap_user_str)
		else:
			ret,msg = iSCSIChapDisable(args.target_name_str)
		log_insert('iSCSI', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)
	# chap list
	if args.list_set:
		CommOutput(iSCSIChapList(args.target_name_str))
	comm_exit(False, '请输入正确的CHAP操作参数!')
	return

def iscsiUsage():
	print """
iscsi --target --list [--target-name <name>]
      --target --modify --name <name> --attribute <key> --value <value>
      --target --add --name <name>
      --target --remove <name>

      --volume --list [--volume-name <name> | --udv <name>]
      --volume --add --udv <name> [--blocksize <size> --read-only <enable|disable> --wr-method <wb|wt>]
      --volume --remove <volume_name>

      --lun --list [--target-name <name> [--lun-id <id>]]
      --lun --map --target-name <name> --volume-name <name> --lun-id <id|auto> --lun-read-only <enable|disable|auto> [--initiator <name>]
      --lun --map --target-name <name> --add --udv <name> [--block-size <size> --wr-method <wb|wt>] --lun-id <id|auto> --lun-read-only <enable|disable|auto> [--initiator <name>]
      --lun --modify --target-name <name> --current-initiator <name> --lun-id <id> --fresh-initiator <name>
      --lun --unmap --target-name <target_name> --lun-id <id> [--initiator <name>]
      --lun --get-privilage --udv <name>

      --session --list [--target-name <name>]
      --session --force-close <session_id>

      --chap --target-name <name> --incoming --add --user <name> --pass <word>
      --chap --target-name <name> --incoming --remove <name>
      --chap --target-name <name> --incoming --set <enable|disable> [--user <name>]
      --chap --target-name <name> --incoming --duplicate-check --user <name>
      --chap --list [--target-name <name>]

      --misc --update-cfg
      --misc --restore-cfg
      --misc --check-default-target
"""
	sys.exit(-1)


OP_MODE = ['--target', '--volume', '--lun', '--session', '--chap', '--misc']

iscsi_long_opt = ['target', 'list', 'target-name=',
	'modify', 'attribute=', 'value=',
	'add', 'remove=', 'name=', 'get-detail=',
	'volume', 'udv=', 'block-size=', 'read-only=', 'nv-cache=',
	'lun', 'map', 'lun-id=', 'unmap', 'get-privilage', 'target-name=',
	'session', 'volume-name=', 'lun-read-only=', 'wr-method=', 'force-close=', 'initiator=',
	'modify', 'current-initiator=', 'fresh-initiator=', 'misc', 'update-cfg',
	'check-default-target', 'restore-cfg', 'chap', 'incoming', 'user=', 'pass=', 'set=',
	'duplicate-check']

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', iscsi_long_opt)
	except getopt.GetoptError, e:
		comm_exit(False, '%s' % e)

	iscsiArgs = iSCSIArgs()
	for opt,arg in opts:
		# mode set
		if opt in OP_MODE:
			iscsiArgs.setMode(opt)

		# args proc
		if opt == '--list':
			iscsiArgs.list_set = True
		elif opt == '--target-name':
			iscsiArgs.target_name_set = True
			iscsiArgs.target_name_str = arg
		elif opt == '--volume-name':
			iscsiArgs.volume_name_set = True
			iscsiArgs.volume_name_str = arg
		elif opt == '--modify':
			iscsiArgs.modify_set = True
		elif opt == '--attribute':
			iscsiArgs.attr_set = True
			iscsiArgs.attr_str = arg
		elif opt == '--value':
			iscsiArgs.value_set = True
			iscsiArgs.value_str = arg
		elif opt == '--add':
			iscsiArgs.add_set = True
		elif opt == '--remove':
			iscsiArgs.remove_set = True
			iscsiArgs.remove_str = arg
		elif opt == '--name':
			iscsiArgs.name_set = True
			iscsiArgs.name_str = arg
		elif opt == '--get-detail':
			iscsiArgs.detail_set = True
			iscsiArgs.detail_str = arg
		elif opt == '--udv':
			iscsiArgs.udv_set = True
			iscsiArgs.udv_str = arg
		elif opt == '--block-size':
			iscsiArgs.blocksize_set = True
			iscsiArgs.blocksize_str = arg
		elif opt == '--lun-read-only':
			iscsiArgs.lun_read_only_set = True
			iscsiArgs.lun_read_only_str = arg
		elif opt == '--read-only':
			iscsiArgs.read_only_set = True
			iscsiArgs.read_only_str = arg
		elif opt == '--wr-method':
			iscsiArgs.wrth_str = arg
		elif opt == '--lun-id':
			iscsiArgs.lun_id_set = True
			iscsiArgs.lun_id_str = arg
		elif opt == '--target-name':
			iscsiArgs.target_name_set = True
			iscsiArgs.target_name_str = arg
		elif opt == '--initiator':
			iscsiArgs.initor = arg
		elif opt == '--map':
			iscsiArgs.map_set = True
		elif opt == '--unmap':
			iscsiArgs.unmap_set = True
		elif opt == '--get-privilage':
			iscsiArgs.get_privilage_set = True
		elif opt == '--force-close':
			iscsiArgs.force_close_sid = arg
		elif opt == '--current-initiator':
			iscsiArgs.cur_initor = arg
		elif opt == '--fresh-initiator':
			iscsiArgs.fre_initor = arg
		elif opt == '--update-cfg':
			iscsiArgs.update_cfg = True
		elif opt == '--restore-cfg':
			iscsiArgs.restore_cfg = True
		elif opt == '--check-default-target':
			iscsiArgs.default_target = True
		elif opt == '--incoming':
			iscsiArgs.chap_type = 'incoming'
		elif opt == '--user':
			iscsiArgs.chap_user_str = arg
		elif opt == '--pass':
			iscsiArgs.chap_pass_str = arg
		elif opt == '--set':
			iscsiArgs.chap_set_str = arg
		elif opt == '--duplicate-check':
			iscsiArgs.chap_dup = True

	if iscsiArgs.mode == '--target':
		iscsiTargetProc(iscsiArgs)
	elif iscsiArgs.mode == '--volume':
		iscsiVolumeProc(iscsiArgs)
	elif iscsiArgs.mode == '--lun':
		iscsiLunProc(iscsiArgs)
	elif iscsiArgs.mode == '--session':
		iscsiSessionProc(iscsiArgs)
	elif iscsiArgs.mode == '--misc':
		iscsiMiscProc(iscsiArgs)
	elif iscsiArgs.mode == '--chap':
		iscsiChapProc(iscsiArgs)
	else:
		iscsiUsage()

if __name__ == "__main__":
	main()
