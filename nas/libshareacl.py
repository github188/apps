#!/usr/bin/env python
# -*- coding: utf-8 -*-

#~ cat /opt/samba/conf/rd/libusermanage.py|grep ^#~###-|sed 's/#~###-/#~ /g'
import os
import sys
import commands
import stat
import json
import codecs
import ConfigParser
import subprocess
import shutil
#~ import os.path

from os.path import join, getsize
reload(sys)
sys.setdefaultencoding('utf8')

SMB_CONF_PATH = "/opt/etc/samba/smb.conf"
config = ConfigParser.ConfigParser()  
config.read(SMB_CONF_PATH) 

def deviant(name, Field):
	result = ''
	if Field != '':
		try:
			result = config.get(name, Field)
		except:
			result = ''
	return result

def censor(name):
	if name == '':
		Export(False, '共享名称不能为空！')
	if config.has_section(name) == False:
		Export(False, '找不到共享名称！')

def __Check__Name__(name):
	s = False
	if name != '':
		if config.has_section(name):
			s = True
	return s

def Export(ret = True, msg = ''):
	ret_msg = {'status':True, 'msg':''}
	ret_msg['status'] = ret
	ret_msg['msg'] = msg
	print json.dumps(ret_msg, encoding="UTF-8", ensure_ascii=False)
	sys.exit(-1)

#~### 执行系统命令并输出结果
def SYSTEM_OUT(com):
	s = ''
	try:
		p = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		s = p.stdout.readline()
		s = s.replace('\n','')
	except:
		pass
	return s

#~ 通过路径返回一个共享名
def __Out_Share_name__(path):
	out_list = config.sections()
	out_list= [i for i in out_list if i!='global' and i!='系统设置']
	Share_name = ''
	for name in out_list:
		if len(deviant(name, "path").split(path)) > 1:
			Share_name = name
			break
	return Share_name
	
def AUsage(err=""):
	if err != "":
		print '##命令参数不正确，错误提示： %s' % err
	else:
		print '##命令参数不正确，请检查要执行的命令模式！'
	print """
shareacl --tree --path <path> [--name <share_name> ]		##输出目录内的子文件夹树列表
	--list --path <path>		##输出目录的权限信息
	--son --name <share_name>		##输出是否开启子目录权限功能
	--setson --name <share_name> --status <disable|enable>		##设置是否开始子目录权限
	--edit --owner <Owner_name> --other <---|r-x|rwx> --flags <0|1> --inherit <0|1> --cover <0|1> --purv <purview List> --path <path>		##设置子目录权限
"""
	sys.exit(-1)

def Tree_List(value):
	class list_info():
		def __init__(self):
			self.id = ''
			self.text = ''
			self.checked = True
			self.state = 'closed'

	if os.path.lexists(value.path_set):
		Dirlist = os.listdir(value.path_set)
		list = []
		for x_name in Dirlist:
			Folder_path = os.path.join(value.path_set, x_name)
			if os.path.isdir(Folder_path):
				out = list_info()
				out.id = Folder_path
				out.text = x_name
				list.append(out.__dict__)
		print json.dumps(list, encoding="UTF-8", ensure_ascii=False)
	else:
		if __Check__Name__(value.name_set):
			json_info = [{'id':deviant(value.name_set, "path"), 'text':value.name_set, 'checked':True, 'state':'closed'}]
			print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)
		else:
			Export(False, '路径不能为空，请输入参数！')

def P_List(value):
	class Son_info():
		def __init__(self):
			self.name = ''
			self.name_note = ''
			self.name_type = ''
			self.Purview = '---'
	if os.path.lexists(value.path_set):
		list = []
		Other = '---' #~其它用户权限
		Owner = '' #~拥有者
		Flags = '0' #~其它用户是否允许删除
		Inherit = '0' #~设置成默认权限
		json_info = {'status':True, 'Other':'', 'rows':[], 'Owner':'', 'Flags': 'no', 'Inherit': 'yes'}
		getfacl_list = subprocess.Popen('getfacl -p -e %s' % value.path_set, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for x in getfacl_list.stdout.readlines():
			x = x.replace(' ','').replace('\n','')
			x_name = x.split(':')
			if x_name[0] == 'other':
				Other = x_name[2]
			if x_name[0] == '#owner':
				Owner = x_name[1]
			if x_name[0] == '#flags':
				Flags = '1'
			if x_name[0] == 'default':
				Inherit = '1'
			if len(x_name) == 4:
				if len(x_name[1]) > 0 and x_name[0] != 'default':
					#~ print x_name
					out = Son_info()
					out.name = x_name[1]
					out.name_note = SYSTEM_OUT('cat /etc/passwd|grep "^'+x_name[1]+':"|cut -d ":" -f5')
					out.name_type = x_name[0]
					out.Purview = x_name[3]
					list.append(out.__dict__)
		if Owner == "root":
			Owner = "admin"
		json_info['rows'] = list
		json_info['Other'] = Other
		json_info['Owner'] = Owner
		json_info['Flags'] = Flags
		json_info['Inherit'] = Inherit
		print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)
	else:
		Export(False, '路径不能为空，请输入参数！')
def Son(value):
	if __Check__Name__(value.name_set):
		path = deviant(value.name_set, "path")
		pathStr = os.path.split(deviant(value.name_set, "path"))
		if SYSTEM_OUT("/bin/ls -l %s|grep -w %s|awk '{print $1}'|grep '+'|wc -l" % (pathStr[0], pathStr[1])) == '0':
			Q = 'disable'
		else:
			Q = 'enable'
	else:
		Q = 'disable'
	Export(Q, path)

def Setson(value):
	if __Check__Name__(value.name_set):
		path = deviant(value.name_set, "path")
		if value.status_set == 'disable':
			SYSTEM_OUT('chown -R root.root %s' % path)
			SYSTEM_OUT('chmod -R 777 %s' % path)
			SYSTEM_OUT('setfacl -R -b %s' % path)
			Export(True, '关闭子目录权限控制成功！')
		else:
			SYSTEM_OUT('chown -R admin.users %s' % path)
			SYSTEM_OUT('setfacl -R -m other:r-x %s' % path)
			SYSTEM_OUT('setfacl -d -R -m other:r-x %s' % path)
			SYSTEM_OUT('nasconf --edit --access --name %s --write guest,@users' % value.name_set)
			Export(True, '开启子目录权限控制成功！')
		
	else:
		Export(False, '路径不能为空，请输入参数！')

def Edit(value):
	if len(value.purv_set) > 0:
		value.purv_set = '%s,other:%s' % (value.purv_set,value.other_set)
	else:
		value.purv_set = 'other:%s' % value.other_set		
	if os.path.lexists(value.path_set):
		cover_com = ''
		inherit_com = ''
		#~ 判断是否要设置子目录
		if value.cover_set == '1':
			cover_com = '-R '
				
		#~ 先删除所有权限
		SYSTEM_OUT('setfacl %s-b %s' % (cover_com,value.path_set))
		
		#~其它用户是否允许删除
		if value.flags_set == '0':
			SYSTEM_OUT('chmod %s-t %s' % (cover_com, value.path_set))
		else:
			SYSTEM_OUT('chmod %s+t %s' % (cover_com, value.path_set))
			
			
		if value.owner_set != '':
			SYSTEM_OUT('chown %s%s %s' % (cover_com, value.owner_set, value.path_set))
			
		commstr = 	'%s-m %s %s' % (cover_com, value.purv_set, value.path_set)
		SYSTEM_OUT('setfacl %s' % commstr)
		if value.inherit_set == '1':
			SYSTEM_OUT('setfacl -d %s' % commstr)
		Export(True, '目录权限设置成功！')
	else:
		Export(False, '路径不能为空，请输入参数！')
		
		
		
		


