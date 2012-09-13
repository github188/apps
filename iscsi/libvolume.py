#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import pickle
import json
import os
os.chdir(os.path.dirname(__file__))

from libiscsicommon import *

# 参数约束条件
VOL_BLOCK_SIZE = [512, 1024, 2048, 4096]
VOL_BOOL_MAP = {'enable':'1', 'disable':'0'}
VOL_BOOL_RMAP = {'1':'enable', '0':'disable'}

class iSCSIVolume:
	def __init__(self):
		self.volume_name = ''
		self.udv_name = ''
		self.udv_dev = ''
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

def isDevNodeUsed(udv_dev):
	for xx in iSCSIVolumeGetList():
		if xx.udv_dev == udv_dev:
			return True
	return False

def iSCSIVolumeAdd(udv_name, blocksize = 512, ro = 'disable', nv_cache = 'enable'):
	if not blocksize in VOL_BLOCK_SIZE:
		return (False, '映射iSCSI数据卷失败！Block Size参数不正确！')
	if not ro in VOL_BOOL_MAP:
		return (False, '映射iSCSI数据卷失败！Read Only参数不正确！')
	if not nv_cache in VOL_BOOL_MAP:
		return (False, '映射iSCSI数据卷失败！NV CACHE参数不正确！')
	udv_dev = getUdvDevByName(udv_name)
	if isDevNodeUsed(udv_dev):
		return (False, '映射iSCSI数据卷失败！用户数据卷 %s 已经被使用！' % udv_name)

	vol_name = 'vd_' + time.strftime('%Y%m%d%H%M',time.localtime(time.time()))
	iscsi_cmd = 'add_device %s filename=%s;blocksize=%d;nv_cache=%s;read_only=%s' % (vol_name, udv_dev, blocksize, VOL_BOOL_MAP[nv_cache], VOL_BOOL_MAP[ro])

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
	vol.udv_dev = AttrRead(vol_full_path, 'filename')
	vol.udv_name = getUdvNameByDev(vol.udv_dev)
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

def getVolumeByUdv(udv_name):
	try:
		for vol in iSCSIVolumeGetList():
			if vol.udv_name == udv_name:
				return vol.volume_name
	except:
		pass
	return None

if __name__ == '__main__':
	(ret, msg) = iSCSIVolumeAdd('udv1')
	print 'add udv1 ret: ', ret
	print 'msg: ', msg
	for xx in iSCSIVolumeGetList():
		print '-------------------------------'
		print 'volume_name: ', xx.volume_name
		print 'udv_dev: ', xx.udv_dev
		print 'udv_name: ', xx.udv_name
		print 'capacity: ', xx.capacity
		print 'blocksize: ', xx.blocksize
		print 'read_only: ', xx.read_only
		print 'nv_cache: ', xx.nv_cache
		print 't10_dev_id: ', xx.t10_dev_id
		ss = pickle.dumps(xx)
		print json.dumps(ss, indent = 4)
		#(ret, msg) = iSCSIVolumeRemove(xx.volume_name)
		#print 'ret = ', ret
		#print 'msg = ', msg