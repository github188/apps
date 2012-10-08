#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

NAS_CONF_FILE = '/etc/rc.local'
NAS_CONF_START_SEP = '# *** JW-NAS-CONF-START ***'
NAS_CONF_END_SEP = '# *** JW-NAS-CONF-END ***'
NAS_CONF_TMP = '/tmp/.nas_tmp_conf'

"""
NAS卷属性
"""
class NasVolumeAttr:
	def __init__(self):
		self.path = ''		# 被挂载的路径 eg. /mnt/Share/udv1
		self.volume_name = ''	# 卷名称，实际为udv名称
		self.state = ''		# NAS卷状态: formatting,mounted,formatted
		self.fmt_percent = 0	# 格式化进度，取值 0 ~ 100
		self.capacity = 0	# 容量，单位：字节
		self.occupancy = 0	# 已经使用容量，单位：字节
		self.remain = 0		# 剩余容量，单位：字节
		self.fs_type = ''	# 文件系统类型

"""
配置文件操作函数
"""
#  增加配置项
def nas_conf_add(dev, mnt):
	if nas_conf_is_exist(mnt):
		return False, '记录已经存在!'

	try:
		old_f = open(NAS_CONF_FILE, 'r')
		#new_file_name = os.tempnam()
		new_file_name = NAS_CONF_TMP
		new_f = open(new_file_name, 'w')
		for line in old_f.readlines():
			if line.find(NAS_CONF_END_SEP) >= 0:
				new_f.write('mount %s %s\n' % (dev, mnt))
			new_f.write(line)
		old_f.close()
		new_f.close()
		os.rename(new_file_name, NAS_CONF_FILE)
	except RuntimeWarning, e:  # 消除os.tmpnam()带来的运行时安全警告
		pass
	except:
		return False, '增加记录失败!'
	return True, '增加记录成功!'

# 删除指定配置项
def nas_conf_remove(mnt):
	if not nas_conf_is_exist(mnt):
		return False,'记录不存在!'
	try:
		old_f = open(NAS_CONF_FILE, 'r')
		#new_file_name = os.tempnam()
		new_file_name = NAS_CONF_TMP
		new_f = open(new_file_name, 'w')
		for line in old_f.readlines():
			if line.find(mnt) >= 0:
				continue
			new_f.write(line)
		old_f.close()
		new_f.close()
		os.rename(new_file_name, NAS_CONF_FILE)
	except RuntimeWarning, e:  # 消除os.tmpnam()带来的运行时安全警告
		pass
	except:
		return False,'删除配置文件记录失败!'
	return True, '删除配置文件记录成功!'

# 检查配置项是否存在
def nas_conf_is_exist(mnt):
	exist = False
	try:
		f = open(NAS_CONF_FILE)
		for line in f.readlines():
			if line.find(mnt) >= 0:
				exist = True
		f.close()
	except:
		return False
	return exist

# 获取配置项列表
def nas_conf_get_list():
	nas_conf_list = []
	conf_start = False
	conf_end = False
	try:
		f = open(NAS_CONF_FILE)
		for line in f.readlines():
			if line.find(NAS_CONF_START_SEP) >= 0:
				conf_start = True
			if line.find(NAS_CONF_END_SEP) >= 0:
				conf_end = True

			# load conf line:
			# (FORMAT): mount /dev/md1p1 /mnt/Share/udv1
			if con_start and not conf_end:
				nas_conf = NasVolumeAttr()
				nas_conf.path = line.split()[-1]
				nas_conf.volume_name =
				nas_conf.state = 'mounted'
				nas_conf.fmt_percent = 0
				nas_conf.capacity =
				nas_conf.occupancy =
				fs_type = 'ext3'
				nas_conf_list.append(nas_conf)
	except:
		pass
	return nas_conf_list

"""
格式化相关函数
"""
# 获取格式化列表
def nas_fmt_get_list():
	return

"""
已经加载卷相关函数
"""
# 获取已经加载的卷列表
def nas_mount_get_list():
	return

"""
API
"""
# 获取指定或者所有NAS卷列表
def nasGetList(volume_name):
	return

# 映射NAS卷
def nasMapping(udv):
	return

# 解除NAS卷映射
def nasUnmapping(volume_name):
	return

# 检查是否为NAS卷
def isNasVolume(volume_name):
	return

if __name__ == '__main__':
	nas_conf_add('/dev/md1p2', '/mnt/Share/udv2')
	nas_conf_remove('/mnt/Share/udv2')

	if nas_conf_is_exist('/mnt/Share/udv2'):
		print 'exist'
	else:
		print 'not exist'
	if nas_conf_is_exist('/mnt/Share/udv1'):
		print 'exist'
	else:
		print 'not exist'
