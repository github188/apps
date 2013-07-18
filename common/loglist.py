#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import os.path
import commands
import getopt
import json
import sqlite3
import time
import statvfs
import stat
import shutil
import codecs
import subprocess

from os.path import join, getsize

reload(sys)
sys.setdefaultencoding('utf8')

os.chdir(os.path.dirname(sys.argv[0]))
Out_Log_PATH = "/var/www/log"
Out_Log_FILE = Out_Log_PATH+"/log.txt"
LOG_FILE = "/opt/log/jw-log.db"
LOG_PATH = os.path.dirname(LOG_FILE)
if os.path.exists(LOG_PATH) == False:
	os.mkdir(LOG_PATH) 

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

class IArgs:
	def __init__(self):
		self.list_set = False
		self.out_set = False
		self.del_set = False
		self.id_set = ''
		self.id_state = False
		self.module_set = ''
		self.category_set = ''
		self.event_set = ''
		self.user_set = ''
		self.page_set = 0
		self.coun_set = 10
		self.search_set = ''
		self.timeStart_set = ''
		self.timeEnd_set = ''

def AUsage(err=""):
	if err != "":
		print '##命令参数不正确，错误提示： %s' % err
	else:
		print '##命令参数不正确，请检查要执行的命令模式！'
	print """
	--list [ < --id <log_id> > | < --module <module> --category <category> --event <event> --page <int> --coun <int> --user <user_name>  --search <content> --start <timeStart> --end <timeEnd> >]		##输出查询列表
	--del		##导出日志
	--out		##导出日志
"""
	sys.exit(-1)

long_opt = ['list', 'del', 'out',  'id=', 'user=', 'module=', 'category=', 'event=', 'page=', 'coun=', 'search=', 'start=', 'end=']

def CleanDir( Dir ):
	if os.path.isdir( Dir ):
		paths = os.listdir( Dir )
		for path in paths:
			filePath = os.path.join( Dir, path )
			if os.path.isfile( filePath ):
				try:
					os.remove( filePath )
				except os.error:
					autoRun.exception( "remove %s error." %filePath )
			elif os.path.isdir( filePath ):
				if filePath[-4:].lower() == ".svn".lower():
					continue
			shutil.rmtree(filePath,True)
	return True

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', long_opt)
	except getopt.GetoptError, e:
		AUsage(e)

	iArgs = IArgs()
	for opt,arg in opts:
		if opt == '--list':
			iArgs.list_set = True
		elif opt == '--del':
			iArgs.del_set = True
		elif opt == '--out':
			iArgs.out_set = True
		elif opt == '--id':
			iArgs.id_set = arg
			iArgs.id_state = True
		elif opt == '--module':
			iArgs.module_set = arg
		elif opt == '--category':
			iArgs.category_set = arg
		elif opt == '--event':
			iArgs.event_set = arg
		elif opt == '--user':
			iArgs.user_set = arg
		elif opt == '--search':
			iArgs.search_set = arg
		elif opt == '--page':
			iArgs.page_set = arg
		elif opt == '--coun':
			iArgs.coun_set = arg
		elif opt == '--start':
			iArgs.timeStart_set = arg
		elif opt == '--end':
			iArgs.timeEnd_set = arg

	if iArgs.list_set == True:
		__List__(iArgs)
	elif iArgs.del_set == True:
		__Del__(iArgs)
	elif iArgs.out_set == True:
		__Out__(iArgs)
	else:
		AUsage()

class list_info():
	def __init__(self):
		self.id = 1
		self.date = ''
		self.user = ''
		self.module = ''
		self.category = ''
		self.event = ''
		self.content = ''

def __List__(value):
	cx = sqlite3.connect(LOG_FILE)
	cu = cx.cursor()
	if value.id_state == True:
		id = int(value.id_set)
		sql = 'select * from jwlog where id = %d' % id
		cu.execute(sql) 
		res = cu.fetchall()
		json_info = {}
		json_info['id'] = res[0][0]
		json_info['date'] = res[0][1]
		json_info['user'] = res[0][2]
		json_info['module'] = res[0][3]
		json_info['category'] = res[0][4]
		json_info['event'] = res[0][5]
		json_info['content'] = res[0][6]
	else:
		sqlwhere = ''
		if value.module_set != "":
			sqlwhere += ' and module = "'+value.module_set+'"'
		if value.category_set != "":
			sqlwhere += ' and category = "'+value.category_set+'"'
		if value.event_set != "":
			sqlwhere += ' and event = "'+value.event_set+'"'
		if value.user_set != "":
			sqlwhere += ' and user = "'+value.user_set+'"'
		if value.search_set != "":
			sqlwhere += ' and content LIKE "%'+value.search_set+'%"'
		if value.timeStart_set != "":
			sqlwhere += ' and date >= "'+value.timeStart_set+'"'
		if value.timeEnd_set != "":
			sqlwhere += ' and date < "'+value.timeEnd_set+'"'
		page = int(value.page_set)
		coun = int(value.coun_set)
		Start = 0
		limit = ''
		if page > 0:
			Start = coun * page - coun
			limit = 'limit %s,%s'%(Start,coun)
		cu.execute('select count() from jwlog where 1=1 %s' %(sqlwhere)) 
		count = cu.fetchall()[0][0]
		cu.execute('select * from jwlog where 1=1%s order by date desc,id desc %s' %(sqlwhere,limit)) 
		res = cu.fetchall()
		list = []
		json_info = {'total':0, 'rows':[]}
		for line in res:
			out = list_info()
			out.id = line[0]
			out.date = line[1]
			out.user = line[2]
			out.module = line[3]
			out.category = line[4]
			out.event = line[5]
			out.content = line[6]
			list.append(out.__dict__)
		json_info['total'] = count
		json_info['rows'] = list
	cu.close()
	print json.dumps(json_info, encoding="UTF-8", ensure_ascii=False)

def __Del__(value):
	total = 1000
	cx = sqlite3.connect(LOG_FILE)
	cu = cx.cursor()
	cu.execute('select count() from jwlog') 
	count = cu.fetchall()[0][0]
	if count < total:
		Export(False, "删除失败，日志最少要保留1000条记录，方便故障分析！")
	else:
		cu.execute('delete from jwlog where rowid in (select rowid from jwlog order by date desc,id desc limit %s,%s)' % (total, count-total)) 
		cx.commit() 
		cu.close()
		Export(True, "清除日志成功！")

def __Out__(value):
	cx = sqlite3.connect(LOG_FILE)
	cu = cx.cursor()
	cu.execute('select * from jwlog') 
	res = cu.fetchall()
	if os.path.exists(Out_Log_PATH) == False:
		try:
			os.makedirs(Out_Log_PATH)
		except:
			pass
	else:
		CleanDir( Out_Log_PATH )

	logwrite = open(Out_Log_FILE, 'w')
	try:
		for line in res:
			out = 'id:[%s], date:[%s], user:[%s], module:[%s], category:[%s], event:[%s], content:[%s]\r\n'%(line[0],line[1],line[2],line[3],line[4],line[5],line[6])
			logwrite.write(out)
		logwrite.close()
	except:
		logwrite.close()
	cu.close()
	tardate = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
	tarfile = 'log'+tardate+'.tgz'
	SYSTEM_OUT('cd /var; tar cfz /var/www/log/var.tgz log')
	SYSTEM_OUT('cd /var/www/log; tar cfz '+tarfile+' var.tgz log.txt')
	Export(True, tarfile)

if __name__ == '__main__':
	main()
	
