#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
#os.chdir(os.path.dirname(__file__))

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

# 检查指定的Volume当前映射的读写方式
# 判断条件
#   1. volume如果是只读，则返回False，表示只能读
#   2. volume映射的lun中如果有一个是读写的，则返回False，表示只读
def isLunMappedRw(volume_name):
	for tgt in iSCSIGetTargetList():
		tgt_luns_dir = SCST.TARGET_DIR + os.sep + tgt.name + '/luns'
		for lun in getDirList(tgt_luns_dir):
			# 检查Volume是否一致
			lun_path = tgt_luns_dir + os.sep + lun
			lun_device = lun_path + '/device'
			if volume_name != os.path.basename(os.readlink(lun_device)):
				continue
			# 如果Volume是只读，则映射的所有卷都是只读
			if AttrRead(lun_device, 'read_only') == '1':
				return False
			# 如果Volume映射的Lun有一个是读写，则返回只读
			if AttrRead(lun_path, 'read_only') == '0':
				return False
	return True

def iSCSILunMap(tgt, volume_name, lun_id = 'auto', ro = 'auto'):
	if not isTargetExist(tgt):
		return (False, '添加LUN映射失败！Target %s 不存在！' % tgt)
	if not isVolumeExist(volume_name):
		return (False, '添加LUN映射失败！iSCSI数据卷 %s 不存在！' % volume_name)
	if lun_id == 'auto':
		lun_id = getFreeLunId(tgt)
		if lun_id == -1:
			return (False, '添加LUN映射失败！LUN映射已经超出最大允许范围！')

	lunRW = isLunMappedRw(volume_name)
	if ro == 'auto':
		if lunRW:
			lunRO = '0'
		else:
			lunRO = '1'
	elif ro == 'enable':
		lunRO = '1'
	elif ro == 'disable':
		if not lunRW:
			return (False, '设置映射LUN读写属性失败，iSCSI数据卷 %s 只能映射为只读属性!' % volume_name)
		lunRO = '1'
	else:
		return (False, '添加LUN映射失败！ReadOnly属性设置不正确！')

	lun_cmd = 'add %s %d read_only=%s' % (volume_name, lun_id, lunRO)
	tgt_luns_dir = SCST.TARGET_DIR + os.sep + tgt + '/luns'
	if AttrWrite(tgt_luns_dir, 'mgmt', lun_cmd):
		return (True, '添加LUN映射成功！')
	return (False, '添加LUN映射失败！')

def __get_vdisk_by_lun(lun_dir):
	volume = ''
	try:
		lun_dev = lun_dir + os.sep + 'device'
		volume = os.path.basename(os.readlink(lun_dev))
	except:
		pass
	return volume

def iSCSILunUnmap(tgt, lun_id):
	if not isTargetExist(tgt):
		return (False, '解除LUN %d 映射失败！Target %s 不存在！' % (lun_id, tgt))
	if not isLunIdExist(tgt, lun_id):
		return (False, '解除LUN %d 映射失败！LUN不存在！' % lun_id)

	lun_cmd = 'del %d' % lun_id
	tgt_luns_dir = SCST.TARGET_DIR + os.sep + tgt + '/luns'
	volume = __get_vdisk_by_lun('%s/%d' % (tgt_luns_dir, lun_id))	# 保留vdisk名称供删除后检查
	if AttrWrite(tgt_luns_dir, 'mgmt', lun_cmd):
		if not isLunExported(volume):
			if iSCSIVolumeRemove(volume):
				return (True, '解除LUN %d 映射成功！' % lun_id)
			else:
				return (False, '解除LUN %d 映射成功！删除VDISK %s失败！' % (lun_id, volume))
		else:
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
		for lun in iSCSILunGetList():
			if lun['udv_name'] == udv_name:
				priv_dict['volume_name'] = lun['volume_name']
				priv_dict['udv_name'] = udv_name
				priv_dict['status'] = True
				if lun['read_only'] == 'disable':
					priv_dict['privilage'] = 'ro'
				else:
					priv_dict['privilage'] = 'rw'
	except:
		pass
	return priv_dict

if __name__ == '__main__':
	#print iSCSILunGetPrivilage('Udv326_1')
	print isLunMappedRw('vd7a9e46f2')
