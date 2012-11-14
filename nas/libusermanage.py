#!/usr/bin/env python
# -*- coding: utf-8 -*-

#~ cat /opt/samba/conf/rd/libusermanage.py|grep ^#~###-|sed 's/#~###-/#~ /g'
import os
import sys
import commands
import json
import codecs
import ConfigParser
import subprocess

from os.path import join, getsize

reload(sys)
sys.setdefaultencoding('utf8')

SMB_CONF_PATH = "/opt/samba/smb.conf"
USERS_CONF_PATH = "/etc/passwd"
GROUP_CONF_PATH = "/etc/group"
SMBCONFIG_FILE = "/opt/samba/smbpasswd"
RESTART_SMB = 'killall -HUP smbd nmbd'

USE_CONF = """[global]
workgroup = WORKGROUP
server string = %h
security = user
passdb backend = smbpasswd
smb passwd file = /opt/samba/smbpasswd
include = /opt/samba/smb.conf.guest
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

config = ConfigParser.ConfigParser()  
config.read(SMB_CONF_PATH) 

OUT_Array = config.sections()
OUT_Array = [i for i in OUT_Array if i!='global' and i!='系统设置']

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

def deviant(name, Field):
	result = ''
	if Field != '':
		try:
			result = config.get(name, Field)
		except ConfigParser.NoOptionError:
			if Field == 'browsable':
				result = 'yes'
	return result

def AUsage(err=""):
	if err != "":
		print '##命令参数不正确，错误提示： %s' % err
	else:
		print '##命令参数不正确，请检查要执行的命令模式！'
	print """
usermanage --user --add  --name <user_name> --pwd <password> [ --note <Remark> --member <grouplist> ]		##增加用户
	   --user --edit --name <user_name> [--pwd <password> --note <Remark> --member <grouplist>]		##修改用户密码或备注用户所属组
	   --user --list [ --name <user_name --page <int> --coun <int> --search <user name> ]		##输出用户列表
	   --user --del --name <user_name>		##删除用户
	   --user --share --name <user_name> --write  <share list> --read <read list>		##修改用户共享权限
	   --user --check --name <User_name>		##用户重名验证
	   --group --edit --name <group_name> --member <user_list>		##增加组成员
	   --group --share --name <group_name> --write  <write list> --read <read list>		##修改组共享权限
	   --group --list [  --name <group_name> --Page <int> --coun <int> --search <group_name> ]		##输出组列表
	   --group --del --name <group_name>		##删除组
	   --group --check --name <group_name>		##组重名验证
	   --userpwd --name <user_name>	--pwd <Original_password> --newpwd <New_password>	##用户修改密码
"""
	sys.exit(-1)

#~#### 增加用户主程序
def User_Add(value):
	if __Check_System_Internal_User__(USERS_CONF_PATH, value.name_set) == True:
		if __System_User_Check__(value.name_set) == True:
			comstr = 'useradd ' + value.name_set + ' -N -M'
			if value.note_state == True:
				comstr += ' -c ' + value.note_set
			else:
				comstr += ' -c ' + value.name_set
			if value.member_state == True:
				comstr += ' -G ' + __List_Group_Check__(value.member_set)
			SYSTEM_OUT(comstr)
			
		if __Samba_User_Check__(value.name_set) == True:
			if value.pwd_set == '':
				value.pwd_set = '888888'
			SYSTEM_OUT('(echo ' + value.pwd_set + '; echo ' + value.pwd_set + ') | smbpasswd -s -a ' + value.name_set)

			xpath = SMB_CONF_PATH + '.' + value.name_set
			try:
				f = open(xpath, 'w')
				f.write(USE_CONF)
			finally:
				f.close()

			if value.member_state == True:
				__Add_User_initialize_Conf__(value.name_set, value.member_set)
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '用户名创建成功！')
	Export(False, '用户名创建失败，用户名不合理！')


#~#### 修改用户主程序
def User_Edit(value):
	if __Check_Samba_User_licit__(value.name_set):
		if value.pwd_state == True:
			SYSTEM_OUT('(echo ' + value.pwd_set + '; echo ' + value.pwd_set + ') | smbpasswd -s ' + value.name_set)
		if value.note_state == True:
			SYSTEM_OUT('usermod '+ value.name_set + ' -c ' + value.note_set)
		if value.member_state == True:
			SYS_User_Group =  __List_Group_Check__(value.member_set).split(',')
			IN_User_Group = __User_Group_List__(value.name_set).split(',')
			for group_name in IN_User_Group:
				if group_name not in SYS_User_Group and group_name != '':
					SYSTEM_OUT('gpasswd -d '+value.name_set+' '+group_name)
					__Edit_Group_User__(group_name, value.name_set, 'D')
					
			for group_name in SYS_User_Group:
				if group_name not in IN_User_Group and group_name != '':
					SYSTEM_OUT('gpasswd -a '+value.name_set+' '+group_name)
					__Edit_Group_User__(group_name, value.name_set, 'A')
		SYSTEM_OUT(RESTART_SMB)			
		Export(True, '用户 "'+value.name_set+'" 创建成功！')
	else:
		Export(False, '修改失败，用户名不存在！')

#~ 用户列表输出项
class User_list_info():
	def __init__(self):
		self.User_name = ''
		self.User_note = ''
		self.User_Group_List = ''

#~ 用户列表输出项函数
def __User_List_Property__(User_name):
	out = User_list_info()
	out.User_name = User_name
	out.User_note = SYSTEM_OUT('cat /etc/passwd|grep "^'+User_name+':"|cut -d ":" -f5')
	out.User_Group_List = __User_Group_List__(User_name)
	return out

#~#### 用户列表主程序
def User_List(value):
	if value.name_set != '':
		json_info = {}
		if __Check_Samba_User_licit__(value.name_set):
			json_info['User_name'] = value.name_set
			json_info['User_note'] = SYSTEM_OUT('cat /etc/passwd|grep "^'+value.name_set+':"|cut -d ":" -f5')
			json_info['User_Group'] = __User_Group_List__(value.name_set)
			json_info['User_Share_read'] = __User_Share_List__(value.name_set, 'r')
			json_info['User_Share_write'] = __User_Share_List__(value.name_set, 'w')
	else:
		list = []
		User_list = []
		json_info = {'total':0, 'rows':[]}
		open_conf = open(SMBCONFIG_FILE, 'r')
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
		try:
			fileList = open_conf.readlines()
			fileList.sort()  
			for fileLine in fileList:
				user = fileLine.split(':')[0]
				if search_check > 0:
					search_check = len(user.split(search))
				if user != 'root' and user != 'guest' and user != 'pw' and search_check == 0:
					inti += 1
					if inti >= Start and inti < StartEnd or Start == 0:
						list.append(__User_List_Property__(user).__dict__)
				elif user != 'root' and user != 'guest' and user != 'pw' and search_check > 1:
					inti += 1
					if inti >= Start and inti < StartEnd or Start == 0:
						list.append(__User_List_Property__(user).__dict__)
			open_conf.close()
		except:
			open_conf.close()		
		json_info['total'] = inti
		json_info['rows'] = list

	print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)

#~#### 删除用户主程序
def User_Del(name_list):
	if name_list != '':
		name_list = name_list.split(',')
		for name in name_list:
			if __Check_Samba_User_licit__(name):
				SYSTEM_OUT('smbpasswd -x '+ name)
				SYSTEM_OUT('userdel '+ name)
				xpath = SMB_CONF_PATH +'.'+ name
				try:
					os.remove(xpath)
				except:
					pass
					
				for share in OUT_Array:
					__Conf_Share_Del_User__(name, share)	
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '删除成功！')
	Export(False, '删除失败，没有这个用户！')

#~#### 修改用户共享权限主程序
#~ write 为组有权限写的共享目录，read为组有权限读的共享目录
def User_Share(value):
	if __Check_Samba_User_licit__(value.name_set):
		write = []
		read = []
		IN_Share = []
		if value.write_state == True:
			write = __Share_List_Exclude__(value.write_set).split(',')
			IN_Share.extend(write)
		if value.read_state == True:
			read = __Share_List_Exclude__(value.read_set).split(',')
			for i in write:
				if i in read:
					read = filter(lambda x:x !=i,read)
			IN_Share.extend(read)
		IN_Share = __Share_List_Exclude__(IN_Share).split(',')
		Original_Share = __User_Share_List__(value.name_set).split(',')
		for x in Original_Share:
			if x not in IN_Share and x != '':
				__Conf_Share_Del_User__(value.name_set, x)
				__Del_User_Share__(value.name_set, x)
		for x in read:
			__Add_User_initialize_Conf_Operating__(value.name_set, x, 'r')
			__Conf_Share_Edit_Purview__(x, value.name_set, 'r')
		for x in write:
			__Add_User_initialize_Conf_Operating__(value.name_set, x, 'w')
			__Conf_Share_Edit_Purview__(x, value.name_set, 'w')
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '"'+value.name_set+'" 的共享权限修改成功！')
	Export(False, '修改失败，没有找到这个用户！')

#~#### 验证用户重名主程序
def User_Check(value):
	if __Samba_User_Check__(value.name_set) == True:
		Export(True, '用户名可用！')
	else:
		Export(False, '用户名已存在！')

#~#### 修改用户组主程序
#~ 当为新用户名时，自动增加
def Group_Edit(value):
	Status = False
	if __Check_System_Internal_User__(GROUP_CONF_PATH, value.name_set) == True:
		if __System_Group_Check__(value.name_set):
			SYSTEM_OUT('groupadd -f '+value.name_set)
			Status = True
		if value.member_state == True:
			Group_List = __Group_User__(value.name_set).split(',')
			IN_Group = value.member_set.split(',')
			for user in Group_List:
				if user not in IN_Group and user != '':
					SYSTEM_OUT('gpasswd -d '+user+' '+value.name_set)
					__Edit_Group_User__(value.name_set, user, 'D')

			for user in IN_Group:
				if user not in Group_List and user != '':
					SYSTEM_OUT('gpasswd -a '+user+' '+value.name_set)
					__Edit_Group_User__(value.name_set, user, 'A')
		SYSTEM_OUT(RESTART_SMB)
		if Status == True:
			Export(True, '"'+value.name_set+'" 用户组增加成功！')
		else:
			Export(True, '"'+value.name_set+'" 用户组修改成功！')			
	Export(False, '修改失败，没有找到这个用户组！')

#~ 用户列表输出项
class Group_list_info():
	def __init__(self):
		self.Group_name = ''
		self.Group_User_List = ''

#~#### 用户组列表组主程序
def Group_List(value):
	if value.name_set != '':
		json_info = {}
		if __System_Group_Check__(value.name_set) == False:
			Group_name = '@'+value.name_set
			json_info['Group_name'] = value.name_set
			json_info['Group_user'] = __Group_User__(value.name_set)
			json_info['Group_Share_read'] = __User_Share_List__(Group_name, 'r')
			json_info['Group_Share_write'] = __User_Share_List__(Group_name, 'w')
	else:
		list = []
		User_list = []
		json_info = {'total':0, 'rows':[]}
		open_conf = open(GROUP_CONF_PATH, 'r')
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
		try:
			fileList = open_conf.readlines()
			fileList.sort()  
			for fileLine in fileList:
				Grout_Cont = fileLine.split(':')
				Grout_id = int(Grout_Cont[2])
				if Grout_id > 1000 and Grout_id < 60001:
					group = Grout_Cont[0]
					if search_check > 0:
						search_check = len(group.split(search))
					if search_check == 0:
						inti += 1
						if inti >= Start and inti < StartEnd or Start == 0:
							out = Group_list_info()
							out.Group_name = group
							out.Group_User_List =  __Group_User__(group)
							list.append(out.__dict__)
					elif search_check > 1:
						inti += 1
						if inti >= Start and inti < StartEnd or Start == 0:
							out = Group_list_info()
							out.Group_name = group
							out.Group_User_List =  __Group_User__(group)
							list.append(out.__dict__)
			open_conf.close()
		except:
			open_conf.close()		
		json_info['total'] = inti
		json_info['rows'] = list

	print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)

#~#### 删除用户组主程序
def Group_Del(name_list):
	if name_list != '':
		name_list = name_list.split(',')
		for group in name_list:
			if __System_Group_Check__(group) == False:
				name = '@'+group
				for share in OUT_Array:
					Conf_valid = deviant(share, 'valid users').split(',')
					if name in Conf_valid:
						Conf_valid.remove(name)
						config.set(share, 'valid users', ','.join(Conf_valid))
						share_write = deviant(share, 'write list').split(',')
						if name in share_write:
							share_write.remove(name)
							config.set(share, 'write list', ','.join(share_write))
						else:
							share_read = deviant(share, 'read list').split(',')
							share_read.remove(name)
							config.set(share, 'read list', ','.join(share_read))
							
						config.write(open(SMB_CONF_PATH, 'w'))	

					User_List = __Group_User__(group).split(',')
					for user in User_List:
						if __Share_limits__(share, user, 'V'):
							__Del_User_Share__(user, share)
				try:
					SYSTEM_OUT('groupdel '+ group)
				except:
					pass
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '用户组删除成功！')
	Export(False, '用户组删除失败！')


#~#### 修改用户组共享权限主程序
#~ write 为组有权限写的共享目录，read为组有权限读的共享目录
def Group_Share(value):
	if __System_Group_Check__(value.name_set) == False:
		group = '@'+value.name_set
		group_user_list = __Group_User__(value.name_set).split(',')
		write = []
		read = []
		IN_Share = []
		if value.write_state == True:
			write = __Share_List_Exclude__(value.write_set).split(',')
			IN_Share.extend(write)
		if value.read_state == True:
			read = __Share_List_Exclude__(value.read_set).split(',')
			for i in write:
				if i in read:
					read = filter(lambda x:x !=i,read)
			IN_Share.extend(read)
		IN_Share = __Share_List_Exclude__(IN_Share).split(',')
		Original_Share = __User_Share_List__(group).split(',')
		for x in Original_Share:
			if x not in IN_Share and x != '':
				__Conf_Share_Del_User__(group, x)
				for user in group_user_list:
					__Del_User_Share__(user, x)
		for x in read:
			if x != '':
				for user in group_user_list:
					__Add_User_initialize_Conf_Operating__(user, x, 'r')
				__Conf_Share_Edit_Purview__(x, group, 'r')
		for x in write:
			if x != '':
				for user in group_user_list:
					__Add_User_initialize_Conf_Operating__(user, x, 'w')
				__Conf_Share_Edit_Purview__(x, group, 'w')
		SYSTEM_OUT(RESTART_SMB)
		Export(True, '"'+value.name_set+'" 的共享权限修改成功！')
	Export(False, '修改失败，没有找到这个用户组！')

#~#### 验证用户组重名主程序
def Group_Check(value):
	if __System_Group_Check__(value.name_set) == True:
		Export(True, '组名称可用！')
	else:
		Export(False, '组名称已存在！')

#~#### 验证用户组重名主程序
def User_Edit_Pwd(value):
	if __Check_Samba_User_licit__(value.name_set):
		if value.pwd_state and value.newpwd_state:
			pwd = value.pwd_set.strip()
			newpwd = value.newpwd_set.strip()
			if __System_User_Check__('pw'):
				SYSTEM_OUT('useradd pw -N -M -u 996')
				SYSTEM_OUT('(echo mkmkmk; echo mkmkmk) | smbpasswd -s -a pw')
			SYSTEM_OUT('(echo '+pwd+'; echo '+pwd+') | smbpasswd -s pw')
			if __Read_Samba_User_pwd__('pw', 3) == __Read_Samba_User_pwd__(value.name_set, 3):
				if newpwd != pwd:
					SYSTEM_OUT('(echo '+newpwd+'; echo '+newpwd+') | smbpasswd -s '+value.name_set)
				Export(True, '密码修改成功')
	Export(False, '用户名或原密码不正确！')

#~###-验证是否是用户内置帐号和组	__Check_System_Internal_User__(File, name):
def __Check_System_Internal_User__(File, name):
	Status = True
	if name != '' and File != '':
		open_conf = open(File, 'r')
		try:
			fileList = open_conf.readlines()
			for fileLine in fileList:
				if fileLine.split(':')[0] == name:
					if int(fileLine.split(':')[2]) < 1001 or int(fileLine.split(':')[2]) > 60000:
						Status = False
					break
			open_conf.close()
		except:
			open_conf.close()		
	return Status
	
#~###-验证系统用户重名模块	__System_User_Check__(name):
def __System_User_Check__(name):
	Status = True
	if name != '':
		open_conf = open(USERS_CONF_PATH, 'r')
		try:
			fileList = open_conf.readlines()
			for fileLine in fileList:
				if fileLine.split(':')[0] == name:
					Status = False
					break
			open_conf.close()
		except:
			open_conf.close()		
	return Status

#~###-验证SAMBA用户重名模块	__Samba_User_Check__(name):
def __Samba_User_Check__(name):
	Status = True
	if name != '':
		open_conf = open(SMBCONFIG_FILE, 'r')
		try:
			fileList = open_conf.readlines()
			for fileLine in fileList:
				if fileLine.split(':')[0] == name:
					Status = False
					break
			open_conf.close()
		except:
			open_conf.close()		
	return Status
	
#~###-读出一个SAMBA用户的密码	__Read_Samba_User_pwd__(name):
def __Read_Samba_User_pwd__(name, Row):
	OUT = ''
	Row = int(Row)
	if name != '':
		open_conf = open(SMBCONFIG_FILE, 'r')
		try:
			fileList = open_conf.readlines()
			for fileLine in fileList:
				user = fileLine.split(':')
				if user[0] == name:
					OUT= user[Row]
					break
			open_conf.close()
		except:
			open_conf.close()		
	return OUT

#~###-验证是否是合法的SAMBA用户	__Check_Samba_User_licit__(name):
def __Check_Samba_User_licit__(name):
	Status = False
	if __Samba_User_Check__(name) == False and name != 'root' and name != 'guest' and name != 'pw':
		Status = True
	return Status

#~###-从列表中取出系统中存在的用户	__List_Samba_User_Check__(User_list):
def __List_Samba_User_Check__(User_list):
	if isinstance(User_list,list) != True:
		User_list = User_list.split(',')
	remove_user = []
	for user in User_list:
		if __Samba_User_Check__(user):
			remove_user.append(user)
	for x in remove_user:
		User_list.remove(x)
	return ','.join(User_list)

#~###-从列共享表中取出存在的共享	__Share_List_Exclude__(IN_Share_list):
def __Share_List_Exclude__(IN_Share_list):
	if isinstance(IN_Share_list,list) != True:
		IN_Share_list = IN_Share_list.split(',')
	OUT_Share_list = []
	for share in IN_Share_list:
		if share in OUT_Array:
			OUT_Share_list.append(share)
	return ','.join(OUT_Share_list)


#~###-验证系统用户组重名模块	__System_Group_Check__(name):
def __System_Group_Check__(name):
	Status = True
	if name != '':
		open_conf = open(GROUP_CONF_PATH, 'r')
		try:
			fileList = open_conf.readlines()
			for fileLine in fileList:
				if fileLine.split(':')[0] == name:
					Status = False
					break
			open_conf.close()
		except:
			open_conf.close()		
	return Status

#~###-从列表中取出系统中存在的用户组	__List_Group_Check__(group_list):
def __List_Group_Check__(group_list):
	if isinstance(group_list,list) != True:
		group_list = group_list.split(',')
	remove_group = []
	for group in group_list:
		if __System_Group_Check__(group):
			remove_group.append(group)
	for x in remove_group:
		group_list.remove(x)
	return ','.join(group_list)

#~###-列出一个用户或一个组的共享	__User_Share_List__(name):
def __User_Share_List__(name, rwv='v'):
	Share_List = []
	if rwv == 'r':
		users = 'read list'
	elif rwv == 'w':
		users = 'write list'
	else:
		users = 'valid users'		
	for x in OUT_Array:
		if name in deviant(x, users).split(','):
			Share_List.append(x)
	return ','.join(Share_List)

#~###-为组用户，增加用户初始配置	__Add_User_initialize_Conf__(User_name, Group_List):
def __Add_User_initialize_Conf__(User_name, Group_List):
	if isinstance(Group_List,list) != True:
		Group_List = Group_List.split(',')
	for Group_name in Group_List:
		Group_name = '@'+Group_name
		for x in OUT_Array:
			Conf_valid = deviant(x, 'valid users').split(',')
			if Group_name in Conf_valid:
				if Group_name in deviant(x, 'write list').split(','):
					rw = 'w'
				else:
					rw = 'r'
				__Add_User_initialize_Conf_Operating__(User_name, x, rw)

#~###-增加用户初始配置，操作函数	__Add_User_initialize_Conf_Operating__(User_name, Share_name, rw):
def __Add_User_initialize_Conf_Operating__(User_name, Share_name, rw):
	Conf_valid = __GroupList_User_List__(deviant(Share_name, 'valid users'))
	xpath = SMB_CONF_PATH +'.'+ User_name
	if os.path.exists(xpath) == False:
		f = open(xpath, 'w')
		f.write(USE_CONF)
		f.close()
	e_conf = ConfigParser.ConfigParser()  
	e_conf.read(xpath) 
	if e_conf.has_section(Share_name) == False:
		e_conf.add_section(Share_name)
	e_conf.set(Share_name, 'comment', deviant(Share_name, "comment"))
	e_conf.set(Share_name, 'path', deviant(Share_name, "path"))
	e_conf.set(Share_name, 'browsable', 'yes')
	e_conf.set(Share_name, 'inherit permissions', deviant(Share_name, "inherit permissions"))				
	if rw == 'r' and User_name not in Conf_valid:
		e_conf.set(Share_name, 'read only', 'yes')
		try:
			e_conf.remove_option(Share_name,  "writable")
		except:
			pass
	else:
		e_conf.set(Share_name, 'writable', 'yes')
		try:
			e_conf.remove_option(Share_name,  "read only")
		except:
			pass
	e_conf.write(open(xpath, 'w'))

#~###-列出组中的所有用户	__Group_User__(group):
def __Group_User__(group):
	conf = open (GROUP_CONF_PATH, 'r')
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

#~###-列出多个组的所有用户	__GroupList_User_List__(UG_Name):
#~ 输出为列表
def __GroupList_User_List__(UG_Name):
	if isinstance(UG_Name,list) != True:
		UG_Name = UG_Name.split(',')
	Out_List = []
	for x in UG_Name:
		group = x.split('@')
		if len(group) > 1:
			Out_List.extend(__Group_User__(group[1]).split(','))
	return list(set(Out_List))

#~###-列出一个用户所属的组	__User_Group_List__(User):
def __User_Group_List__(User):
	OUT_List = ''
	try:
		Group_list = SYSTEM_OUT('groups '+User).split(':')[1].strip().split(' ')
		Group_list.remove('users')
		OUT_List = ','.join(Group_list)
	except:
		pass
	return OUT_List

#~###-修改组用户函数	__Edit_Group_User__(group,user,AD):
def __Edit_Group_User__(group,user,AD):
	Group_name = '@'+group
	for x in OUT_Array:
		Conf_valid = deviant(x, 'valid users').split(',')
		if Group_name in Conf_valid and __Share_limits__(x, user, 'V'):
			if AD == 'D':
				__Del_User_Share__(user, x)
			else:
				if Group_name in deviant(x, 'write list').split(','):
					rw = 'w'
				else:
					rw = 'r'
				__Add_User_initialize_Conf_Operating__(user, x, rw)

#~###-在主配置文件的共享中删除一个用户名或一个组名	__Conf_Share_Del_User__(name, share):
#~ name为用户名称、Share为共享名称
def __Conf_Share_Del_User__(name, share):
	Conf_valid = deviant(share, 'valid users').split(',')
	if name in Conf_valid:
		Conf_valid.remove(name)
		config.set(share, 'valid users', ','.join(Conf_valid))
		share_write = deviant(share, 'write list').split(',')
		if name in share_write:
			share_write.remove(name)
			config.set(share, 'write list', ','.join(share_write))
		else:
			share_read = deviant(share, 'read list').split(',')
			share_read.remove(name)
			config.set(share, 'read list', ','.join(share_read))
			
		config.write(open(SMB_CONF_PATH, 'w'))	
				
#~###-删除一个用户的一个共享目录	__Del_User_Share__(User_name, Share_name):
def __Del_User_Share__(User_name, Share_name):
	Conf_valid = deviant(Share_name, 'valid users')
	if  User_name not in __GroupList_User_List__(Conf_valid):
		xpath = SMB_CONF_PATH +'.'+ User_name
		if os.path.exists(xpath):
			e_conf = ConfigParser.ConfigParser()  
			e_conf.read(xpath)
			try:
				e_conf.remove_section(Share_name)
				e_conf.write(open(xpath, 'w'))
			except:
				pass

#~###-主配置文件的增加共享权限	__Conf_Share_Edit_Purview__(share, user, rw):
def __Conf_Share_Edit_Purview__(share, user, rw):
	write = list(set(deviant(share, 'write list').split(',')))
	read = list(set(deviant(share, 'read list').split(',')))
	valid = list(set(deviant(share, 'valid users').split(',')))
	if rw == 'r':
		if user not in read:
			read.append(user)
		if user in write:
			write.remove(user)
		if user not in valid:
			valid.append(user)
	else:
		if user not in write:
			write.append(user)
		if user in read:
			read.remove(user)
		if user not in valid:
			valid.append(user)
	config.set(share, 'read list', ','.join(list(set(read))))
	config.set(share, 'write list', ','.join(list(set(write))))
	config.set(share, 'valid users', ','.join(list(set(valid))))
	config.write(open(SMB_CONF_PATH, 'w'))	
	
#~###-列出共享的访问权限	__Share_limits__(Share_name, user, RWV):
#~ 输出为True时为共享用户列表没有这个用户
def __Share_limits__(Share_name, user, RWV):
	OUT_List = ''
	Status = True
	if RWV == 'R':
		OUT_List = deviant(Share_name, 'read list').split(',')
	elif  RWV == 'W':
		OUT_List = deviant(Share_name, 'write list').split(',')
	elif  RWV == 'V':
		OUT_List = deviant(Share_name, 'valid users').split(',')
	if user in OUT_List:
		Status = False
	return Status

