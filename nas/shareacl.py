#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import getopt

os.chdir(os.path.dirname(sys.argv[0]))

from libshareacl import *

class IArgs:
	def __init__(self):
		self.mode = ''
		self.tree_set = False
		self.list_set = False
		self.son_set = False
		self.setson_set = False
		self.edit_set = False
		self.path_set = ''
		self.name_set = ''
		self.status_set = 'disable'
		self.owner_set = 'admin'
		self.other_set = '---'
		self.flags_set = '0'
		self.inherit_set = '0'
		self.cover_set = '0'
		self.purv_set = ''

	def setMode(self, mode):
		if self.mode == '':
			self.mode = mode
		else:
			print '##操作模式为唯一性，请选择 [ '+','.join(OP_MODE)+' ] 中的一种!参见如下命令格式：\n'
			AUsage()

OP_MODE = ['--tree','--list','--son','--setson','--edit']
long_opt = ['tree', 'list', 'son', 'setson',  'edit', 'name=', 'path=', 'status=', 'owner=', 'other=', 'flags=', 'inherit=', 'cover=', 'purv=']

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', long_opt)
	except getopt.GetoptError, e:
		AUsage(e)

	iArgs = IArgs()
	for opt,arg in opts:
		if opt in OP_MODE:
			iArgs.setMode(opt)

		if opt == '--tree':
			iArgs.tree_set = True
		elif opt == '--list':
			iArgs.list_set = True
		elif opt == '--son':
			iArgs.son_set = True
		elif opt == '--setson':
			iArgs.setson_set = True
		elif opt == '--edit':
			iArgs.edit_set = True
		elif opt == '--path':
			iArgs.path_set = arg
		elif opt == '--name':
			iArgs.name_set = arg
		elif opt == '--status':
			iArgs.status_set = arg
		elif opt == '--owner':
			iArgs.owner_set = arg
		elif opt == '--other':
			iArgs.other_set = arg
		elif opt == '--flags':
			iArgs.flags_set = arg
		elif opt == '--inherit':
			iArgs.inherit_set = arg
		elif opt == '--cover':
			iArgs.cover_set = arg
		elif opt == '--purv':
			iArgs.purv_set = arg

	if iArgs.mode == '--tree':
		Tree_List(iArgs)
	elif iArgs.mode == '--list':
		P_List(iArgs)
	elif iArgs.mode == '--son':
		Son(iArgs)
	elif iArgs.mode == '--setson':
		Setson(iArgs)
	elif iArgs.mode == '--edit':
		Edit(iArgs)
	else:
		AUsage()

if __name__ == '__main__':
	main()

