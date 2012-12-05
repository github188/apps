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

def isLunIdExist(tgt, initor, lun_id):
	if not isTargetExist(tgt):
		return False
	if initor == '*':
		_check_path = '%s/%s/luns/%d' % (SCST.TARGET_DIR, tgt, lun_id)
	else:
		_check_path = '%s/%s/ini_groups/%s-grp/luns/%d' % (SCST.TARGET_DIR, tgt, initor, lun_id)
	return os.path.isdir(_check_path)

def __getFreeLunId(lun_dir):
	luns = getDirList(lun_dir)
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

def __set_initiator(tgt, initor):
	try:
		grp_dir = '%s/%s/ini_groups' % (SCST.TARGET_DIR, tgt)
		initor_grp = '%s/%s-grp' % (grp_dir, initor)
		if not os.path.exists(initor_grp):
			_cmd = 'create %s-grp' % initor
			if not AttrWrite(grp_dir, 'mgmt', _cmd):
				return False
		if not os.path.isdir(initor_grp):
			return False
		initor_dir = '%s/initiators' % initor_grp
		if not os.path.isfile('%s/%s' % (initor_dir, initor)):
			_cmd = 'add %s' % initor
			return True if AttrWrite(initor_dir, 'mgmt', _cmd) else False
	except:
		return False
	return True

def iSCSILunMap(tgt, volume_name, lun_id = 'auto', ro = 'auto', initor = '*'):

	if not isTargetExist(tgt):
		return (False, '添加LUN映射失败！Target %s 不存在！' % tgt)

	if not isVolumeExist(volume_name):
		return (False, '添加LUN映射失败！iSCSI数据卷 %s 不存在！' % volume_name)

	lun_dir = '%s/%s/luns' % (SCST.TARGET_DIR, tgt)
	if initor != '*':
		if __set_initiator(tgt, initor):
			lun_dir = '%s/%s/ini_groups/%s-grp/luns' % (SCST.TARGET_DIR, tgt, initor)
		else:
			return False, '增加Initiator配置到Target出错!'

	if lun_id == 'auto':
		lun_id = __getFreeLunId(lun_dir)
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
		"""
		if not lunRW:
			return (False, '设置映射LUN读写属性失败，iSCSI数据卷 %s 只能映射为只读属性!' % volume_name)
		"""
		lunRO = '0'
	else:
		return (False, '添加LUN映射失败！ReadOnly属性设置不正确！')

	lun_cmd = 'add %s %d read_only=%s' % (volume_name, lun_id, lunRO)
	if AttrWrite(lun_dir, 'mgmt', lun_cmd):
		return (True, '添加LUN映射成功！')
	return (False, '添加LUN映射失败！')

def iSCSILunModify(tgt, lun_id, cur_initor, fre_initor):

	_lun_id = int(lun_id)
	_volume_name = None
	_read_only = None

	# 获取当前LUN的读写属性以及volume_name
	for x in iSCSILunGetList(tgt):
		if x['initiator']==cur_initor and x['lun_id']==_lun_id:
			_volume_name = x['volume_name']
			_read_only = x['read_only']
	if (_volume_name==None) or (_read_only==None):
		return False, '修改LUN映射失败! LUN_ID %d 不存在!' % _lun_id

	if not isLunIdExist(tgt, cur_initor, _lun_id):
		return (False, '解除LUN %d 映射失败！LUN不存在！' % _lun_id)

	# 删除当前Lun映射
	ret, msg = iSCSILunUnmap(tgt, _lun_id, cur_initor, remove_volume = False)
	if not ret:
		return ret,msg

	# 增加新映射
	return iSCSILunMap(tgt, _volume_name, 'auto', _read_only, fre_initor)

def __get_vdisk_by_lun(lun_dir):
	volume = ''
	try:
		lun_dev = lun_dir + os.sep + 'device'
		volume = os.path.basename(os.readlink(lun_dev))
	except:
		pass
	return volume

def __isInitiatorExists(tgt, initor):
	initor = '%s/%s/ini_groups/%s-grp/initiators/%s' % (SCST.TARGET_DIR, tgt, initor, initor)
	return True if os.path.isfile(initor) else False

def __delInitiatorConf(tgt, initor):
	grp_mgr = '%s/%s/ini_groups' % (SCST.TARGET_DIR, tgt)
	grp_cmd = 'del %s-grp' % initor
	return True if AttrWrite(grp_mgr, 'mgmt', grp_cmd) else False

def iSCSILunUnmap(tgt, lun_id, initor = '*', remove_volume = True):
	if not isTargetExist(tgt):
		return (False, '解除LUN %d 映射失败！Target %s 不存在！' % (lun_id, tgt))
	if not isLunIdExist(tgt, initor, lun_id):
		return (False, '解除LUN %d 映射失败！LUN不存在！' % lun_id)
	if initor != '*' and not __isInitiatorExists(tgt, initor):
		return Flase, '解除 %s 映射失败！Initiator不存在！' % lun_id

	lun_cmd = 'del %d' % lun_id
	if initor != '*':
		luns_dir = '%s/%s/ini_groups/%s-grp/luns' % (SCST.TARGET_DIR, tgt, initor)
	else:
		luns_dir = '%s/%s/luns' % (SCST.TARGET_DIR, tgt)

	volume = __get_vdisk_by_lun('%s/%d' % (luns_dir, lun_id))	# 保留vdisk名称供删除后检查

	if AttrWrite(luns_dir, 'mgmt', lun_cmd):
		# 检查initiator配置，如果是最后一个lun，删除initiator组配置
		if initor != '*' and getDirList(luns_dir) == []:
			if not __delInitiatorConf(tgt, initor):
				return False, '解除LUN %d 映射失败!无法删除Initiator %s 配置!' % (lun_id, initor)
		if not isLunExported(volume) and remove_volume:
			vol_info = getVolumeInfo(volume)
			if iSCSIVolumeRemove(volume):
				if iscsiExtRemoveUdv(vol_info.udv_name):
					return (True, '解除LUN %d 映射成功！' % lun_id)
				else:
					return (False, '解除LUN %d映射成功！删除VDISK %s 成功！删除用户数据卷 % 失败！' % (lun_id, volume, vol_info.udv_name))
			else:
				return (False, '解除LUN %d 映射成功！删除VDISK %s失败！' % (lun_id, volume))
		else:
			return (True, '解除LUN %d 映射成功！' % lun_id)
	return (False, '解除LUN %d 映射失败！' % lun_id)

def iSCSILunGetList(tgt = ''):
	tgt_lun_list = []
	try:
		for t in iSCSIGetTargetList(tgt):

			# get target luns
			tgt_luns_dir = SCST.TARGET_DIR + os.sep + t.name + '/luns'
			for l in getDirList(tgt_luns_dir):
				volume_path = tgt_luns_dir + os.sep + l + '/device'
				volume_name = os.path.basename(os.readlink(volume_path))
				vol = getVolumeInfo(volume_name)
				lun = vol.__dict__
				lun['lun_id'] = int(l)
				lun['target_name'] = t.name
				lun['initiator'] = '*'
				if vol.read_only == 'enable':
					lun['read_only'] = vol.read_only
				else:
					if AttrRead(tgt_luns_dir + os.sep + l, 'read_only') == '0':
						lun['read_only'] = 'disable'
					else:
						lun['read_only'] = 'enable'
				#tgt_lun.lun_list.append(lun)
				tgt_lun_list.append(lun)

			# get initiator luns
			ini_grp_dir = '%s/%s/ini_groups' % (SCST.TARGET_DIR, t.name)
			for l in getDirList(ini_grp_dir):
				luns_dir = '%s/%s/luns' % (ini_grp_dir, l)
				for k in getDirList(luns_dir):
					volume_path = '%s/%s/device' % (luns_dir, k)
					volume_name = os.path.basename(os.readlink(volume_path))
					vol = getVolumeInfo(volume_name)
					lun = vol.__dict__
					lun['lun_id'] = int(k)
					lun['target_name'] = t.name
					lun['initiator'] = l.split('-')[0]
					if vol.read_only == 'enable':
						lun['read_only'] = vol.read_only
					else:
						if AttrRead('%s/%s' % (luns_dir, k), 'read_only') == '0':
							lun['read_only'] == 'disable'
						else:
							lun['read_only'] = 'enable'
					tgt_lun_list.append(lun)

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
	#print isLunMappedRw('vd7a9e46f2')
	#print __set_initiator('iqn.2006-10.net.vlnb:tgt', 'abc')
	#print __isInitiatorExists('iqn.2006-10.net.vlnb:tgt', 'abc')
	print __delInitiatorConf('iqn.2006-10.net.vlnb:tgt', 'abc')
