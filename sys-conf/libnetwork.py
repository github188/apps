#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import stat
import commands
import getopt
import json
import ConfigParser
import subprocess
import codecs

reload(sys)
sys.setdefaultencoding('utf8')

NET_PATH='/opt/etc/network/'
CONF_File = 'interfaces.conf'
INTERFACESS_File = 'interfaces'
CONF_File_PATH=NET_PATH+CONF_File
INTERFACESS_File_PATH = NET_PATH+INTERFACESS_File
BOND_CONF = NET_PATH+'bond_conf.sh'
DNS_CONFIG_PATH = '/opt/etc/resolv.conf'

BOND_LIST = ['bond0', 'bond1']

def Export(ret = True, msg = ''):
	ret_msg = {'status':True, 'msg':''}
	ret_msg['status'] = ret
	ret_msg['msg'] = msg
	print json.dumps(ret_msg, encoding="UTF-8", ensure_ascii=False)
	sys.exit(-1)

#~ eth接口列表
def __NET_LIST__():
	s = subprocess.Popen('ls /sys/class/net/|grep eth', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	p = s.stdout.readlines()
	p = ','.join(p).replace('\n','')
	return p.split(',')

#~ 当配置文件目录不存在时创建目录
if os.path.exists(NET_PATH) == False:
	try:
		os.makedirs(NET_PATH)
	except:
		pass

#~ 字段读取
def __deviant__(name, Field):
	result = ''
	if Field != '':
		try:
			result = config.get(name, Field)
		except:
			pass
	return result
	
#~ 检查名称是否成在！
def __censor__(name):
	if name == '':
		Export(False, '名称不能为空！')
	if config.has_section(name) == False:
		Export(False, '找不到名称！')

#~#### 恢复默认值
def Default(iface=""):
	if iface == '':
		p = open(CONF_File_PATH, 'w')
		try:
			p.write('')
		finally:
			p.close()
		Det = ConfigParser.ConfigParser()  
		Det.read(CONF_File_PATH)
		ETC_NIC = __NET_LIST__()
		All_NIC = ETC_NIC+BOND_LIST
		All_NIC.append('dns')
		i = 0
		for name in All_NIC:
			if Det.has_section(name) == False:
				Det.add_section(name)
			if name in ETC_NIC:
				Det.set(name, 'mode', 'static')
				Det.set(name, 'address', '192.168.%s.100'%i)
				Det.set(name, 'netmask', '255.255.255.0')
				Det.set(name, 'bond', '')
				i = i + 1
			elif name == 'dns':
				Det.set(name, 'address', '202.106.0.20')
			else:
				Det.set(name, 'mode', 'no')
				Det.set(name, 'iflist', '')
		Det.write(open(CONF_File_PATH, 'w'))
		Sys_interfaces = '/etc/network/'+INTERFACESS_File
		try:
			if os.path.exists(Sys_interfaces) == False:
				os.symlink(INTERFACESS_File_PATH, Sys_interfaces)
			else:
				if os.path.islink(Sys_interfaces) == False:
					os.remove(Sys_interfaces)
					os.symlink(INTERFACESS_File_PATH, Sys_interfaces)
		except:
			pass
		Sys_resolv = '/etc/resolv.conf'
		try:
			if os.path.exists(Sys_resolv) == False:
				os.symlink(DNS_CONFIG_PATH, Sys_resolv)
			else:
				if os.path.islink(Sys_resolv) == False:
					os.remove(Sys_resolv)
					os.symlink(DNS_CONFIG_PATH, Sys_resolv)
		except:
			pass
	else:
		if iface in __NET_LIST__():
			config.set(iface, 'mode', 'static')
			config.set(iface, 'address', '192.168.0.100')
			config.set(iface, 'netmask', '255.255.255.0')
			try:
				config.remove_option(iface, 'gateway')
			except:
				pass	
			config.set(iface, 'bond', '')
			config.write(open(CONF_File_PATH, 'w'))
	OUT_CONF()
	
def OUT_CONF():
	def deviant(name, Field):
		result = ''
		if Field != '':
			try:
				result = OUT.get(name, Field)
			except:
				pass
		return result

	etc_str= """#请不要直接修改本配置文件
#修改IP地址请使用 network 命令\n
auto lo
iface lo inet loopback\n
"""
	bond_str = '#!/bin/bash\n\n'
	dns_str = ''

	OUT = ConfigParser.ConfigParser()  
	OUT.read(CONF_File_PATH) 
	olist = OUT.sections()
	olist.sort() 
	for name in olist:
		if name in BOND_LIST:
			if deviant(name, 'mode') != 'no':
				bond_str = bond_str + 'echo +' + name  + ' > /sys/class/net/bonding_masters\n'
				bond_str = bond_str + 'echo ' + deviant(name, 'mode')  + ' > /sys/class/net/' + name  + '/bonding/mode\n'
				bond_str = bond_str + 'echo 2 > /sys/class/net/' + name  + '/bonding/xmit_hash_policy\n'
				bond_str = bond_str + 'ifconfig ' + name  + ' ' + deviant(name, 'address')  + ' netmask ' + deviant(name, 'netmask')  + ' up\n'
				bond_str = bond_str + 'echo 100 > /sys/class/net/' + name  + '/bonding/miimon\n'
				iflist = deviant(name, 'iflist').split(',')
				if len(iflist) > 0:
					for i in iflist:
						bond_str = bond_str + 'ifconfig ' + i + ' 0.0.0.0 > /dev/null\n'
						bond_str = bond_str + 'ifdown ' + i + ' > /dev/null\n'
						bond_str = bond_str + 'ip rule del table ' + i + '\n'
						bond_str = bond_str + 'echo +' + i + ' > /sys/class/net/' + name  + '/bonding/slaves\n'
						
						bond_str = bond_str + 'route_str=`ip route|grep "'+i+'  proto"|cut -d " " -f1,2,3`\n'
						bond_str = bond_str + 'if [ "$route_str" !=  "" ]; then\n'
						bond_str = bond_str + '	ip ro del $route_str\n'
						bond_str = bond_str + 'fi\n'
				bond_str = bond_str + '\n'
				if deviant(name, 'gateway') != '':
						bond_str = bond_str + 'route add default gw '+deviant(name, 'gateway')+' dev ' + name  + '\n\n'
		elif name == 'dns':
			dns = deviant(name, 'address').split(',')
			if len(dns) > 0:
				for x in dns:
					dns_str = dns_str + 'nameserver ' + x + '\n'
		else:
			mode = deviant(name, 'mode') 
			etc_str = etc_str + 'auto ' + name  + '\n'
			etc_str = etc_str + 'iface ' + name  + ' inet ' + mode  + '\n'
			if mode != 'dhcp':
				etc_str = etc_str + 'address ' + deviant(name, 'address')  + '\n'
				etc_str = etc_str + 'netmask ' + deviant(name, 'netmask')  + '\n'
				if deviant(name, 'gateway') != '':
					etc_str = etc_str + 'gateway ' +  deviant(name, 'gateway')  + '\n'
			etc_str = etc_str + '\n'
	#~ 保存BODN配置
	bond_file = open(BOND_CONF, 'w')
	try:
		bond_file.write(bond_str)
	finally:
		bond_file.close()
	os.chmod(BOND_CONF, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)

	#~ 保存DNS配置
	dns_file = open(DNS_CONFIG_PATH, 'w')
	try:
		dns_file.write(dns_str)
	finally:
		dns_file.close()

	#~ 保存网络配置
	etc_file = open(INTERFACESS_File_PATH, 'w')
	try:
		etc_file.write(etc_str)
	finally:
		etc_file.close()
	

#~ 当配置XML文件不存在时，创建默认文件
if os.path.exists(CONF_File_PATH) == False:
	Default()

config = ConfigParser.ConfigParser()  
config.read(CONF_File_PATH) 

#~ 验证网关和IP地址是不是在同一网段
def Gw_Check(value):
	nic = value.iface_set
	ip = value.ip_set
	mask = value.mask_set
	gw = value.gw_set
	if mask == '':
		mask = __deviant__(nic, 'netmask')
	if mask == '':
		mask = '255.255.255.0'
	if ip == '':
		ip = __deviant__(nic, 'address')
	if ip == '':
		Export(False, 'IP地址不能为空')
	ipadd_items = ip.split('.')
	ipadd_int = 0
	for itemadd in ipadd_items:
		ipadd_int = ipadd_int * 256 + int(itemadd)

	ipmask_items = mask.split('.')
	ipmask_int = 0
	for itemmask in ipmask_items:
		ipmask_int = ipmask_int * 256 + int(itemmask)
	
	ipgw_items = gw.split('.')
	ipgw_int = 0
	for itemgw in ipgw_items:
		ipgw_int = ipgw_int * 256 + int(itemgw)

	total = 256 ** 4
	subnet_int = total - ipmask_int
	net_int = int(ipadd_int / subnet_int) * subnet_int
	
	iparea_Start = int(net_int)+1
	iparea_End = int(net_int) + int(subnet_int) - 1

	if ipgw_int < iparea_Start or  ipgw_int >= iparea_End:
		Export(False, '网关和IP地址不属于同一网段.')
		sys.exit(-1)


#~ 执行系统命令并输出结果
def SYSTEM_OUT(com):
	s = ''
	try:
		p = subprocess.Popen(com, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		s = p.stdout.readline()
		s = s.replace('\n','')
	except:
		pass
	return s
	
def AUsage(err=""):
	if err != "":
		print '##命令参数不正确，错误提示： %s' % err
	else:
		print '##命令参数不正确，请检查要执行的命令模式！'
	print """
network --list < --iface <name> | --filter |--intbond >
	--ifconfig --iface <name> < --dhcp  | [ --ip <address> --mask <netmask> --gw <gateway> ] > 		##设置IP地址
	--bond --iface <bond0|bond1> --nic <eth1,eth2,eth3,eth4,.....> --mode <bonding mode(1|2|4)> --ip <address> --mask <netmask> [--gw<gateway>]		###配置启用BOND接口
	--bond --remove --iface <bond0|bond1>			###卸载bond接口
	--dns < --val <nameserver1,nameserver2> >
	--default [--iface <eth0> ]		###恢复默认
	--status		###网络接口状态列表
	--niccoun		###输出网卡数量
"""
	sys.exit(-1)

#~#### 保存配置
def __Conf_Save__():
	config.write(open(CONF_File_PATH, 'w'))
	OUT_CONF()
	
#~#### 网络接口数量
def NIC_INT_Count():
	print len(__NET_LIST__())

class nic_info():
	def __init__(self):
		self.Network_Name = ''
		self.Network_Mode = ''
		self.Network_IP = ''
		self.Network_Mask = ''
		self.Network_Gateway = ''
		self.Network_Bond = ''
		self.Network_Iflist = ''
	
#~#### 网络接口列表
def NIC_List(value):
	if value.iface_set != '':
		name = value.iface_set
		json_info = {}
		json_info['Network_Name'] = name
		json_info['Network_Mode'] = __deviant__(name, 'mode')
		if __deviant__(name, 'mode') == 'dhcp':
			eth =SYSTEM_OUT('ifconfig ' +name+ '|grep \'inet addr:\'|tr -s \' \'|tr -d \'\n\'').split(' ')
			Network_IP = ''
			Network_Mask = ''
			if len(eth) > 3:
				Network_IP = eth[2].split(':')[1]
				Network_Mask = eth[4].split(':')[1]
			json_info['Network_IP'] = Network_IP
			json_info['Network_Mask'] = Network_Mask
			json_info['Network_Gateway'] = SYSTEM_OUT('ip route|grep \'dev ' + name + '\'|grep \'^default\'|awk \'{print $3}\'|tr -d \'\n\'')
		else:
			json_info['Network_IP'] = __deviant__(name, 'address')
			json_info['Network_Mask'] = __deviant__(name, 'netmask')
			json_info['Network_Gateway'] = __deviant__(name, 'gateway')
		json_info['Network_Bond'] = __deviant__(name, 'bond')
		json_info['Network_Iflist'] = __deviant__(name, 'iflist')
		print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)
	elif value.intbond_set == True:
		list = []
		for name in __NET_LIST__():
			if __deviant__(name, 'bond') != '':
				list.append(name)
		print ','.join(list)
	else:
		list = []
		json_info = {'total':0, 'rows':[]}
		inti = 0
		NET_LIST_NEW = __NET_LIST__()
		if len(__NET_LIST__()) > 4 and value.filter_set == True:
			NET_LIST_NEW= [i for i in NET_LIST_NEW if i!='eth0']
		for name in NET_LIST_NEW:
			if __deviant__(name, 'bond') == '':
				nic = nic_info()
				nic.Network_Name = name
				nic.Network_Mode =  __deviant__(name, 'mode')
				if __deviant__(name, 'mode') == 'dhcp':
					eth =SYSTEM_OUT('ifconfig ' +name+ '|grep \'inet addr:\'|tr -s \' \'|tr -d \'\n\'').split(' ')
					Network_IP = ''
					Network_Mask = ''
					if len(eth) > 3:
						Network_IP = eth[2].split(':')[1]
						Network_Mask = eth[4].split(':')[1]
					nic.Network_IP = Network_IP
					nic.Network_Mask = Network_Mask
					nic.Network_Gateway =  SYSTEM_OUT('ip route|grep \'dev ' + name + '\'|grep \'^default\'|awk \'{print $3}\'|tr -d \'\n\'')
				else:
					nic.Network_IP =  __deviant__(name, 'address')
					nic.Network_Mask =  __deviant__(name, 'netmask')
					nic.Network_Gateway =  __deviant__(name, 'gateway')				
				nic.Network_Bond =  __deviant__(name, 'bond')
				nic.Network_Iflist =  __deviant__(name, 'iflist')
				list.append(nic.__dict__)
				inti += 1
		if value.filter_set == False:
			for name in BOND_LIST:
				nic = nic_info()
				nic.Network_Name = name
				nic.Network_Mode =  __deviant__(name, 'mode')
				if __deviant__(name, 'mode') == 'dhcp':
					eth =SYSTEM_OUT('ifconfig ' +name+ '|grep \'inet addr:\'|tr -s \' \'|tr -d \'\n\'').split(' ')
					Network_IP = ''
					Network_Mask = ''
					if len(eth) > 3:
						Network_IP = eth[2].split(':')[1]
						Network_Mask = eth[4].split(':')[1]
					nic.Network_IP = Network_IP
					nic.Network_Mask = Network_Mask
					nic.Network_Gateway =  SYSTEM_OUT('ip route|grep \'dev ' + name + '\'|grep \'^default\'|awk \'{print $3}\'|tr -d \'\n\'')
				else:
					nic.Network_IP =  __deviant__(name, 'address')
					nic.Network_Mask =  __deviant__(name, 'netmask')
					nic.Network_Gateway =  __deviant__(name, 'gateway')				
				nic.Network_Bond =  __deviant__(name, 'bond')
				nic.Network_Iflist =  __deviant__(name, 'iflist')
				list.append(nic.__dict__)
				inti += 1
		json_info['total'] = inti
		json_info['rows'] = list
		print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)

#~#### IP设置
def NIC_Set(value):
	name = value.iface_set
	if name in __NET_LIST__():
		if __deviant__(name, 'bond') == '':
			if value.dhcp_set:
				config.set(name, 'mode',  'dhcp')
				__Conf_Save__()
				os.system('ifdown '+ name +' > /dev/null')
				os.system('ifup '+ name +' > /dev/null')
				os.system('advanceroute ' + name)
			else:
				ip = value.ip_set
				mask = value.mask_set
				gw = value.gw_set
				config.set(name, 'mode',  'static')
				if value.ip_state == True:
					config.set(name, 'address',  ip)
				else:
					ip = __deviant__(name, 'address')
				if value.mask_state == True:
					config.set(name, 'netmask',  mask)
				else:
					mask = __deviant__(name, 'netmask')
				config.set(name, 'gateway',  gw)
				SYSTEM_OUT('ifconfig ' + name + ' '  + ip +' netmask '  + mask)
				if len(gw) > 0:
					SYSTEM_OUT('route add default gw '+gw+' dev ' + name)
				__Conf_Save__()
				os.system('advanceroute ' + name)
			Export(True, '设置成功！')
		else:
			Export(False, '该接口是聚合组成员，不能设置！')
	else:
		Export(False, '接口名称不存在！')

#~#### BOND接口设置
def BOND_Set(value):
	name = value.iface_set
	ip = value.ip_set
	mask = value.mask_set
	gw = value.gw_set
	if value.iface_set in BOND_LIST:
		if value.remove_set == False:
			Nic = value.nic_set
			if Nic == '' and __deviant__(name, 'mode')  != 'no':
				Nic = __deviant__(name, 'iflist')
				for e in Nic.split(','):
					if len(e) > 0:
						SYSTEM_OUT('echo -'+e+' > /sys/class/net/'+name+'/bonding/slaves')
						os.system('ifup '+e+' > /dev/null')
			Nic_Array = Nic.split(',')
			if len(Nic_Array) > 1:
				if value.ip_state == True:
					config.set(name, 'address',  ip)
				else:
					ip = __deviant__(name, 'address')
				if value.mask_state == True:
					config.set(name, 'netmask',  mask)
				else:
					mask = __deviant__(name, 'netmask')
				config.set(name, 'gateway',  gw)
				config.set(name, 'iflist',  Nic)
				config.set(name, 'mode', value.mode_set)
				if os.path.exists('/sys/class/net/'+name) == False:
					SYSTEM_OUT('echo +'+name+' > /sys/class/net/bonding_masters')
				if int(SYSTEM_OUT('ifconfig|grep "^'+name+'"|wc -l')) > 0:
					os.system('ifconfig '+name+' down > /dev/null')
				SYSTEM_OUT('echo '+value.mode_set+' > /sys/class/net/'+name+'/bonding/mode')
				os.system('echo 2 > /sys/class/net/' +name+ '/bonding/xmit_hash_policy')
				SYSTEM_OUT('ifconfig '+name+' '+ip+' netmask '+mask+' up')
				os.system('advanceroute ' + name)
				if len(gw) > 0:
					SYSTEM_OUT('route add default gw '+gw+' dev ' + name)
				for x in  Nic_Array:
					if len(x) > 0:
						config.set(x, 'bond',  name)
						os.system('ip rule del table ' +x)
						os.system('ifconfig '+x+' 0.0.0.0 > /dev/null')
						os.system('ifdown '+x+' > /dev/null')
						SYSTEM_OUT('echo +'+x+' > /sys/class/net/'+name+'/bonding/slaves')
						route_str = SYSTEM_OUT('ip route|grep "'+x+'  proto"|cut -d " " -f1,2,3')
						if len(route_str) > 9:
							SYSTEM_OUT('ip ro del '+route_str)
				for n in __NET_LIST__():
					if n not in Nic_Array:
						if __deviant__(n, 'bond') == name:
							config.set(n, 'bond',  '')
							SYSTEM_OUT('echo -'+n+' > /sys/class/net/'+name+'/bonding/slaves;')
							os.system('ifup '+n+' > /dev/null')
				
				__Conf_Save__()
				Export(True, '开启成功！')
			else:
				Export(False, '至少需要选择2个网络接口')
		else:
			if __deviant__(name, 'mode')  != 'no':
				config.set(name, 'mode', 'no')
				Nic = __deviant__(name, 'iflist')
				for e in Nic.split(','):
					if len(e) > 0:
						SYSTEM_OUT('echo -'+e+' > /sys/class/net/'+name+'/bonding/slaves')
						config.set(e, 'bond', '')
				if int(SYSTEM_OUT('ifconfig|grep "^'+name+'"|wc -l')) > 0:
					os.system('ifconfig '+name+' down > /dev/null')
					os.system('ip rule del table ' +name)
				for e in Nic.split(','):
					if len(e) > 0:
						os.system('ifup '+e+' > /dev/null')
						os.system('advanceroute '+e)
				SYSTEM_OUT('echo -'+name+' > /sys/class/net/bonding_masters')
				config.set(name, 'iflist', '')
				__Conf_Save__()
			Export(True, '卸载成功！')
	else:
		Export(False, '接口名称不存在！')

#~#### DNS设置
def DNS_Set(value):
	if value.val_set != '':
		config.set('dns', 'address',  value.val_set)
		__Conf_Save__()	
		Export(True, '设置成功！')
	else:
		dns_out = {'dns':__deviant__('dns', 'address')}
		print json.dumps(dns_out, encoding="UTF-8", ensure_ascii=False)

#~#### 网络接口状态列表输出字段
class net_info():
	def __init__(self):
		self.Interface_Name = ''
		self.Interface_MAC = ''
		self.Interface_Velocity = ''
		self.Interface_Status = ''

#~#### 网络接口状态列表
def NIC_Status_List():
	list = []
	json_info = {'total':0, 'rows':[]}
	net_list = __NET_LIST__()
	for inc_name in net_list:
		inc_name = inc_name.replace('\n','')
		out = net_info()
		out.Interface_Name = inc_name
		out.Interface_MAC =  SYSTEM_OUT('cat /sys/class/net/%s/address' % inc_name)
		Speed = SYSTEM_OUT('cat /sys/class/net/%s/speed' % inc_name);
		if int(Speed) > 100000:
			out.Interface_Velocity = '0 Mbps'
		else:
			out.Interface_Velocity = Speed+' Mbps'
		out.Interface_Status =  SYSTEM_OUT('cat /sys/class/net/%s/operstate' % inc_name)
		list.append(out.__dict__)
	json_info['total'] = len(net_list)
	json_info['rows'] = list
	print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)

