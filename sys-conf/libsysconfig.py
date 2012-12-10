#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import codecs
import ConfigParser
import subprocess
import hashlib
import time
import shutil

#~ from os.path import join, getsize

reload(sys)
sys.setdefaultencoding('utf8')

CONF_PATH="/opt/"
CRONTAB_PATH="/opt/crontab"
TIMEZONE_PATH="/opt/timezone"
LOCALTIME_PATH="/opt/localtime"


CRONTAB_CONF = """SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# m h dom mon dow user	command
17 *	* * *	root    cd / && run-parts --report /etc/cron.hourly
25 6	* * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
47 6	* * 7	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
52 6	1 * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
#

"""

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
sysconfig --switch <reboot|poweroff|check>		##系统重启，关机，验证状态
	   --hosts <system_name>		##修改主机名称
	   --view		##取主机名称
	   --date --output <this|conf>		##输出当前日期时间和星期
	   --date --config [<--ntp <NTPServer> --interval <int> --unit <1|2> | --now <date> | --zone <Zoneinfo>>]		##输出当前日期时间和星期
"""
	sys.exit(-1)


#~#### 系统重启、关机、验证状态主程序
def switch(value):
	if value.switch_set == 'reboot':
		SYSTEM_OUT('reboot')
		Export(True, '系统正在重启中，请等待。。。。')
	elif value.switch_set == 'poweroff':
		SYSTEM_OUT('poweroff')
		Export(True, '关机命令执行成功！')
	elif value.switch_set == 'check':
		Export(True, '系统运行正常！')
	else:
		Export(False, '操作失败，未能识别的操作指令！')

#~#### 更改系统名称主程序
def hosts(value):
	if value.hosts_set != '':
		hostname = CONF_PATH+'hostname'
		sys_hostname = '/etc/hostname'
		n = open(hostname, 'w')
		try:
			n.write(value.hosts_set+'\n')
		finally:
			n.close()
		if os.path.islink(sys_hostname) == False:
			os.remove(sys_hostname)
			os.symlink(hostname, sys_hostname)			
		os.system('hostname '+value.hosts_set)
		Export(True, '主机名修改成功！')
	else:
		Export(False, '修改失败，没有输入主机名！')

#~#### 更改系统名称主程序
def hosts_view():
	open_conf = open(CONF_PATH+'hostname', 'r')
	OUT= ''
	try:
		OUT = open_conf.read()
	finally:
		open_conf.close()
	print OUT.replace('\n','')
		

#~#### 时间配置主程序
def date(value):
	if value.output_state:
		if value.output_set == 'this':
			json_info = {}
			json_info['this'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
			json_info['Week'] = time.strftime('%w',time.localtime(time.time()))
			print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)
		else:
			ntp = ''
			interval = ''
			unit = '1'
			ntpconf = __ntp_check__()
			if ntpconf != '':
				ntparray = ntpconf.split(' ')
				if ntparray[1] == '1':
					unit = '2'
					interval = ntparray[2].split('/')[1]
				else:
					interval = ntparray[1].split('/')[1]
				ntp = ntparray[6]
			json_info = {}
			json_info['zone'] = __timezone__()
			json_info['ntp'] = ntp
			json_info['interval'] = interval
			json_info['unit'] = unit
			print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)
	elif value.config_set:
		if value.ntp_state:
			if value.ntp_set !='' and value.interval_set != '' and value.unit_set != '':
				__del_ntp__()
				if value.unit_set == '1':
					conf = '1 */'+value.interval_set+' * * *	root ntpdate '+value.ntp_set+'\n'
				else:
					conf = '1 1 */'+value.interval_set+' * *	root ntpdate '+value.ntp_set+'\n'
				f = open(CRONTAB_PATH, 'a')
				try:
					f.write(conf)
				finally:
					f.close()
				sys_crontab = "/etc/crontab"
				if os.path.islink(sys_crontab) == False:
					os.remove(sys_crontab)
					os.symlink(CRONTAB_PATH, sys_crontab)			
				SYSTEM_OUT('ntpdate '+value.ntp_set+' &')
				Export(True, '设置成功！')
			else:
				Export(False, '设置失败，输入的参数正确！')
		elif value.zone_state:
			value.zone_set = value.zone_set.replace('_','/')
			zonetime = '/usr/share/zoneinfo/'+value.zone_set
			if value.zone_set != '' and os.path.exists(zonetime):
				sys_localtime="/etc/localtime"
				shutil.copy(zonetime,LOCALTIME_PATH)
				f = open(TIMEZONE_PATH, 'w')
				try:
					f.write(value.zone_set)
				finally:
					f.close()
				if os.path.islink(sys_localtime) == False:
					os.remove(sys_localtime)
					os.symlink(LOCALTIME_PATH, sys_localtime)
				Export(True, '设置成功！')
			else:
				Export(False, '设置失败，没有这个时区！')
		else:
			if value.now_set != '':
				__del_ntp__()
				SYSTEM_OUT('date -s '+value.now_set)
				SYSTEM_OUT('hwclock -w')
				Export(True, '设置成功！')
			else:
				Export(False, '设置失败，时间格式不正确')
	else:
		AUsage()
		
#~ 验证是否启用NTP服务,输出字符串
def __ntp_check__():
	open_conf = open(CRONTAB_PATH, 'r')
	OUT= ''
	try:
		fileList = open_conf.readlines()
		for fileLine in fileList:
			if len(fileLine.split('root ntpdate ')) > 1:
				OUT= fileLine.replace('\n','')
				break
	finally:
		open_conf.close()
	return OUT
	
#~ 删除NTP服务
def __del_ntp__():
	if os.path.exists(CRONTAB_PATH) == False:
		f = open(CRONTAB_PATH, 'w')
		try:
			f.write(CRONTAB_CONF)
		finally:
			f.close()
		
	r = open(CRONTAB_PATH, 'r')
	OUT= ''
	try:
		fileList = r.readlines()
		for fileLine in fileList:
			if len(fileLine.split('root ntpdate ')) == 1 and len(fileLine) > 1:
				OUT+= fileLine
	finally:
		r.close()
	w = open(CRONTAB_PATH, 'w')
	try:
		w.write(OUT)
	finally:
		w.close()
	
#~ 输出时区
def __timezone__():
	open_conf = open(TIMEZONE_PATH, 'r')
	OUT= ''
	try:
		OUT = open_conf.read()
	finally:
		open_conf.close()
	return OUT.replace('\n','').replace('/','-')
	
