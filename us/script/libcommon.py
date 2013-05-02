#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, json, sys, fcntl

TMP_RAID_INFO = '/tmp/.raid-info/by-dev'

def list_files(path, reg):
    if not path.endswith("/"):
        path += "/"

    r = re.compile(reg)
    names = os.listdir(path)
    f = [path + x for x in names if r.match(x)]
    return f

def json_dump(obj):
    print json.dumps(obj, ensure_ascii=False, sort_keys=True, indent = 4)

def debug_status(res):
    if res:
        msg = {"status": res[0], "msg": res[1] }
        print json.dumps(msg, ensure_ascii=False)
	if res[0] is False:
		sys.exit(-1)

def LogInsert(module, category, event, content):
	cmd = 'sys-manager log --insert --module %s --category %s --event %s --content "%s"' % (module, category, event, content)
	(module, category, event, content)
	os.popen(cmd)

# 公用函数
def AttrRead(dir_path, attr_name):
	value = ''
	full_path = dir_path + os.sep + attr_name
	try:
		f = open(full_path)
		value = f.readline()
	except:
		return ''
	else:
		f.close()
	return value.strip()

def AttrWrite(dir_path, attr_name, value):
	full_path = dir_path + os.sep + attr_name
	try:
		f = open(full_path, 'w')
		f.write(value)
		f.close()
	except IOError,e:
		err_msg = e
		return False
	else:
		return True

def getDirList(file_path):
	dir_list = []
	try:
		for td in os.listdir(file_path):
			if os.path.isdir(file_path + os.sep + td):
				dir_list.append(td)
	except IOError,e:
		err_msg = e
	finally:
		return dir_list

def basename(dev):
	return os.path.basename(dev)

def initlog():
	import logging
	
	logger = logging.getLogger()

	logfile = '/var/log/jw-log'
	hdlr = logging.FileHandler('/var/log/jw-log')

	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)

	logger.addHandler(hdlr)
	logger.setLevel(logging.INFO)
	return logger

RAID_REBUILD_LOCK = '/tmp/.raid_rebuild_lock'
def lock_file(filepath):
	try:
		f = open(filepath, 'w')
	except:
		return None
	
	fcntl.flock(f, fcntl.LOCK_EX)
	return f
	
def unlock_file(f):
	if f == None:
		return
	fcntl.flock(f, fcntl.LOCK_UN)  
	f.close() 

if __name__ == '__main__':
	log = initlog()
	log.info('测试')
