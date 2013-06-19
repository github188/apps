#!/usr/bin/env python
#-*- coding: utf-8 -*-

from libiscsicomm import *
from libiscsitarget import iSCSIGetTargetList

#TARGET_DIR

class SessionStat():
	def __init__(self):
		self.none_cmd_count = 0
		self.unknown_cmd_count = 0
		self.bidi_cmd_count = 0
		self.bidi_io_count_kb = 0
		self.read_cmd_count = 0
		self.read_io_count_kb = 0
		self.write_cmd_count = 0
		self.write_io_count_kb = 0

class iSCSI_Session():
	def __init__(self):
		self.sid = ''
		self.initiator_name = ''
		self.luns = 0
		self.target_name = ''
		self.ip_addr = ''
		self.iscsi_protocol = {}  # iSCSI_Protocol()
		self.statistics = {}      # SessionStat()

def __sess_get_stat(sess_path):
	# session stat
	_stat = SessionStat()
	
	val = fs_attr_read(sess_path + '/none_cmd_count')
	if val != '' and val.isdigit():
		_stat.none_cmd_count = int(val)
	
	val = fs_attr_read(sess_path + '/unknown_cmd_count')
	if val != '' and val.isdigit():
		_stat.unknown_cmd_count = int(val)
	
	val = fs_attr_read(sess_path + '/bidi_cmd_count')
	if val != '' and val.isdigit():
		_stat.bidi_cmd_count = int(val)
	
	val = fs_attr_read(sess_path + '/bidi_io_count_kb')
	if val != '' and val.isdigit():
		_stat.bidi_io_count_kb = int(val)
	
	val = fs_attr_read(sess_path + '/read_cmd_count')
	if val != '' and val.isdigit():
		_stat.read_cmd_count = int(val)
	
	val = fs_attr_read(sess_path + '/read_io_count_kb')
	if val != '' and val.isdigit():
		_stat.read_io_count_kb = int(val)
	
	val = fs_attr_read(sess_path + '/write_cmd_count')
	if val != '' and val.isdigit():
		_stat.write_cmd_count = int(val)
	
	val = fs_attr_read(sess_path + '/write_io_count_kb')
	if val != '' and val.isdigit():
		_stat.write_io_count_kb = int(val)
	return _stat

def __sess_get_ip(sess_path):
	ip = ''
	for d in os.listdir(sess_path):
		if not os.path.isdir('%s/%s' % (sess_path, d)):
			continue
		if os.path.exists('%s/%s/ip' % (sess_path, d)):
			ip = fs_attr_read('%s/%s/ip' % (sess_path, d))
			break
	return ip

def iSCSIGetSessionList(spec_tgt=None):
	_session_list = []
	for tgt in iSCSIGetTargetList():
		if spec_tgt and tgt.name != spec_tgt:
			continue
		_iscsi_proto = getISCSIProto(tgt.name).__dict__
		for sess in os.listdir('%s/%s/sessions' % (SCST.TARGET_DIR, tgt.name)):
			if os.path.isfile('%s/%s/sessions/%s' % (SCST.TARGET_DIR, tgt, sess)):
				continue
			_session = iSCSI_Session()
			_session.iscsi_protocol = _iscsi_proto
			_session.initiator_name = sess
			_sess_path = '%s/%s/sessions/%s' % (SCST.TARGET_DIR, tgt.name, sess)
			_session.sid = fs_attr_read(_sess_path + '/sid')
			_session.luns = len(os.listdir('%s/luns' % _sess_path)) -1
			_session.target_name = tgt.name
			_session.ip_addr = __sess_get_ip(_sess_path)
			_session.statistics = __sess_get_stat(_sess_path).__dict__
			_session_list.append(_session)
	return _session_list


def iSCSIDeleteSession(sid):
	for sess in iSCSIGetSessionList():
		if sess.sid == sid:
			cmd = 'echo "1" > %s/%s/sessions/%s/force_close' % (SCST.TARGET_DIR, sess.target_name, sess.initiator_name)
			ret,txt = commands.getstatusoutput(cmd)
			if ret == 0:
				return True,'删除iSCSI Session %s 成功' % sid
			else:
				return False,'删除iSCSI Session %s 失败' % sid
	return False,'删除iSCSI Session失败，Session %s 不存在' % sid

if __name__ == '__main__':
	sys.exit(0)
