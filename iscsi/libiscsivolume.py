#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pickle
import json
import os
import uuid

from libcommon import *
from libudv import *
from libiscsicomm import *
from libiscsitarget import iSCSIUpdateCFG

# 参数约束条件
VOL_BLOCK_SIZE = [512, 1024, 2048, 4096]
VOL_BOOL_MAP = {'enable':'1', 'disable':'0'}
VOL_BOOL_RMAP = {'1':'enable', '0':'disable'}

class iSCSIVolume:
	def __init__(self):
		self.volume_name = ''
		self.udv_name = ''
		self.vg_name = ''
		self.udv_dev = ''
		self.capacity = 0
		self.blocksize = 512
		self.read_only = 'disable'
		self.nv_cache = 'disable'
		self.t10_dev_id = ''
		self.wr_method = ''

def isVolumeExist(volume_name):
	vol_path = SCST.VDISK_DIR + os.sep + volume_name
	if os.path.isdir(vol_path) and os.path.islink(vol_path):
		return True
	return False

def __wrth_int(wr):
	return '1' if wr == 'wt' else '0'

def __wrth_str(wr):
	return 'wt' if wr == '1' else 'wb'

def iSCSIVolumeAdd(udv_name, blocksize = 512, ro = 'disable', wrth = 'wb'):
	if not blocksize in VOL_BLOCK_SIZE:
		return (False, '映射iSCSI数据卷失败, Block Size参数不正确')
	if not ro in VOL_BOOL_MAP:
		return (False, '映射iSCSI数据卷失败, Read Only参数不正确')

	udv_dev = get_dev_byudvname(udv_name)
	if '' == udv_dev:
		return (False, '映射iSCSI数据卷失败, 用户数据卷不存在.')

	# todo: add nas check
	if get_iscsivolname_bydev(udv_dev) != '':
		return (False, '映射iSCSI数据卷失败！用户数据卷 %s 已经被使用！' % udv_name)

	vol_name = 'vd' + str(uuid.uuid1()).split('-')[0]
	iscsi_cmd = 'add_device %s filename=%s;blocksize=%d;read_only=%s;write_through=%s' % (vol_name, udv_dev, blocksize, VOL_BOOL_MAP[ro], __wrth_int(wrth))

	if AttrWrite(SCST.VDISK_DIR, 'mgmt', iscsi_cmd):
		ret,msg = iSCSIUpdateCFG()
		if not ret:
			return (True, '添加iSCSI数据卷 %s 成功, 更新配置文件失败 %s' % (vol_name, msg))
		return (True, '添加iSCSI数据卷 %s 成功' % vol_name)
	return (False, '添加iSCSI数据卷 %s 失败' % vol_name)

# 检查Vdisk是否有lun在使用
def isLunExported(volume_name):
	exp_dir = SCST.VDISK_DIR + os.sep + volume_name + os.sep + 'exported'
	exported = False
	try:
		if os.listdir(exp_dir) == []:
			exported = False
		else:
			exported = True
	except:
		exported = False
	return exported

def iSCSIVolumeRemove(volume_name):
	if not isVolumeExist(volume_name):
		return (False, 'iSCSI数据卷 %s 不存在' % volume_name)

	if isLunExported(volume_name):
		return (False, '删除iSCSI数据卷失败, iSCSI数据卷正在被其他LUN使用')

	iscsi_cmd = 'del_device %s' % volume_name
	if AttrWrite(SCST.VDISK_DIR, 'mgmt', iscsi_cmd):
		ret,msg = iSCSIUpdateCFG()
		if not ret:
			return (True, '删除iSCSI数据卷 %s 成功, 更新配置文件失败 %s' % (volume_name, msg))
		return (True, '删除iSCSI数据卷 %s 成功' % volume_name)
	return (False, '删除iSCSI数据卷 %s 失败' % volume_name)

def getVolumeInfo(volume_name):
	if not isVolumeExist(volume_name):
		return None

	vol_full_path = SCST.VDISK_DIR + os.sep + volume_name
	vol = iSCSIVolume()
	vol.volume_name = volume_name
	vol.udv_dev = AttrRead(vol_full_path, 'filename')
	vol.udv_name = get_udvname_bydev(vol.udv_dev)
	vol.vg_name = get_vgname_bydev(vol.udv_dev)
	vol.capacity = int(AttrRead(vol_full_path, 'size_mb')) * 1024 * 1024
	vol.blocksize = int(AttrRead(vol_full_path, 'blocksize'))
	vol.read_only = VOL_BOOL_RMAP[AttrRead(vol_full_path, 'read_only')]
	vol.nv_cache = VOL_BOOL_RMAP[AttrRead(vol_full_path, 'nv_cache')]
	vol.t10_dev_id = AttrRead(vol_full_path, 't10_dev_id')
	vol.wr_method = __wrth_str(AttrRead(vol_full_path, 'write_through'))
	return vol

def iSCSIVolumeGetList(volume_name = '', udv_name = ''):
	vol_list = []

	if volume_name != '':
		vol_info = getVolumeInfo(volume_name)
		if vol_info:
			vol_list.append(vol_info)
	elif udv_name != '':
		udv_dev = get_dev_byudvname(udv_name)
		if udv_dev != '':
			volume_name = get_iscsivolname_bydev(udv_dev)
			vol_info = getVolumeInfo(volume_name)
			if vol_info:
				vol_list.append(vol_info)
	else:
		for vol in list_child_dir(SCST.VDISK_DIR):
			vol_info = getVolumeInfo(vol)
			if vol_info:
				vol_list.append(vol_info)

	return vol_list

if __name__ == '__main__':
	sys.exit(0)

