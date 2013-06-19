#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
#os.chdir(os.path.dirname(__file__))

from libiscsicomm import *
from libiscsitarget import *
from libiscsivolume import *

LUN_ID_MAX = 254

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
	luns = list_child_dir(lun_dir)
	for i in xrange(0, LUN_ID_MAX+1):
		if str(i) not in luns:
			return i
	return -1

# 检查指定的Volume当前映射的读写方式
# 判断条件
#   1. volume如果是只读，则返回False，表示只能读
#   2. volume映射的lun中如果有一个是读写的，则返回False，表示只读
def isLunMappedRw(volume_name):
	for tgt in iSCSIGetTargetList():
		tgt_luns_dir = SCST.TARGET_DIR + os.sep + tgt.name + '/luns'
		for lun in list_child_dir(tgt_luns_dir):
			# 检查Volume是否一致
			lun_path = tgt_luns_dir + os.sep + lun
			lun_device = lun_path + '/device'
			if volume_name != os.path.basename(os.readlink(lun_device)):
				continue
			# 如果Volume是只读，则映射的所有卷都是只读
			if fs_attr_read(lun_device + '/read_only') == '1':
				return False
			# 如果Volume映射的Lun有一个是读写，则返回只读
			if fs_attr_read(lun_path + '/read_only') == '0':
				return False
	return True

def __set_initiator(tgt, initor):
	try:
		grp_dir = '%s/%s/ini_groups' % (SCST.TARGET_DIR, tgt)
		initor_grp = '%s/%s-grp' % (grp_dir, initor)
		if not os.path.exists(initor_grp):
			_cmd = 'create %s-grp' % initor
			if not fs_attr_write(grp_dir + '/mgmt', _cmd):
				return False
		if not os.path.isdir(initor_grp):
			return False
		initor_dir = '%s/initiators' % initor_grp
		if not os.path.isfile('%s/%s' % (initor_dir, initor)):
			_cmd = 'add %s' % initor
			return True if fs_attr_write(initor_dir + '/mgmt', _cmd) else False
	except:
		return False
	return True

def iSCSILunMap(tgt, volume_name, lun_id = 'auto', ro = 'auto', initor = '*'):
	err_msg = '映射iSCSI卷 %s 为LUN' % volume_name
	if not isTargetExist(tgt):
		return (False, err_msg + '失败, Target %s 不存在' % tgt)

	if not isVolumeExist(volume_name):
		return (False, err_msg + '失败, iSCSI卷不存在')

	lun_dir = '%s/%s/luns' % (SCST.TARGET_DIR, tgt)
	if initor != '*':
		if __set_initiator(tgt, initor):
			lun_dir = '%s/%s/ini_groups/%s-grp/luns' % (SCST.TARGET_DIR, tgt, initor)
		else:
			return (False, err_msg + '失败, 增加Initiator配置到Target出错')

	if lun_id == 'auto':
		_lun_id = __getFreeLunId(lun_dir)
		if _lun_id == -1:
			return (False, err_msg + '失败, LUN数量已经达到最大值')
	else:
		_lun_id = int(lun_id)
		if isLunIdExist(tgt, initor, _lun_id):
			return (False, err_msg + '失败, LUN %d(%s) 已存在' % (_lun_id, initor))

	lunRW = isLunMappedRw(volume_name)
	if ro == 'auto':
		if lunRW:
			lunRO = '0'
		else:
			lunRO = '1'
	elif ro == 'enable':
		lunRO = '1'
	elif ro == 'disable':
		lunRO = '0'
	else:
		return (False, err_msg + '失败, ReadOnly属性设置不正确！')

	lun_cmd = 'add %s %d read_only=%s' % (volume_name, _lun_id, lunRO)
	if not fs_attr_write(lun_dir + '/mgmt', lun_cmd):
		return (False, err_msg + '失败, 系统错误')

	if not iSCSIUpdateCFG():
		lun_cmd = 'del %d' % _lun_id
		fs_attr_write(lun_dir + '/mgmt', lun_cmd)
		iSCSIUpdateCFG()
		return (False, err_msg + '失败, 保存配置文件失败')
	
	return (True, err_msg + ' %d(%s) 成功' % (_lun_id, initor))

def iSCSILunModify(tgt, lun_id, cur_initor, new_initor):
	_lun_id = int(lun_id)
	volume_name = None
	read_only = None
	
	err_msg = '修改LUN %d(%s) ' % (_lun_id, cur_initor)
	if not isLunIdExist(tgt, cur_initor, _lun_id):
		return (False, err_msg + '失败, LUN不存在')
	
	if isLunUsed(tgt, lun_id, cur_initor):
		return (False, err_msg + '失败, LUN正在使用')

	if cur_initor == '*':
		lun_dir = '%s/%s/luns/%s' % (SCST.TARGET_DIR, tgt, lun_id)
	else:
		lun_dir = '%s/%s/ini_groups/%s-grp/luns/%s' % (SCST.TARGET_DIR, tgt, cur_initor, lun_id)
	
	volume_name = basename(os.readlink(lun_dir + '/device'))
	if '0' == fs_attr_read(lun_dir + '/read_only'):
		read_only = 'disable'
	else:
		read_only = 'enable'

	# 删除当前Lun映射
	ret, msg = iSCSILunUnmap(tgt, _lun_id, cur_initor, remove_volume = False)
	if not ret:
		return (ret, err_msg + '失败, ' + msg)

	# 增加新映射
	ret, msg = iSCSILunMap(tgt, volume_name, 'auto', read_only, new_initor)
	if not ret:
		return (False, err_msg + '失败.' + msg)
	else:
		return (True, err_msg + '成功.' + msg)

def isLunUsed(tgt, lun_id, initor):
	sess_dir = '%s/%s/sessions' % (SCST.TARGET_DIR, tgt)
	if initor != '*':
		initor_dir = sess_dir + os.sep + initor
		return True if os.path.isdir(initor_dir) else False
	
	for initor in list_child_dir(sess_dir):
		initor_dir = sess_dir + os.sep + initor
		if os.path.islink(initor_dir + '/luns'):
			if os.readlink(initor_dir + '/luns') == '../../luns':
				return True

	return False

def __isInitiatorExists(tgt, initor):
	initor = '%s/%s/ini_groups/%s-grp/initiators/%s' % (SCST.TARGET_DIR, tgt, initor, initor)
	return True if os.path.isfile(initor) else False

def __delInitiatorConf(tgt, initor):
	grp_mgr = '%s/%s/ini_groups' % (SCST.TARGET_DIR, tgt)
	grp_cmd = 'del %s-grp' % initor
	return True if fs_attr_write(grp_mgr + '/mgmt', grp_cmd) else False

def iSCSILunUnmap(tgt, lun_id, initor = '*', remove_volume = False):
	err_msg = '解除LUN %d(%s) 映射' % (lun_id, initor)

	if not isTargetExist(tgt):
		return (False, err_msg + '失败, Target %s 不存在' % tgt)
	if not isLunIdExist(tgt, initor, lun_id):
		return (False, err_msg + '失败, LUN不存在')
	if initor != '*' and not __isInitiatorExists(tgt, initor):
		return (False, err_msg + '失败, Initiator不存在')
	if isLunUsed(tgt, lun_id, initor):
		return (False, err_msg + '失败, LUN正在使用')

	lun_cmd = 'del %d' % lun_id
	if initor != '*':
		luns_dir = '%s/%s/ini_groups/%s-grp/luns' % (SCST.TARGET_DIR, tgt, initor)
	else:
		luns_dir = '%s/%s/luns' % (SCST.TARGET_DIR, tgt)

	# 保留vdisk名称供删除后检查
	volume = basename(os.readlink(luns_dir + os.sep + str(lun_id) + '/device'))

	if not fs_attr_write(luns_dir + '/mgmt', lun_cmd):
		return (False, err_msg + '失败, 系统错误')

	# 检查initiator配置，如果是最后一个lun，删除initiator组配置
	if initor != '*' and list_child_dir(luns_dir) == []:
		__delInitiatorConf(tgt, initor)

	if not isLunExported(volume) and remove_volume:
		vol_info = getVolumeInfo(volume)
		if not iSCSIVolumeRemove(volume):
			iSCSIUpdateCFG()
			return (False, err_msg + '成功, 删除iSCSI卷 %s 失败' % volume)
	
	if not iSCSIUpdateCFG():
		return (False, err_msg + '成功, 更新配置文件失败')

	return (True, err_msg + '成功')

def iSCSILunGetList(tgt = ''):
	tgt_lun_list = []
	try:
		for t in iSCSIGetTargetList(tgt):
			# get target luns
			tgt_luns_dir = SCST.TARGET_DIR + os.sep + t.name + '/luns'
			for l in list_child_dir(tgt_luns_dir):
				volume_path = tgt_luns_dir + os.sep + l + '/device'
				volume_name = os.path.basename(os.readlink(volume_path))
				vol = getVolumeInfo(volume_name)
				lun = vol.__dict__
				lun['lun_id'] = int(l)
				lun['target_name'] = t.name
				lun['initiator'] = '*'
				if vol.read_only == 'enable':
					lun['read_only'] = vol.read_only
					lun['wr_method'] = 'N/A'
				else:
					if fs_attr_read(tgt_luns_dir + os.sep + l + '/read_only') == '0':
						lun['read_only'] = 'disable'
					else:
						lun['read_only'] = 'enable'
						lun['wr_method'] = 'N/A'

				tgt_lun_list.append(lun)

			# get initiator luns
			ini_grp_dir = '%s/%s/ini_groups' % (SCST.TARGET_DIR, t.name)
			for l in list_child_dir(ini_grp_dir):
				luns_dir = '%s/%s/luns' % (ini_grp_dir, l)
				for k in list_child_dir(luns_dir):
					volume_path = '%s/%s/device' % (luns_dir, k)
					volume_name = os.path.basename(os.readlink(volume_path))
					vol = getVolumeInfo(volume_name)
					lun = vol.__dict__
					lun['lun_id'] = int(k)
					lun['target_name'] = t.name
					lun['initiator'] = l.split('-grp')[0]
					if vol.read_only == 'enable':
						lun['read_only'] = vol.read_only
					else:
						if fs_attr_read('%s/%s' % (luns_dir, k) + '/read_only') == '0':
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
					break
				else:
					priv_dict['privilage'] = 'rw'
	except:
		pass
	return priv_dict

if __name__ == '__main__':
	sys.exit(0)
