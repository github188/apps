#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import statvfs
import sys
import stat
import shutil
import commands
import json
import codecs
import ConfigParser
import subprocess

from os.path import join, getsize

reload(sys)
sys.setdefaultencoding('utf8')

SMB_PATH = "/opt/etc/samba/"
WWW_PATH = "/var/www/"
SMB_CONF_PATH = SMB_PATH+"smb.conf"
SMB_USER_CONF_PATH = SMB_CONF_PATH+"."
NFS_CONF_PATH = "/opt/etc/exports"
GROUP_CONF_FILE = "/etc/group"
RESTART_SMB = 'killall -HUP smbd nmbd'
DEF_NASCONF = '/opt/jw-conf/system/nasconf/'
if os.path.exists(SMB_PATH) == False:
	try:
		os.makedirs(SMB_PATH)
		os.chmod(SMB_PATH, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
	except:
		pass

if os.path.exists(NFS_CONF_PATH) == False:
	try:
		os.mknod(NFS_CONF_PATH)
	except:
		pass

if os.path.exists(DEF_NASCONF) == False:
	try:
		os.makedirs(DEF_NASCONF)
		os.chmod(DEF_NASCONF, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
	except:
		pass
if os.path.exists(DEF_NASCONF+'修改登陆密码.html') == False:
	try:
		os.symlink(WWW_PATH+'pwd.html', DEF_NASCONF+'修改登陆密码.html')
	except:
		pass

USE_CONF = """[global]
workgroup = WORKGROUP
server string = %h
security = user
passdb backend = smbpasswd
smb passwd file = /etc/samba/smbpasswd
include = /opt/etc/samba/smb.conf.guest
encrypt passwords = yes
guest account = guest
load printers = no
dns proxy = no
dos charset = UTF_8
display charset = UTF_8
unix charset = UTF-8
socket options = TCP_NODELAY SO_KEEPALIVE SO_RCVBUF=8192 SO_SNDBUF=8192
directory mask = 0777
create mask = 0777
oplocks = yes
locking = yes
veto files = /.AppleDB/.AppleDouble/.AppleDesktop/:2eDS_Store/Network Trash Folder/Temporary Items/TheVolumeSettingsFolder/.@__thumb/.@__desc/:2e*/
os level = 33
max log size = 10
username level = 0
deadtime = 10
name resolve order = bcast wins
force directory security mode = 0000
template shell = /bin/sh
delete veto files = yes
map archive = no
map system = no
map hidden = no
map read only = no
use sendfile = yes
unix extensions = no
store dos attributes = yes
client ntlmv2 auth = yes
dos filetime resolution = no
inherit acls = yes
wide links = yes

"""
SMB_CONF = """[global]
workgroup = WORKGROUP
server string = %h
security = user
passdb backend = smbpasswd
smb passwd file = /etc/samba/smbpasswd
config file = /opt/etc/samba/smb.conf.%U
encrypt passwords = yes
guest account = guest
load printers = no
dns proxy = no
dos charset = UTF_8
display charset = UTF_8
unix charset = UTF-8
socket options = TCP_NODELAY SO_KEEPALIVE SO_RCVBUF=8192 SO_SNDBUF=8192
directory mask = 0777
create mask = 0777
oplocks = yes
locking = yes
veto files = /.AppleDB/.AppleDouble/.AppleDesktop/:2eDS_Store/Network Trash Folder/Temporary Items/TheVolumeSettingsFolder/.@__thumb/.@__desc/:2e*/
os level = 33
max log size = 10
username level = 0
deadtime = 10
name resolve order = bcast wins
force directory security mode = 0000
template shell = /bin/sh
delete veto files = yes
map archive = no
map system = no
map hidden = no
map read only = no
use sendfile = yes
unix extensions = no
store dos attributes = yes
client ntlmv2 auth = yes
dos filetime resolution = no
inherit acls = yes
wide links = yes
browsable = yes
public = yes
guest ok = yes

[系统设置]
comment = 系统设置
path = """+DEF_NASCONF+"""
directory mask = 0777
create mask = 0777
read list = guest
write list = root
valid users = root,guest
inherit permissions = yes

"""

config = ConfigParser.ConfigParser()  
#~ e_conf = ConfigParser.ConfigParser()  
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

def AUsage(err=""):
	if err != "":
		print '##命令参数不正确，错误提示： %s' % err
	else:
		print '##命令参数不正确，请检查要执行的命令模式！'
	print """
nasconf --list [ --name <nas_name> --page <int> --coun <int> --search <Share_name> --nfs <nfs Filter>]		###输出共享列表
	--add --name <nas_name> --path <nas_path> [--write  <write list> --read <read list> --invalid <invalid users> --browsable <yes|no> --comment <Remark>]		###增加共享
	--edit --basic [--name <nas_name> [--new <New name> --comment <Remark> --browsable <yes|no>]		###基本信息修改
	--edit --access --name <nas_name> [--write  <write list> --read <read list> --invalid <invalid users>]		###修改访问权限
	--edit --nasallow --name <nas_name> --allow <hosts allow[format: (192.168.11.10 * EXCEPT 192.188.22.* 10.11.20.22)]> 		###修改NAS访问控制列表
	--edit --nfsallow --name <nas_name> --allow <hosts allow[format: (192.168.*(rw,async,no_root_squash,insecure) 10.1.0*(ro,async,no_root_squash,insecure))]> 	###修改NFS访问控制列表
	--del --name <nas_name>		###删除共享
	--check --new <New name> [--name <nas_name>]		##重名验证
	--sync --path <volume path>		###删除NAS卷时同步删除NAS卷中的共享目录及配置
	--high [--guest <yes|no> --privacy <yes|no>]			###高级配置，管理SAMBA的共享模式
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
	return result
	
#~ 检查共享名称是否成在！
def censor(name):
	if name == '':
		Export(False, '共享名称不能为空！')
	if config.has_section(name) == False:
		Export(False, '找不到共享名称！')

def check(value):
	if value.new_set == '':
		Export(False, '共享名称不能为空！')
	if value.name_set == '':
		if config.has_section(value.new_set) == True:
			Export(False, '新共享名称 "'+value.new_set+'" 已存在！')
		else:
			Export(True, '新共享名称 "'+value.new_set+'" 可用！')
	else:
		if value.name_set != value.new_set:
			if config.has_section(value.new_set) == True:
				Export(False, '新共享名称 "'+value.new_set+'" 已存在！')
			else:
				Export(True, '新共享名称 "'+value.new_set+'" 可用！')
		else:
			Export(True, '新共享名称可用！')

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

class list_info():
	def __init__(self):
		self.Folder_name = ''
		self.Remain = 0
		self.Occupancy = 0
		self.Catalog = 0
		self.nasallow = 'no'
		self.NFS = 'no'
		self.State = 'no'
	
def nas_list(value):
	if value.name_set != '':
		censor(value.name_set)
		json_info = {}
		json_info['Name'] = value.name_set
		json_info['comment'] = deviant(value.name_set, "comment")
		json_info['path'] = deviant(value.name_set, "path")
		json_info['browsable'] = deviant(value.name_set, "browsable")
		json_info['invalid users'] = deviant(value.name_set, "invalid users")
		json_info['read list'] = deviant(value.name_set, "read list")
		json_info['write list'] = deviant(value.name_set, "write list")
		json_info['valid users'] = deviant(value.name_set, "valid users")
		json_info['inherit permissions'] = deviant(value.name_set, "inherit permissions")
		json_info['hosts allow'] = deviant(value.name_set, "hosts allow")
		nfs_conf = open (NFS_CONF_PATH, 'r')
		nfs_allow = ''
		try:
			fileList = nfs_conf.readlines()
			path = json_info['path']+' '
			for fileLine in fileList:
				if len(fileLine.split(path)) > 1:
					nfs_allow = fileLine.replace(path,'')
					exist = False
			nfs_conf.close()
		except:
			nfs_conf.close()
		json_info['NFS allow'] = nfs_allow.replace('\n','')
	else:
		list = []
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
		out_list= [i for i in out_list if i!='global' and i!='系统设置']
		out_list.sort() 
		for name in out_list:
			if search_check > 0:
				search_check = len(name.split(search))
			if value.nfs_set:
				nfsSat = int(SYSTEM_OUT('cat '+NFS_CONF_PATH+'|grep "^'+deviant(name, "path")+' "|wc -l'))
				if search_check == 0 and nfsSat > 0:
					inti += 1
					if inti >= Start and inti < StartEnd or Start == 0:
						list.append(__Share_List_out__(name).__dict__)
				elif search_check > 1 and nfsSat > 0:
					inti += 1
					if inti >= Start and inti < StartEnd or Start == 0:
						list.append(__Share_List_out__(name).__dict__)
			else:
				if search_check == 0:
					inti += 1
					if inti >= Start and inti < StartEnd or Start == 0:
						list.append(__Share_List_out__(name).__dict__)
				elif search_check > 1:
					inti += 1
					if inti >= Start and inti < StartEnd or Start == 0:
						list.append(__Share_List_out__(name).__dict__)
		json_info['total'] = inti
		json_info['rows'] = list
		
	print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)

#~ 共享列表输出函数
#~ name为共享名称
def __Share_List_out__(name):
	Path = deviant(name, "path")
	hosts = 'no'
	if len(deviant(name, "hosts allow").strip()) > 0 and deviant(name, "hosts allow").strip() != '*':
		hosts = 'yes'
	nfs_stat = 'no'
	out = list_info()
	out.Folder_name = name
	if os.path.exists(Path) == True:
		if int(SYSTEM_OUT('cat '+NFS_CONF_PATH+'|grep "^'+Path+' "|wc -l')) > 0:
			nfs_stat = 'yes'
		out.Occupancy = get_dir_size(Path)
		out.Remain = get_nas_remain(deviant(name, "path"))
		out.Catalog = SYSTEM_OUT('find '+Path+' -type d|wc -l')
		out.State = 'yes'
	out.nasallow = hosts
	out.NFS = nfs_stat
	return out

#~ 列出组中的所有用户
def __Group_User__(group):
	group = group.replace('@','')
	conf = open (GROUP_CONF_FILE, 'r')
	user_list = ''
	try:
		fileList = conf.readlines()
		for fileLine in fileList:
			x = fileLine.split(':')
			if len(x) > 3:
				if x[0] == group:
					user_list = x[3].split('\n')[0]
					
		conf.close()
	except:
		conf.close()
	return user_list
	
#~ 列出所有用户
def __User_List__(U_list):
	if isinstance(U_list,list) != True:
		U_list = U_list.split(',')
	user_list = ''
	for x in U_list:
		if len(x.split('@')) == 1:
			if len(user_list) > 0:
				user_list += ','+x
			else:
				user_list = x
	return user_list

#~ 列出所有组的用户
def __Group_List__(U_list):
	if isinstance(U_list,list) != True:
		U_list = U_list.split(',')
	user_list = ''
	for x in U_list:
		if len(x.split('@')) > 1:
			if len(user_list) > 0:
				user_list += ','+__Group_User__(x)
			else:
				user_list = __Group_User__(x)
	return ','.join(list(set(user_list.split(','))))

#~ 列出所有用户和组的用户
def __User_Group_List__(U_list):
	userlist = __User_List__(U_list)
	grouplist = __Group_List__(U_list)
	uglist = ''
	if userlist != "" and grouplist != "":
		uglist = userlist + ',' + grouplist
	elif  userlist != "" and grouplist == "":
		uglist = userlist
	elif  userlist == "" and grouplist != "":
		uglist = grouplist
	return  __Exclude_Root_List__(list(set(uglist.split(','))))

#~ 列出不包含ROOT所有用户
def __Exclude_Root_List__(U_list):
	if isinstance(U_list,list) != True:
		U_list = U_list.split(',')
	if 'root' in U_list:
		U_list.remove('root')
	return ','.join(list(set(U_list)))


#~ 增加修改用户独立SAMBA配置文件
def __user_purview__(value, u_list, rw):
	u_list = __User_Group_List__(u_list).split(',')
	if len(u_list) > 0:
		for x in u_list:
			if len(x.strip()) > 0:
				xpath = SMB_USER_CONF_PATH + x
				if os.path.exists(xpath) == False:
					f = open(xpath, 'w')
					f.write(USE_CONF)
					f.close()
				e_conf = ConfigParser.ConfigParser()  
				e_conf.read(xpath) 
				if e_conf.has_section(value.name_set) == False:
					e_conf.add_section(value.name_set)
				if value.add_set == True:
					if value.comment_set == '':
						value.comment_set = value.name_set
					e_conf.set(value.name_set, 'comment', value.comment_set)
					e_conf.set(value.name_set, 'path', value.path_set)
					e_conf.set(value.name_set, 'browsable', 'yes')
					e_conf.set(value.name_set, 'inherit permissions', 'yes')
				else:
					e_conf.set(value.name_set, 'comment', deviant(value.name_set, "comment"))
					e_conf.set(value.name_set, 'path', deviant(value.name_set, "path"))
					e_conf.set(value.name_set, 'browsable', 'yes')
					e_conf.set(value.name_set, 'inherit permissions', deviant(value.name_set, "inherit permissions"))				
				if rw == 'r':
					e_conf.set(value.name_set, 'read only', 'yes')
					try:
						e_conf.remove_option(value.name_set,  "writable")
					except:
						pass
				else:
					e_conf.set(value.name_set, 'writable', 'yes')
					try:
						e_conf.remove_option(value.name_set,  "read only")
					except:
						pass
				e_conf.write(open(xpath, 'w'))

#~ 增加共享配置
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
		if value.browsable_set == 'no':
			config.set(value.name_set, 'browsable', value.browsable_set)
		config.set(value.name_set, 'invalid users', value.invalid_set)
		config.set(value.name_set, 'read list', ','.join(read))
		config.set(value.name_set, 'write list', ','.join(write))
		config.set(value.name_set, 'valid users', ','.join(list(set(valid))))
		config.set(value.name_set, 'inherit permissions', 'yes')
		config.write(open(SMB_CONF_PATH, 'w'))
		try:
			os.mkdir(value.path_set) 
			os.chmod(value.path_set, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
		except:
			pass
		__user_purview__(value, read, 'r')
		__user_purview__(value, write, 'w')
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '增加共享 "'+value.name_set+'" 成功！')
	else:
		Export(False, '共享 "'+value.name_set+'" 的名称已经存在！')

#~ 修改用户基本配置
#~ user为用户		
def __user_conf__(value,user):
	if user != '':
		xpath = SMB_USER_CONF_PATH + user
		e_conf = ConfigParser.ConfigParser()  
		e_conf.read(xpath) 
		if value.new_set != "" and value.name_set != value.new_set:
			if e_conf.has_section(value.new_set) == False:
				e_conf.add_section(value.new_set)
				for x in e_conf.options(value.name_set):
					if x == 'comment':
						if value.comment_state == True:
							e_conf.set(value.new_set, 'comment', value.comment_set) 
						else:
							e_conf.set(value.new_set, 'comment', e_conf.get(value.name_set, "comment"))
					elif x == 'browsable':
						if value.browsable_state == True:
							e_conf.set(value.new_set, 'browsable', value.browsable_set) 
						else:
							e_conf.set(value.new_set, 'browsable', e_conf.get(value.name_set, "browsable"))
					else:
						e_conf.set(value.new_set, x, e_conf.get(value.name_set, x))
				e_conf.remove_section(value.name_set)
		else:	
			if e_conf.has_section(value.name_set) == False:
				e_conf.add_section(value.name_set)
				for x in e_conf.options(value.name_set):
					if x == 'comment':
						if value.comment_state == True:
							e_conf.set(value.new_set, 'comment', value.comment_set) 
						else:
							e_conf.set(value.new_set, 'comment', e_conf.get(value.name_set, "comment"))
					elif x == 'browsable':
						if value.browsable_state == True:
							e_conf.set(value.new_set, 'browsable', value.browsable_set) 
						else:
							e_conf.set(value.new_set, 'browsable', e_conf.get(value.name_set, "browsable"))
					else:
						e_conf.set(value.new_set, x, e_conf.get(value.name_set, x))
			else:
				if value.comment_state == True:
					e_conf.set(value.name_set, 'comment', value.comment_set) 
		e_conf.write(open(xpath, 'w'))

#~ 修改一个共享的所有用户基本配置
#~ USR为用户列表
def __User_Basic_Edit__(value, usr):
	user_list = __User_Group_List__(usr).split(',')
	for x in user_list:
		__user_conf__(value, x)

#~ 修改一个共享的共享权限
#~ Original原来的用户
#~ NEW为修改后的用户列表
#~ read只读用户列表
#~ write写权限用户列表
def __Share_Access_Edit__(value, Original, NEW, read, write):
	if value.name_set != "":
		Original = __User_Group_List__(Original).split(',')
		NEW = __User_Group_List__(NEW).split(',')
		for x in Original:
			if x not in NEW:
				__Del_User_Share__(value.name_set, x)
		__user_purview__(value, read, 'r')
		__user_purview__(value, write, 'w')

#~ 修改一个共享的安全策略
#~ U_list用户列表
#~ allow为配置
def __Share_Nasallow_Edit__(name, U_list, allow):
	if name != "" and U_list != "":
		U_list = __User_Group_List__(U_list).split(',')
		if allow != '':
			for x in U_list:
				xpath = SMB_USER_CONF_PATH + x
				e_conf = ConfigParser.ConfigParser()  
				e_conf.read(xpath) 
				e_conf.set(name, 'hosts allow', allow)
				e_conf.write(open(xpath, 'w'))
		else:
			for x in U_list:
				xpath = SMB_USER_CONF_PATH + x
				e_conf = ConfigParser.ConfigParser()  
				e_conf.read(xpath) 
				if e_conf.has_option(name,  "hosts allow"):
					e_conf.remove_option(name,  "hosts allow")
					e_conf.write(open(xpath, 'w'))
			
#~ 从一个用户的配置中删除一个共享
#~ name为共享名称
#~ use为用户名称
def __Del_User_Share__(name, use):
	if use != '':
		xpath = SMB_USER_CONF_PATH + use
		e_conf = ConfigParser.ConfigParser()  
		e_conf.read(xpath)
		try:
			e_conf.remove_section(name)
			e_conf.write(open(xpath, 'w'))
		except:
			pass

def edit(value):
	censor(value.name_set)
	if value.basic_set == True:
		if value.new_set != "" and value.name_set != value.new_set:
			if config.has_section(value.new_set) == False:
				config.add_section(value.new_set) 
				if value.comment_state == True and value.comment_set == '':
					config.set(value.new_set, 'comment', value.comment_set) 
				else:
					config.set(value.new_set, 'comment', deviant(value.name_set, "comment")) 				
				config.set(value.new_set, 'path', deviant(value.name_set, "path") ) 				
				if value.browsable_state == True:
					config.set(value.new_set, 'browsable', value.browsable_set) 
				else:
					config.set(value.new_set, 'browsable', deviant(value.name_set, "browsable")) 				
				config.set(value.new_set, 'invalid users', deviant(value.name_set, "invalid users")) 				
				config.set(value.new_set, 'read list', deviant(value.name_set, "read list")) 				
				config.set(value.new_set, 'write list', deviant(value.name_set, "write list")) 
				config.set(value.new_set, 'valid users', deviant(value.name_set, "valid users"))
				config.set(value.new_set, 'inherit permissions', deviant(value.name_set, "inherit permissions"))
				if deviant(value.name_set, "hosts allow") != '':
					config.set(value.new_set, 'hosts allow', deviant(value.name_set, "hosts allow"))
				config.remove_section(value.name_set)
				__User_Basic_Edit__(value, deviant(value.new_set, "valid users"))
			else:
				 Export(False, '共享 "'+value.new_set+ '" 的名称已存在！')
		else:	
			if value.comment_state == True:
				config.set(value.name_set, 'comment', value.comment_set) 
			if value.browsable_state == True:
				config.set(value.name_set, 'browsable', value.browsable_set)
			if value.comment_state == True or value.browsable_state == True:
				__User_Basic_Edit__(value, deviant(value.name_set, "valid users"))
		config.write(open(SMB_CONF_PATH, 'w'))
		SYSTEM_OUT(RESTART_SMB)
		Export(True, 'NAS "'+value.name_set+'" 的基本信息修改成功！')
	elif value.access_set == True:
		Original = deviant(value.name_set, "valid users")
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
		__Share_Access_Edit__(value, Original, ','.join(list(set(valid))), ','.join(read), ','.join(write))
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '共享NAS "'+value.name_set+'" 的安全策略修改成功！')
	elif value.nasallow_set == True:
		User_List = deviant(value.name_set, "valid users")
		if value.allow_set != '':
			config.set(value.name_set, 'hosts allow', value.allow_set)
			config.write(open(SMB_CONF_PATH, 'w'))
			__Share_Nasallow_Edit__(value.name_set, User_List, value.allow_set)
		else:
			if config.has_option(value.name_set,  "hosts allow"):
				config.remove_option(value.name_set,  "hosts allow")
				config.write(open(SMB_CONF_PATH, 'w'))
				__Share_Nasallow_Edit__(value.name_set, User_List, value.allow_set)
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '共享NAS "'+value.name_set+'" 的安全策略修改成功！')
	elif value.nfsallow_set == True:
		nfs_conf = open (NFS_CONF_PATH, 'r')
		try:
			fileList = nfs_conf.readlines()
			path = config.get(value.name_set, "path")+' '
			file = ''
			exist = True
			for fileLine in fileList:
				if len(fileLine) > 2:
					if len(fileLine.split(path)) > 1:
						if value.allow_set != '':
							file = file + path + value.allow_set +'\n'
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
				operating.write(path +  value.allow_set +'\n')
				operating.close()
				Export(True, '共享NFS "'+value.name_set+'" 的安全策略修改成功！')
			except:
				operating.close()
		else:
			operating = open(NFS_CONF_PATH, 'w')
			try:
				operating.write(file)
				operating.close()
				Export(True, '共享NFS "'+value.name_set+'" 的安全策略修改成功！')
			except:
				operating.close()
		SYSTEM_OUT('exportfs -r')
		xix = open (NFS_CONF_PATH, 'r')
		print xix.read()
		xix.close()
	else:
		AUsage()

#~ name 共享名称
#~ U_list 用户列表
def __Del_Share__(name, U_list):
	if name != "" and U_list != "":
		U_list = __User_Group_List__(U_list).split(',')
		for x in U_list:
			 __Del_User_Share__(name, x)
	
def NASdel(value):
	censor(value.name_set)
	User_List = deviant(value.name_set, "valid users")
	path = config.get(value.name_set, "path")
	result = config.remove_section(value.name_set)
	exist = True
	if result == True:
		nfs_conf = open (NFS_CONF_PATH, 'r')
		try:
			fileList = nfs_conf.readlines()
			file = ''
			for fileLine in fileList:
				if len(fileLine.split(path+' ')) > 1:
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
			try:
				shutil.rmtree(path)
			except:
				pass
		__Del_Share__(value.name_set, User_List)
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '删除" '+value.name_set+' "共享成功！')
	else:
		Export(False, '删除" '+value.name_set+' "共享失败，请重新操作！')

#~ 删除NAS卷时，同时 SMB和NFS 删除配置文件
def get_sync(value):
	out_list = config.sections()
	out_list= [i for i in out_list if i!='global']
	Path = value.path_set+'/'
	for name in out_list:
		if len(deviant(name, "path").split(Path)) > 1:
			User_List = deviant(name, "valid users")
			__Del_Share__(name, User_List)
			config.remove_section(name)
			nfs_conf = open (NFS_CONF_PATH, 'r')
	exist = True
	nfs_conf = open (NFS_CONF_PATH, 'r')
	try:
		fileList = nfs_conf.readlines()
		file = ''
		for fileLine in fileList:
			if len(fileLine.split(Path)) > 1:
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
	SYSTEM_OUT(RESTART_SMB)

def get_high(value):
	if value.guest_state == True or value.privacy_state == True:
		if value.guest_state == True:
			if value.guest_set == 'yes':
				config.set('global', 'map to guest', 'bad user')
			else:
				if config.has_option('global',  "map to guest"):
					try:
						config.remove_option('global',  "map to guest")
					except:
						pass
		if value.privacy_state == True:
			if value.privacy_set == 'yes':
				config.set('global', 'config file', SMB_CONF_PATH+'.%U')
			else:
				if config.has_option('global', 'config file'):
					try:
						config.remove_option('global', 'config file')
					except:
						pass
		config.write(open(SMB_CONF_PATH, 'w'))
		SYSTEM_OUT('/etc/init.d/samba restart &')
		Export(True, 'NAS高级配置修改成功！')
	else:
		json_info = {}
		if config.has_option('global', 'map to guest'):
			json_info['guest'] = 'yes'
		else:
			json_info['guest'] = 'no'
		if config.has_option('global', 'config file'):
			json_info['privacy'] = 'yes'
		else:
			json_info['privacy'] = 'no'
		print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)
	



