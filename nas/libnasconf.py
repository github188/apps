#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import statvfs
import sys
import commands
import json
import codecs
import ConfigParser
import subprocess

from os.path import join, getsize

reload(sys)
sys.setdefaultencoding('utf8')

SMB_CONF_PATH="/etc/samba/smb.conf"
NFS_CONF_PATH="/etc/exports"

config = ConfigParser.ConfigParser()  
config.read(SMB_CONF_PATH) 

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

def networkUsage(err=""):
	if err != "":
		print '##命令参数不正确，错误提示： %s' % err
	else:
		print '##命令参数不正确，请检查要执行的命令模式！'
	print """
network --list [ --name <nas_name>]
	--add --name <nas_name> --path <nas_path> [--write  <write list> --read <read list> --invalid <invalid users> --browsable <yes|no> --oplocks <yes|no> --ftpwrite <yes|no> --public <yes|no> --inherit <yes|no> --comment <Remark>]
	--edit --basic [-name <nas_name> [--new <New name> --comment <Remark> --browsable <yes|no> --oplocks <yes|no>] ##基本信息修改
	--edit --access --name <nas_name> [--write  <write list> --read <read list> --invalid <invalid users>]##修改访问权限
	--edit --nasallow --name <nas_name> --allow <hosts allow[format: (192.168.11.10 * EXCEPT 192.188.22.* 10.11.20.22)]> ##修改NAS访问控制列表
	--edit --nfsallow --name <nas_name> --allow <hosts allow[format: (192.168.*(rw,async,no_root_squash,insecure) 10.1.0*(ro,async,no_root_squash,insecure))]> ##修改NFS访问控制列表
	--del --name <nas_name> ##删除
	--check --new <New name> [--name <nas_name>] ##重名验证
	--default
"""
	sys.exit(-1)

def deviant(name, Field):
	result = ''
	if Field != '':
		try:
			result = config.get(name, Field)
		except ConfigParser.NoOptionError:
			if Field == 'browsable':
				result = 'yes'
			elif Field == 'oplocks':
				result = 'no'
			elif Field == 'ftp write only':
				result = 'no'
			elif Field == 'public':
				result = 'yes'
	return result
	
#~ 检查共享名称是否成在！
def censor(name):
	if name == '':
		Export(False, '共享名称不能为空！')
	if config.has_section(name) == False:
		Export(False, '找不到共享名称！')

def check(value):	if value.new_set == '':
		Export(False, '共享名称不能为空！')
	if value.name_set == '':		if config.has_section(value.new_set) == True:
			Export(False, '新共享名称已存在！')
		else:
			Export(True, '新共享名称可用！')
	else:
		if value.name_set != value.new_set:
			if config.has_section(value.new_set) == True:
				Export(False, '新共享名称已存在！')
			else:
				Export(True, '新共享名称可用！')
		else:
			Export(True, '新共享名称可用！')

class list_info():
	def __init__(self):
		self.Folder_name = ''
		self.Space = '0/0'
		self.Catalog = ''
		self.documents = 0
		self.browsable = ''
		self.manip = '0/0'

#获得文件夹的父路径挂载点
def imount(Path):
	try:
		list = Path.split('/')
		for i in list:
			if i !='':
				Path = os.path.dirname(Path)
				if os.path.ismount(Path) == True:
					break
	except:
		pass
	return Path

# 获取nas卷容量
def get_nas_capacity(Path):
	capacity = 0
	try:
		vfs = os.statvfs(Path)
		capacity = vfs.f_blocks * vfs.f_bsize
	except:
		pass
	return capacity

# 获取nas卷已经剩余空间
def get_nas_remain(Path):
	remain = 0
	try:
		vfs = os.statvfs(Path)
		remain = vfs.f_bavail * vfs.f_bsize
	except:
		pass
	return remain

# 获取nas卷已经使用空间
def get_nas_occupancy(Path):
	return get_nas_capacity(Path) - get_nas_remain(Path)

def get_dir_size(dir):
	size = 0L
	for root, dirs, files in os.walk(dir):
		size += sum( [getsize(join(root, name)) for name in files] )
	return size
	
def nas_list(value):
	if value.name_set != '':
		censor(value.name_set)
		json_info = {}
		json_info['Name'] = value.name_set
		json_info['comment'] = deviant(value.name_set, "comment")
		json_info['path'] = deviant(value.name_set, "path")
		json_info['browsable'] = deviant(value.name_set, "browsable")
		json_info['oplocks'] = deviant(value.name_set, "oplocks")
		json_info['ftp write only'] = deviant(value.name_set, "ftp write only")
		json_info['public'] = deviant(value.name_set, "public")
		json_info['invalid users'] = deviant(value.name_set, "invalid users")
		json_info['read list'] = deviant(value.name_set, "read list")
		json_info['write list'] = deviant(value.name_set, "write list")
		json_info['valid users'] = deviant(value.name_set, "valid users")
		json_info['inherit permissions'] = deviant(value.name_set, "inherit permissions")
		json_info['hosts allow'] = deviant(value.name_set, "hosts allow")
	else:
		list = []
		json_info = {'total':0, 'rows':[]}
		out_list = config.sections()
		out_list= [i for i in out_list if i!='global']
		#~ out_list = json.dumps(out_list, encoding="UTF-8", ensure_ascii=False)
		for name in out_list:
			Path = deviant(name, "path")
			hosts = deviant(name, "hosts allow")
			if hosts == '*':
				hosts = 1
			else:
				hosts = 0
			nfs_stat = 0
			space = '0/0'
			Catalog = 0
			browsable = 0
			if os.path.exists(Path) == True:
				nfs_stat = SYSTEM_OUT('cat '+NFS_CONF_PATH+'|grep "^'+Path+'"|wc -l')
				space = '%d/%d' % (get_dir_size(Path),get_nas_remain(deviant(name, "path")))
				Catalog = SYSTEM_OUT('find '+Path+' -type d|wc -l')
				browsable = SYSTEM_OUT('find '+Path+' -type f|wc -l')
			out = list_info()
			out.Folder_name = name
			out.Space = space
			out.Catalog = Catalog
			out.documents = browsable
			out.browsable = deviant(name, "browsable")
			out.manip = '%d,%s' % (hosts,nfs_stat)
			list.append(out.__dict__)
		json_info['total'] = len(out_list)
		json_info['rows'] = list
		
	print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)


def add(value):
	if config.has_section(value.name_set) == False and value.name_set != '':
		if value.write_set.strip() != "":
			value.write_set = 'root,'+value.write_set.strip()
			valid = value.write_set
		else:
			value.write_set = 'root'
			valid = value.write_set
		if value.read_set.strip() != "":
			valid = valid +','+ value.read_set.strip()
			
		read = list(set(value.read_set.split(',')))
		write = list(set(value.write_set.split(',')))
		for i in write:
			if i in read:
				read = filter(lambda x:x !=i,read)
		valid = list(set(valid.strip().split(',')))
		config.add_section(value.name_set)
		if value.comment_set == '':
			value.comment_set = value.name_set
		config.set(value.name_set, 'comment', value.comment_set)
		if value.path_set == "":
			Export(False, '共享路径不能为空！')
		config.set(value.name_set, 'path', value.path_set)
		config.set(value.name_set, 'browsable', value.browsable_set)
		config.set(value.name_set, 'oplocks', value.oplocks_set)
		config.set(value.name_set, 'ftp write only', value.ftpwrite_set)
		config.set(value.name_set, 'public', value.public_set)
		config.set(value.name_set, 'invalid users', value.invalid_set)
		config.set(value.name_set, 'read list', ','.join(read))
		config.set(value.name_set, 'write list', ','.join(write))
		config.set(value.name_set, 'valid users', ','.join(list(set(valid))))
		config.set(value.name_set, 'inherit permissions', value.inherit_set)
		config.set(value.name_set, 'hosts allow', '*')
		config.write(open(SMB_CONF_PATH, 'w'))
		Export(True, '增加NAS成功！')
	else:
		Export(False, '共享名称已经存在！')

def edit(value):
	censor(value.name_set)
	if value.basic_set == True:
		if value.new_set != "" and value.name_set != value.new_set:
			if config.has_section(value.new_set) == False:
				config.add_section(value.new_set) 
				if value.comment_state == True:
					config.set(value.new_set, 'comment', value.comment_set) 
				else:
					config.set(value.new_set, 'comment', deviant(value.name_set, "comment")) 				
				config.set(value.new_set, 'path', deviant(value.name_set, "path") ) 				
				if value.browsable_state == True:
					config.set(value.new_set, 'browsable', value.browsable_set) 
				else:
					config.set(value.new_set, 'browsable', deviant(value.name_set, "browsable")) 				
				if value.oplocks_state == True:
					config.set(value.new_set, 'oplocks', value.oplocks_set) 
				else:
					config.set(value.new_set, 'oplocks', deviant(value.name_set, "oplocks")) 				
				config.set(value.new_set, 'ftp write only', deviant(value.name_set, "ftp write only")) 				
				config.set(value.new_set, 'public', deviant(value.name_set, "public")) 				
				config.set(value.new_set, 'invalid users', deviant(value.name_set, "invalid users")) 				
				config.set(value.new_set, 'read list', deviant(value.name_set, "read list")) 				
				config.set(value.new_set, 'write list', deviant(value.name_set, "write list")) 
				config.set(value.new_set, 'valid users', deviant(value.name_set, "valid users"))
				config.set(value.new_set, 'inherit permissions', deviant(value.name_set, "inherit permissions"))
				config.set(value.new_set, 'hosts allow', deviant(value.name_set, "hosts allow"))
				config.remove_section(value.name_set)
			else:
				 Export(False, '新共享名称已存在！')
		else:	
			if value.comment_state == True:
				config.set(value.name_set, 'comment', value.comment_set) 
			if value.browsable_state == True:
				config.set(value.name_set, 'browsable', value.browsable_set) 
			if value.oplocks_state == True:
				config.set(value.name_set, 'oplocks', value.oplocks_set) 
		config.write(open(SMB_CONF_PATH, 'w'))
		Export(True, 'NAS基本信息修改成功！')
	elif value.access_set == True:
		if value.write_set.strip() != "":
			value.write_set = 'root,'+value.write_set.strip()
			valid = value.write_set
		else:
			value.write_set = 'root'
			valid = value.write_set
		if value.read_set.strip() != "":
			valid = valid +','+ value.read_set.strip()
			
		read = list(set(value.read_set.split(',')))
		write = list(set(value.write_set.split(',')))
		for i in write:
			if i in read:
				read = filter(lambda x:x !=i,read)
		valid = list(set(valid.strip().split(',')))
		valid.extend(value.write_set.split(','))
		config.set(value.name_set, 'invalid users', value.invalid_set) 				
		config.set(value.name_set, 'read list', ','.join(read)) 				
		config.set(value.name_set, 'write list', ','.join(write)) 
		config.set(value.name_set, 'valid users', ','.join(list(set(valid))))
		config.write(open(SMB_CONF_PATH, 'w'))
		Export(True, 'NAS访问权限修改成功！')
	elif value.nasallow_set == True:
		if value.allow_set == '':
			value.allow_set = '*'
		config.set(value.name_set, 'hosts allow', value.allow_set)
		config.write(open(SMB_CONF_PATH, 'w'))
		Export(True, 'NAS安全策略修改成功！')
	elif value.nfsallow_set == True:
		nfs_conf = open (NFS_CONF_PATH, 'r')
		try:
			fileList = nfs_conf.readlines()
			path = config.get(value.name_set, "path")
			file = ''
			exist = True
			for fileLine in fileList:
				if len(fileLine) > 2:
					if len(fileLine.split(path)) > 1:
						if value.allow_set != '':
							file = file + path + ' '+ value.allow_set +'\n'
							exist = False
						else:
							exist = False
					else:
						file = file + fileLine
			nfs_conf.close()
		except:
			nfs_conf.close()
			Export(False, '操作失败！')
		if exist == True:
			operating = open(NFS_CONF_PATH, 'a')
			try:
				operating.write(path + ' '+ value.allow_set +'\n')
				operating.close()
				Export(True, 'NFS安全策略修改成功！')
			except:
				operating.close()
		else:
			operating = open(NFS_CONF_PATH, 'w')
			try:
				operating.write(file)
				operating.close()
				Export(True, 'NFS安全策略修改成功！')
			except:
				operating.close()
		SYSTEM_OUT('exportfs -r')
		xix = open (NFS_CONF_PATH, 'r')
		print xix.read()
		xix.close()
	else:
		networkUsage()

def NASdel(value):
	censor(value.name_set)
	path = config.get(value.name_set, "path")
	result = config.remove_section(value.name_set)
	exist = True
	if result == True:
		nfs_conf = open (NFS_CONF_PATH, 'r')
		try:
			fileList = nfs_conf.readlines()
			file = ''
			for fileLine in fileList:
				if len(fileLine.split(path)) > 1:
					exist = False
				else:
					file = file + fileLine
			nfs_conf.close()
		except:
			nfs_conf.close()
		config.write(open(SMB_CONF_PATH, 'w'))
		if exist == False:
			operating = open(NFS_CONF_PATH, 'w')
			try:
				operating.write(file)
				operating.close()
				SYSTEM_OUT('exportfs -r')
			except:
				operating.close()
			
		if os.path.exists(path) == True:
			os.system('rm -rf ' +path)
		Export(True, 'NAS共享删除成功！')
	else:
		Export(False, '删除失败，请重新操作！')
	
