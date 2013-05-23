#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, json, sys, fcntl

TMP_RAID_INFO = '/tmp/.raid-info/by-dev'

def list2str(list=[], sep=','):
	return sep.join([str(x) for x in list])

def list_files(path, reg):
    if not path.endswith("/"):
        path += "/"

    r = re.compile(reg)
    names = os.listdir(path)
    f = [path + x for x in names if r.match(x)]
    return f

def json_dump(obj):
	if os.environ.get('SUDO_USER') == 'www-data' or os.environ.get('LOGNAME') == 'www-data':
		print json.dumps(obj, ensure_ascii=False, sort_keys=True)
	else:
		print json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=4)

def debug_status(res):
    if res:
        msg = {"status": res[0], "msg": res[1] }
        print json.dumps(msg, ensure_ascii=False)
	if res[0] is False:
		sys.exit(-1)

def log_insert(module, category, event, content):
	cmd = 'sys-manager log --insert --module %s --category %s --event %s --content "%s"' % (module, category, event, content)
	(module, category, event, content)
	os.popen(cmd)

def fs_attr_read(path):
	value = ''
	try:
		f = open(path)
		value = f.readline()
	except:
		return ''
	else:
		f.close()
	return value.strip()

def fs_attr_write(path, value):
	try:
		f = open(path, 'w')
		f.write(value)
		f.close()
	except IOError,e:
		err_msg = e
		return False
	else:
		return True

def list_child_dir(path):
	list = []
	try:
		for entry in os.listdir(path):
			if os.path.isdir(path + os.sep + entry):
				list.append(entry)
	except:
		pass

	return list

def list_file(path):
	list = []
	try:
		for entry in os.listdir(path):
			if os.path.isfile(path + os.sep + entry):
				list.append(entry)
	except:
		pass

	return list

def basename(dev):
	return os.path.basename(str(dev))

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
