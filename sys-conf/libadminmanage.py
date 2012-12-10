#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import codecs
import ConfigParser
import subprocess
import hashlib

#~ from os.path import join, getsize

reload(sys)
sys.setdefaultencoding('utf8')

Admin_CONF_PATH="/opt/manage.conf"
Session_CONF_PATH="/opt/session.conf"

config = ConfigParser.ConfigParser()  
config.read(Admin_CONF_PATH) 

Admin_CONF = """[admin]
password = 21232F297A57A5A743894A0E4A801FC3
manage_pwd = 21232F297A57A5A743894A0E4A801FC3
manage_type = 1
note = 超级管理员
[root]
password = 80BAEC203A63F45280DAADD5CF3598FE
manage_pwd = 80BAEC203A63F45280DAADD5CF3598FE
manage_type = 3
note = 专用管理员
"""
#~ root帐号密码默认为密码lkjhgfdsA
#~ admin帐号密码默认为密码admin
def Export(ret = True, msg = ''):
	ret_msg = {'status':True, 'msg':''}
	ret_msg['status'] = ret
	ret_msg['msg'] = msg
	print json.dumps(ret_msg, encoding="UTF-8", ensure_ascii=False)
	sys.exit(-1)

#~ 执行系统命令并输出结果
def SYSTEM_OUT(com):
	p = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	s = p.stdout.readline()
	s = s.replace('\n','')
	return s

def AUsage(err=""):
	if err != "":
		print '##命令参数不正确，错误提示： %s' % err
	else:
		print '##命令参数不正确，请检查要执行的命令模式！'
	print """
adminmanage --list [ <--name <admin_name> --page <int> --coun <int> --search <user name> ]		##输出管理员列表
	   --add --name <admin_name> --pwd <password> [--note <Remark>]		##增加用户
	   --edit --name <admin_name> [--new_pwd <new_password> --new_manage_pwd <new_manage_pwd> --manage_type <manage_type> --note <Remark>]		##修改管理员密码或备注
	   --useredit --name <admin_name> --manage_pwd <password> [--new_pwd <new_password> --new_manage_pwd <new_manage_pwd> --note <Remark>]		##管理员自己修改密码或备注
	   --del --name <admin_name>		##删除管理员
	   --check --name <admin_name>		##管理员重名验证
	   --login --name <admin_name> --pwd <password>		##管理员登录
	   --check_pwd --name <admin_name> --pwd <password>		##验证操作密码
	   --outsession [ --session <session> ]		##输入输出session
"""
	sys.exit(-1)

def deviant(name, Field):
	if Field != '':
		try:
			result = config.get(name, Field)
		except ConfigParser.NoOptionError:
			result = ''
	return result

#~ 检查管理员名称是否成在！
def censor(name):
	if name == '':
		Export(False, '管理员名称不能为空！')
	if config.has_section(name) == False:
		Export(False, '找不到管理员名称！')

#~ 管理员列表输出项
class Admin_list_info():
	def __init__(self):
		self.Manage_name = ''
		self.Manage_purview = ''
		self.Manage_Note = ''

#~#### 输出管理员列表主程序
def Admin_list(value):
	if config.has_section(value.name_set) and value.name_set != '':
		json_info = {}
		json_info['Manage_name'] = value.name_set
		json_info['Manage_purview'] = deviant(value.name_set, 'manage_type')
		json_info['Manage_Note'] = deviant(value.name_set, 'note')
	else:
		list = []
		User_list = []
		json_info = {'total':0, 'rows':[]}
		page = int(value.page_set)
		coun = int(value.coun_set)
		search = value.search_set.strip()
		search_check = len(search)		
		inti = 0
		if page > 0:
			StartEnd = page * coun + 1
			Start = StartEnd - coun
		else:
			StartEnd =0
			Start = 0
		out_list = config.sections()
		out_list= [i for i in out_list if i!='admin' and i!='root']
		out_list.sort() 
		for fileLine in out_list:
			if search_check > 0:
				search_check = len(fileLine.split(search))
			if search_check == 0:
				inti += 1
				if inti >= Start and inti < StartEnd and search_check == 0 or Start == 0:
					out = Admin_list_info()
					out.Manage_name = fileLine
					out.Manage_purview =  deviant(fileLine, 'manage_type')
					out.Manage_Note =  deviant(fileLine, 'note')
					list.append(out.__dict__)
			elif search_check > 1:
				inti += 1
				if inti >= Start and inti < StartEnd and search_check > 0 or Start == 0:
					out = Admin_list_info()
					out.Manage_name = fileLine
					out.Manage_purview =  deviant(fileLine, 'manage_type')
					out.Manage_Note =  deviant(fileLine, 'note')
					list.append(out.__dict__)
		json_info['total'] = inti
		json_info['rows'] = list

	print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)

#~#### 增加管理员主程序
def Admin_add(value):
	if config.has_section(value.name_set) == False and value.name_set != '':
		if value.pwd_set != '':
			pwd = hashlib.md5(value.pwd_set).hexdigest().upper()
		else:
			pwd = '21218CCA77804D2BA1922C33E0151105'
		if value.note_state == False:
			value.note_set = '管理员'
		config.add_section(value.name_set)
		config.set(value.name_set, 'password', pwd)
		config.set(value.name_set, 'manage_pwd', pwd)
		config.set(value.name_set, 'manage_type', 2)
		config.set(value.name_set, 'note', value.note_set)
		config.write(open(Admin_CONF_PATH, 'w'))
		Export(True, '管理员"'+value.name_set+'"增加成功！')
	else:
		Export(False, '输入的管理员名称不可用！')	

#~#### 修改管理员主程序
def Admin_edit(value):
	if config.has_section(value.name_set) and value.name_set != '':
		if value.new_pwd_state:
			config.set(value.name_set, 'password', hashlib.md5(value.new_pwd_set).hexdigest().upper())
		if value.new_manage_pwd_state:
			config.set(value.name_set, 'manage_pwd', hashlib.md5(value.new_manage_pwd_set).hexdigest().upper())
		if value.manage_type_state:
			config.set(value.name_set, 'manage_type', value.manage_type_set)
		if value.note_state:
			config.set(value.name_set, 'note', value.note_set)
		config.write(open(Admin_CONF_PATH, 'w'))
		Export(True, '管理员"'+value.name_set+'"修改成功！')
	else:
		Export(False, '输入的管理员名称不可用！')	

#~#### 删除管理员主程序
def Admin_del(value):
	if value.name_set != '':
		name_list = value.name_set.split(',')
		for name in name_list:
			if config.has_section(name):
				config.remove_section(name)
		config.write(open(Admin_CONF_PATH, 'w'))
		Export(True, '管理员"'+value.name_set+'"删除成功！')
	else:
		Export(False, '删除失败！')	

#~#### 验证管理员是否重名主程序
def Admin_check(value):
	if config.has_section(value.name_set):
		Export(False, '管理员名存在！')
	else:
		Export(True, '管理员名称可以用！')		

#~#### 管理员自己修改信息主程序
def Admin_useredit(value):
	if config.has_section(value.name_set) and value.name_set != '':
		if deviant(value.name_set, 'manage_pwd').strip() == hashlib.md5(value.manage_pwd_set).hexdigest().upper():
			if value.new_pwd_state:
				config.set(value.name_set, 'password', hashlib.md5(value.new_pwd_set).hexdigest().upper())
			if value.new_manage_pwd_state:
				config.set(value.name_set, 'manage_pwd', hashlib.md5(value.new_manage_pwd_set).hexdigest().upper())
			if value.manage_type_state:
				config.set(value.name_set, 'manage_type', value.manage_type_set)
			if value.note_state:
				config.set(value.name_set, 'note', value.note_set)
			config.write(open(Admin_CONF_PATH, 'w'))
			Export(True, '管理员"'+value.name_set+'"修改成功！')
		else:
			Export(False, '输入的操作密码不正确！')		
	else:
		Export(False, '输入的管理员名称不可用！')	

#~#### 管理员登录主程序
def Admin_login(value):
	if config.has_section(value.name_set) and value.name_set != '' and deviant(value.name_set, 'password').strip() == hashlib.md5(value.pwd_set).hexdigest().upper():
		Export(True, deviant(value.name_set, 'manage_type'))
	else:
		Export(False, '登录失败！')

#~#### 验证操作密码主程序
def Admin_check_pwd(value):
	if config.has_section(value.name_set) == False or (deviant(value.name_set, 'manage_pwd').strip() != hashlib.md5(value.pwd_set).hexdigest().upper()):
		Export(False, '操作密码不正确！')
	else:
		Export(True, '登验证通过！')

#~#### 恢复默认主程序
def Admin_default():
	f = open(Admin_CONF_PATH, 'w')
	try:
		f.write(Admin_CONF)
	finally:
		f.close()
def out_session(value):
	if value.session_state:
		f = open(Session_CONF_PATH, 'w')
		try:
			f.write(value.session_set)
		finally:
			f.close()		
	else:
		f = open(Session_CONF_PATH, 'r')
		try:
			print f.read()
		finally:
			f.close()


