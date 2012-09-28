#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


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
	return

# 删除指定配置项
def nas_conf_delete(mnt):
	return

# 检查配置项是否存在
def nas_conf_is_exist(mnt):
	return

# 获取配置项列表
def nas_conf_get_list():
	return

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
