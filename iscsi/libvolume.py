#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from libiscsicommon import *

# 参数约束条件
VOL_BLOCK_SIZE = [512, 1024, 2048, 4096]
VOL_BOOL_MAP = {'enable':'1', 'disable':'0'}
VOL_BOOL_RMAP = {'1':'enable', '0':'disable'}

class iSCSIVolume:
	def __init__(self):
		self.volume_name = ''
		self.udv_name = ''
		self.dev_node = ''
		self.capacity = 0
		self.blocksize = 512
		self.read_only = 'disable'
		self.nv_cache = 'enable'
		self.t10_dev_id = ''

def isVolumeExist(volume_name):
	vol_path = SCST.VDISK_DIR + os.sep + volume_name
	if os.path.isdir(vol_path) and os.path.islink(vol_path):
		return True
	return False

def isDevNodeUsed(dev_node):
	for xx in iSCSIVolumeGetList():
		if xx.dev_node == dev_node:
			return True
	return False

def iSCSIVolumeAdd(dev_node, blocksize = 512, ro = 'disable', nv_cache = 'enable'):
	if not blocksize in VOL_BLOCK_SIZE:
		return (False, '映射iSCSI数据卷失败！Block Size参数不正确！')
	if not ro in VOL_BOOL_MAP:
		return (False, '映射iSCSI数据卷失败！Read Only参数不正确！')
	if not nv_cache in VOL_BOOL_MAP:
		return (False, '映射iSCSI数据卷失败！NV CACHE参数不正确！')
	if isDevNodeUsed(dev_node):
		return (False, '映射iSCSI数据卷失败！块设备 %s 已经被使用！' % dev_node)

	vol_name = 'vd_' + time.strftime('%Y%m%d%H%M',time.localtime(time.time()))
	iscsi_cmd = 'add_device %s filename=%s;blocksize=%d;nv_cache=%s;read_only=%s' % (vol_name, dev_node, blocksize, VOL_BOOL_MAP[nv_cache], VOL_BOOL_MAP[ro])

	if AttrWrite(SCST.VDISK_DIR, 'mgmt', iscsi_cmd):
		return (True, '添加iSCSI数据卷 %s 成功！' % vol_name)
	return (False, '添加iSCSI数据卷 %s 失败！' % vol_name)

def iSCSIVolumeRemove(volume_name):
	if not isVolumeExist(volume_name):
		return (False, 'iSCSI数据卷 %s 不存在！' % volume_name)

	iscsi_cmd = 'del_device %s' % volume_name
	if AttrWrite(SCST.VDISK_DIR, 'mgmt', iscsi_cmd):
		return (True, '删除iSCSI数据卷 %s 成功！' % volume_name)
	return (False, '删除iSCSI数据卷 %s 失败！' % volume_name)

def getVolumeInfo(volume_name):
	if not isVolumeExist(volume_name):
		return None
	vol_full_path = SCST.VDISK_DIR + os.sep + volume_name
	vol = iSCSIVolume()
	vol.volume_name = volume_name
	#vol.udv_name =
	vol.dev_node = AttrRead(vol_full_path, 'filename')
	vol.capacity = int(AttrRead(vol_full_path, 'size_mb'))
	vol.blocksize = int(AttrRead(vol_full_path, 'blocksize'))
	vol.read_only = VOL_BOOL_RMAP[AttrRead(vol_full_path, 'read_only')]
	vol.nv_cache = VOL_BOOL_RMAP[AttrRead(vol_full_path, 'nv_cache')]
	vol.t10_dev_id = AttrRead(vol_full_path, 't10_dev_id')
	return vol

def iSCSIVolumeGetList(volume_name = ''):
	vol_list = []

	if volume_name != '':
		vol_info = getVolumeInfo(volume_name)
		if vol_info:
			vol_list.append(vol_info)
	else:
		for vol in getDirList(SCST.VDISK_DIR):
			vol_info = getVolumeInfo(vol)
			if vol_info:
				vol_list.append(vol_info)
	return vol_list

if __name__ == '__main__':
	(ret, msg) = iSCSIVolumeAdd('/dev/sdf')
	print 'ret = ', ret
	print 'msg = ', msg

	for xx in iSCSIVolumeGetList():
		print dir(xx)
		print 'vol.dev_node = ', xx.dev_node
		#(ret, msg) = iSCSIVolumeRemove(xx.volume_name)
		#print 'ret = ', ret
		#print 'msg = ', msg
