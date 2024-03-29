#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys
import os
import commands
import getopt
import json
os.chdir(os.path.dirname(sys.argv[0]))

from libadminmanage import *

class IArgs:
	def __init__(self):
		self.mode = ''
		self.list_set = False
		self.add_set = False
		self.edit_set = False
		self.del_set = False
		self.check_set = False
		self.login_set = False
		self.default_set = False
		self.outsession_set = False
		self.name_set = ''
		self.pwd_set = ''
		self.pwd_state = False
		self.new_pwd_set = ''
		self.new_pwd_state = False
		self.manage_type_set = '2'
		self.manage_type_state = False
		self.note_set = ''
		self.note_state = False
		self.page_set = 0
		self.coun_set = 10
		self.search_set = ''
		self.session_set = ''
		self.session_state = False

	def setMode(self, mode):
		if self.mode == '':
			self.mode = mode

if os.path.exists(Admin_CONF_PATH) == False:
	Admin_default()

OP_MODE = ['--list', '--add', '--edit', '--del', '--check', '--login', '--default', '--outsession']
long_opt = ['list', 'add', 'edit', 'del', 'check', 'default',  'outsession', 'login', 'name=', 'page=', 'coun=', 'search=', 'pwd=', 'new_pwd=', 'manage_type=', 'note=', 'session=']

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
		elif opt == '--check':
			iArgs.check_set = True
		elif opt == '--login':
			iArgs.login_set = True
		elif opt == '--outsession':
			iArgs.outsession_set = True
		elif opt == '--default':
			iArgs.default_set = True
		elif opt == '--page':
			iArgs.page_set = arg
		elif opt == '--coun':
			iArgs.coun_set = arg
		elif opt == '--search':
			iArgs.search_set = arg
		elif opt == '--session':
			iArgs.session_set = arg
			iArgs.session_state = True
		elif opt == '--name':
			iArgs.name_set = arg
		elif opt == '--pwd':
			iArgs.pwd_set = arg
			iArgs.pwd_state = True
		elif opt == '--new_pwd':
			iArgs.new_pwd_set = arg
			iArgs.new_pwd_state = True
		elif opt == '--manage_type':
			iArgs.manage_type_set = arg
			iArgs.manage_type_state = True
		elif opt == '--note':
			iArgs.note_set = arg
			iArgs.note_state = True
		elif opt == '--page':
			iArgs.page_set = arg
		elif opt == '--coun':
			iArgs.coun_set = arg
		elif opt == '--search':
			iArgs.search_set = arg

	if iArgs.list_set == True:
		Admin_list(iArgs)
	elif iArgs.add_set == True:
		Admin_add(iArgs)
	elif iArgs.edit_set == True:
		Admin_edit(iArgs)
	elif iArgs.del_set == True:
		Admin_del(iArgs)
	elif iArgs.check_set == True:
		Admin_check(iArgs)
	elif iArgs.default_set == True:
		Admin_default()
	elif iArgs.login_set == True:
		Admin_login(iArgs)
	elif iArgs.outsession_set == True:
		out_session(iArgs)
	else:
		AUsage()

if __name__ == '__main__':
	main()
