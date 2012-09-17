#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
os.chdir(os.path.dirname(__file__))

from libiscsicommon import *
from libtarget import *
from libvolume import *

LUN_MIN_ID = 0
LUN_MAX_ID = 254

"""
class iSCSILun:
	def __init__(self):
		self.lun_id = 0
		self.udv_name = ''
		self.udv_dev = ''
		self.capacity = 0
		self.blocksize = 512
		self.read_only = 'disable'
		self.nv_cache = 'enable'
		self.t10_dev_id = ''
"""

class iSCSITargetLun:
	def __init__(self):
		self.target = ''
		self.luns = 0
		self.lun_list = []

def isLunIdExist(tgt, lun_id):
	if not isTargetExist(tgt):
		return False
	return os.path.isdir(SCST.TARGET_DIR + os.sep + tgt + '/luns/' + '%d' % lun_id)

def getFreeLunId(tgt):
	if not isTargetExist(tgt):
		return -1
	tgt_luns_dir = SCST.TARGET_DIR + os.sep + tgt + '/luns'
	luns = getDirList(tgt_luns_dir)
	if not len(luns) or not '0' in luns:
		return 0
	idx = 0
	luns_len = len(luns) - 1
	while idx < luns_len:
		if int(luns[idx]) + 1 < int(luns[idx+1]):
			return int(luns[idx]) + 1
		idx = idx + 1
	max_id = int(luns[idx]) + 1
	if max_id >= LUN_MAX_ID:
		return -1
	return max_id

def isLunMappedRw(volume_name):
	for tgt in iSCSIGetTargetList():
		tgt_luns_dir = SCST.TARGET_DIR + os.sep + tgt.name + '/luns'
		for lun in getDirList(tgt_luns_dir):
			lun_path = tgt_luns_dir + os.sep + lun
			if AttrRead(lun_path, 'read_only') == '1':
				return True
			lun_device = lun_path + '/device'
			if AttrRead(lun_device, 'read_only') == '1':
				return True
	return False

def iSCSILunMap(tgt, volume_name, lun_id = 'auto', ro = 'auto'):
	if not isTargetExist(tgt):
		return (False, '添加LUN映射失败！Target %s 不存在！' % tgt)
	if not isVolumeExist(volume_name):
		return (False, '添加LUN映射失败！iSCSI数据卷 %s 不存在！' % volume_name)
	if lun_id == 'auto':
		lun_id = getFreeLunId(tgt)
		if lun_id == -1:
			return (False, '添加LUN映射失败！LUN映射已经超出最大允许范围！')

	isRo = isLunMappedRw(volume_name)
	if isRo:
		ro = '1'
	elif ro == 'auto':
		if isRo:
			ro = '1'
		else:
			ro = '0'
	elif ro == 'enable':
		ro = '1'
	elif ro == 'disable':
		ro = '0'
	else:
		return (False, '添加LUN映射失败！ReadOnly属性设置不正确！')

	lun_cmd = 'add %s %d read_only=%s' % (volume_name, lun_id, ro)
	tgt_luns_dir = SCST.TARGET_DIR + os.sep + tgt + '/luns'
	if AttrWrite(tgt_luns_dir, 'mgmt', lun_cmd):
		return (True, '添加LUN映射成功！')
	return (False, '添加LUN映射失败！')

def iSCSILunUnmap(tgt, lun_id):
	if not isTargetExist(tgt):
		return (False, '解除LUN %d 映射失败！Target %s 不存在！' % (lun_id, tgt))
	if not isLunIdExist(tgt, lun_id):
		return (False, '解除LUN %d 映射失败！LUN不存在！' % lun_id)
	lun_cmd = 'del %d' % lun_id
	tgt_luns_dir = SCST.TARGET_DIR + os.sep + tgt + '/luns'
	if AttrWrite(tgt_luns_dir, 'mgmt', lun_cmd):
		return (True, '解除LUN %d 映射成功！' % lun_id)
	return (False, '解除LUN %d 映射失败！' % lun_id)

def iSCSILunGetList(tgt = ''):
	tgt_lun_list = []
	try:
		for t in iSCSIGetTargetList(tgt):
			#tgt_lun = iSCSITargetLun()
			#tgt_lun.target = t.name
			tgt_luns_dir = SCST.TARGET_DIR + os.sep + t.name + '/luns'
			#tgt_lun.luns = len(lun_list)

			for l in getDirList(tgt_luns_dir):
				volume_path = tgt_luns_dir + os.sep + l + '/device'
				volume_name = os.path.basename(os.readlink(volume_path))
				vol = getVolumeInfo(volume_name)
				lun = vol.__dict__
				lun['lun_id'] = int(l)
				lun['target_name'] = t.name
				if vol.read_only == 'enable':
					lun['read_only'] = vol.read_only
				else:
					if AttrRead(tgt_luns_dir + os.sep + l, 'read_only') == '0':
						lun['read_only'] = 'disable'
					else:
						lun['read_only'] = 'enable'
				#tgt_lun.lun_list.append(lun)
				tgt_lun_list.append(lun)

			#tgt_lun.luns = len(tgt_lun.lun_list)
			#tgt_lun_list.append(tgt_lun)
	except IOError, e:
		msg = e
	finally:
		return tgt_lun_list

# 需要搜索所有Target的LUN映射关系，有一个映射为读写属性则返回只读
def iSCSILunGetPrivilage(udv_name):
	priv_dict = {}
	try:
		for tgt_lun in iSCSILunGetList():
			for lun in tgt_lun.lun_list:
				if lun['udv_name'] == udv_name:
					priv_dict['volume_name'] = lun['volume_name']
					priv_dict['udv_name'] = udv_name
					if lun['read_only'] == 'disable':
						priv_dict['privilage'] = 'ro'
					else:
						priv_dict['privilage'] = 'rw'
	except:
		pass
	finally:
		return priv_dict

if __name__ == '__main__':
	for xx in iSCSILunGetList():
		#print xx.__dict__
		for yy in xx.lun_list:
			print yy
	print iSCSILunGetPrivilage('udv1')
