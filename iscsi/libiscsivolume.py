#!/usr/bin/env python2.6
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
from libnas import is_nasvolume

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
	err_msg = '添加用户数据卷 %s 为iSCSI卷 ' % udv_name
	if not blocksize in VOL_BLOCK_SIZE:
		return (False, err_msg + '失败, Block Size: %s 错误' % blocksize)
	if not ro in VOL_BOOL_MAP:
		return (False, err_msg + '失败, Read Only: %s 错误' % ro)

	udv_dev = get_dev_byudvname(udv_name)
	if '' == udv_dev:
		return (False, err_msg + '失败, 用户数据卷 %s 不存在' % udv_name)

	if get_iscsivolname_bydev(udv_dev) != '':
		return (False, err_msg + '失败, 用户数据卷已经映射为iSCSI卷')
	
	if is_nasvolume(udv_name):
		return (False, err_msg + '失败, 用户数据卷已经映射为NAS卷')

	# vol_name = 'vd' + str(uuid.uuid1()).split('-')[0]
	vol_name = udv_name
	iscsi_cmd = 'add_device %s filename=%s;blocksize=%d;read_only=%s;write_through=%s' % (vol_name, udv_dev, blocksize, VOL_BOOL_MAP[ro], __wrth_int(wrth))

	if not fs_attr_write(SCST.VDISK_DIR + '/mgmt', iscsi_cmd):
		return (False, err_msg + '失败, 系统错误')

	if not iSCSIUpdateCFG():
		iscsi_cmd = 'del_device %s' % vol_name
		fs_attr_write(SCST.VDISK_DIR + '/mgmt', iscsi_cmd)
		iSCSIUpdateCFG()
		return (False, err_msg + '失败, 保存配置文件失败')
	
	return (True, err_msg + '%s 成功' % vol_name)

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
	err_msg = '删除iSCSI卷 %s ' % volume_name
	if not isVolumeExist(volume_name):
		return (False, err_msg + '失败, iSCSI卷不存在')

	if isLunExported(volume_name):
		return (False, err_msg + '失败, iSCSI卷正在使用')

	iscsi_cmd = 'del_device %s' % volume_name
	if not fs_attr_write(SCST.VDISK_DIR + '/mgmt', iscsi_cmd):
		return (False, err_msg + '失败, 系统错误')

	if not iSCSIUpdateCFG():
		return (False, err_msg + '失败, 保存配置文件失败')

	return (True, err_msg + '成功')

def getVolumeInfo(volume_name):
	if not isVolumeExist(volume_name):
		return None

	vol_sys_dir = SCST.VDISK_DIR + os.sep + volume_name
	vol = iSCSIVolume()
	vol.volume_name = volume_name
	vol.udv_dev = fs_attr_read(vol_sys_dir + '/filename')
	vol.udv_name = get_udvname_bydev(vol.udv_dev)
	vol.vg_name = get_vgname_bydev(vol.udv_dev)
	val = fs_attr_read(vol_sys_dir + '/size_mb')
	if val != '' and val.isdigit():
		vol.capacity = int(val) * 1024 * 1024
	val = fs_attr_read(vol_sys_dir + '/blocksize')
	if val != '' and val.isdigit():
		vol.blocksize = int(val)
	vol.read_only = VOL_BOOL_RMAP[fs_attr_read(vol_sys_dir + '/read_only')]
	vol.nv_cache = VOL_BOOL_RMAP[fs_attr_read(vol_sys_dir + '/nv_cache')]
	vol.t10_dev_id = fs_attr_read(vol_sys_dir + '/t10_dev_id')
	vol.wr_method = __wrth_str(fs_attr_read(vol_sys_dir + '/write_through'))
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

