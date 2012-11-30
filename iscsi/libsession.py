#!/usr/bin/env python
#-*- coding: utf-8 -*-

from libiscsicommon import *
from libtarget import iSCSIGetTargetList

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
		self.iscsi_protocol = {}  # iSCSI_Protocol()
		self.statistics = {}      # SessionStat()

def __sess_get_stat(sess_path):
	# session stat
	_stat = SessionStat()
	_stat.none_cmd_count = int(AttrRead(sess_path, 'none_cmd_count'))
	_stat.unknown_cmd_count = int(AttrRead(sess_path, 'unknown_cmd_count'))
	_stat.bidi_cmd_count = int(AttrRead(sess_path, 'bidi_cmd_count'))
	_stat.bidi_io_count_kb = int(AttrRead(sess_path, 'bidi_io_count_kb'))
	_stat.read_cmd_count = int(AttrRead(sess_path, 'read_cmd_count'))
	_stat.read_io_count_kb = int(AttrRead(sess_path, 'read_io_count_kb'))
	_stat.write_cmd_count = int(AttrRead(sess_path, 'write_cmd_count'))
	_stat.write_io_count_kb = int(AttrRead(sess_path, 'write_io_count_kb'))
	return _stat


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
			_session.sid = AttrRead(_sess_path, 'sid')
			_session.luns = len(os.listdir('%s/luns' % _sess_path)) -1
			_session.target_name = tgt.name
			_session.statistics = __sess_get_stat(_sess_path).__dict__
			_session_list.append(_session)
	return _session_list


def iSCSIDeleteSession(sid):
	for sess in iSCSIGetSessionList():
		if sess.sid == sid:
			cmd = 'echo "1" > %s/sessions/%s/force_close' % (sess.target_name, sess.initiator_name)
			ret,txt = commands.getstatusoutput(cmd)
			if ret == 0:
				return True,'删除iSCSI Session %s 成功!' % sid
			else:
				return False,'删除iSCSI Session %s 失败' % sid
	return False,'删除iSCSI Session失败，Session不存在!'

if __name__ == '__main__':
	for sess in iSCSIGetSessionList():
		print sess.__dict__
