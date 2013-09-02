#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import getopt

os.chdir(os.path.dirname(sys.argv[0]))

from libusermanage import *

class IArgs:
	def __init__(self):
		self.mode = ''
		self.add_set = False
		self.edit_set = False
		self.list_set = False
		self.del_set = False
		self.default_set = False
		self.logon_set = False
		self.check_set = False
		self.share_set = False
		self.right_set = False
		self.name_set = ''
		self.pwd_set = ''
		self.pwd_state = False
		self.note_set = ''
		self.note_state = False
		self.member_set = ''
		self.member_state = False
		self.page_set = 0
		self.coun_set = 10
		self.search_set = ''
		self.write_set = ''
		self.write_state = False
		self.read_set = ''
		self.read_state = False
		self.newpwd_set = ''
		self.newpwd_state = False

	def setMode(self, mode):
		if self.mode == '':
			self.mode = mode
		else:
			print '##操作模式为唯一性，请选择 [ '+','.join(OP_MODE)+' ] 中的一种!参见如下命令格式：\n'
			AUsage()

OP_MODE = ['--user', '--group', '--userpwd', '--default', '--logon']
long_opt = ['user', 'group','add', 'edit', 'list', 'del', 'default', 'logon', 'share', 'check', 'right', 'userpwd', 'name=','pwd=', 'note=', 'member=', 'page=', 'coun=', 'search=', 'write=', 'read=', 'newpwd=']

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', long_opt)
	except getopt.GetoptError, e:
		AUsage(e)

	iArgs = IArgs()
	for opt,arg in opts:
		if opt in OP_MODE:
			iArgs.setMode(opt)

		if opt == '--add':
			iArgs.add_set = True
		elif opt == '--edit':
			iArgs.edit_set = True
		elif opt == '--list':
			iArgs.list_set = True
		elif opt == '--del':
			iArgs.del_set = True
		elif opt == '--share':
			iArgs.share_set = True
		elif opt == '--logon':
			iArgs.logon_set = True
		elif opt == '--check':
			iArgs.check_set = True
		elif opt == '--right':
			iArgs.right_set = True
		elif opt == '--name':
			iArgs.name_set = arg
		elif opt == '--pwd':
			iArgs.pwd_set = arg
			iArgs.pwd_state = True
		elif opt == '--note':
			iArgs.note_set = arg
			iArgs.note_state = True
		elif opt == '--member':
			iArgs.member_set = arg
			iArgs.member_state = True
		elif opt == '--page':
			iArgs.page_set = arg
		elif opt == '--coun':
			iArgs.coun_set = arg
		elif opt == '--search':
			iArgs.search_set = arg
		elif opt == '--write':
			iArgs.write_set = arg
			iArgs.write_state = True
		elif opt == '--read':
			iArgs.read_set = arg
			iArgs.read_state = True
		elif opt == '--newpwd':
			iArgs.newpwd_set = arg
			iArgs.newpwd_state = True

	if iArgs.mode == '--user':
		if iArgs.add_set == True:
			User_Add(iArgs)
		elif iArgs.edit_set == True:
			User_Edit(iArgs)
		elif iArgs.list_set == True:
			User_List(iArgs)
		elif iArgs.del_set == True:
			User_Del(iArgs.name_set)
		elif iArgs.share_set == True:
			User_Share(iArgs)
		elif iArgs.check_set == True:
			User_Check(iArgs)
		else:
			AUsage()
	elif iArgs.mode == '--group':
		if iArgs.edit_set == True:
			Group_Edit(iArgs)
		elif iArgs.list_set == True:
			Group_List(iArgs)
		elif iArgs.del_set == True:
			Group_Del(iArgs.name_set)
		elif iArgs.share_set == True:
			Group_Share(iArgs)
		elif iArgs.check_set == True:
			Group_Check(iArgs)
		else:
			AUsage()
	elif iArgs.mode == '--userpwd':
		User_Edit_Pwd(iArgs)
	elif iArgs.mode == '--logon':
		User_Logon(iArgs)
	elif iArgs.mode == '--default':
		DEFAULT()
	else:
		AUsage()

if __name__ == '__main__':
	main()

