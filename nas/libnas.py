#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import statvfs
import json
import commands
import stat

reload(sys)
sys.setdefaultencoding('utf8')

NAS_CONF_FILE = '/etc/rc.local'
NAS_CONF_START_SEP = '# *** JW-NAS-CONF-START ***'
NAS_CONF_END_SEP = '# *** JW-NAS-CONF-END ***'
NAS_CONF_TMP = '/etc/.nas_tmp_conf'
TMP_DIR = '/tmp/.nas_info'

#-------------- 辅助函数 ---------------
def nas_tmpfs_set_value(key, value):
	nas_tmpfs_mkdir()
	mkfs_tmp_dir = nas_tmpfs_get_dir()
	try:
		file_name = '%s/%s' % (mkfs_tmp_dir, key)
		f = open(file_name, 'w')
		f.write(value)
		f.close()
	except IOError, e:
		print 'IO Error while write file', e
		sys.exit(-1)
	except:
		pass
	return

def nas_tmpfs_get_value(key):
	content = ''
	try:
		f = open(key)
		content = f.readline().strip()
		f.close()
	except IOError, e:
		print 'IOError ', e
		sys.exit(-1)
	except:
		pass
	return content

def nas_tmpfs_get_dir():
	global TMP_DIR
	if not os.path.exists(TMP_DIR):
		os.mkdir(TMP_DIR)
	return '%s/%d' % (TMP_DIR, os.getpid())

def nas_tmpfs_mkdir():
	mkfs_tmp_dir = nas_tmpfs_get_dir()
	if not os.path.exists(mkfs_tmp_dir):
		os.mkdir(mkfs_tmp_dir)
	return


#------------------------------------------------------------------------------
#  实用函数
#------------------------------------------------------------------------------

# 通过UDV名称获取设备名称
def __get_udv_dev_by_name(udv):
	udv_dev = ''
	try:
		json_result = os.popen('sys-manager udv --get-dev-byname %s' % udv)
		udv_result = json.loads(json_result.readline())
		if udv_result['status']:
			udv_dev = udv_result['udv_dev']
	except:
		pass
	return udv_dev

# 通过UDV设备名称获取名称
def __get_udv_name_by_dev(dev):
	udv_name = ''
	try:
		json_result = commands.getoutput('sys-manager udv --get-name-bydev %s' % dev)
		udv_result = json.loads(json_result)
		if udv_result['status']:
			udv_name = udv_result['udv_name']
	except:
		pass
	return udv_name

# 获取nas卷容量
def __get_nas_volume_capacity(nas_volume):
	capacity = 0
	try:
		vfs = os.statvfs(nas_volume)
		capacity = vfs.f_blocks * vfs.f_bsize
	except:
		pass
	return capacity

# 获取nas卷已经剩余空间
def __get_nas_volume_remain(nas_volume):
	remain = 0
	try:
		vfs = os.statvfs(nas_volume)
		remain = vfs.f_bavail * vfs.f_bsize
	except:
		pass
	return remain

# 获取nas卷已经使用空间
def __get_nas_volume_occupancy(nas_volume):
	return __get_nas_volume_capacity(nas_volume) - __get_nas_volume_remain(nas_volume)

# 获取nas卷的文件系统类型
def __get_nas_volume_fstype(nas_volume):
	fstype = 'unknown'
	try:
		f = open('/proc/mounts')
		for x in f.readlines():
			if x.find(nas_volume) >= 0:
				fstype = x.split()[2]
				break
		f.close()
	except:
		pass
	return fstype

#------------------------------------------------------------------------------

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
		new_file_name = NAS_CONF_TMP
		new_f = open(new_file_name, 'w')
		for line in old_f.readlines():
			if line.find(NAS_CONF_END_SEP) >= 0:
				new_f.write('mount %s %s\n' % (dev, mnt))
			new_f.write(line)
		old_f.close()
		new_f.close()
		os.rename(new_file_name, NAS_CONF_FILE)
		# set file mod to 755
		os.chmod(NAS_CONF_FILE, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
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
		os.chmod(NAS_CONF_FILE, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
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
def __nas_conf_get_list():
	nas_conf_list = []
	conf_start = False
	conf_end = False
	try:
		f = open(NAS_CONF_FILE)
		for line in f.readlines():
			if line.find(NAS_CONF_START_SEP) >= 0:
				conf_start = True
				continue
			if line.find(NAS_CONF_END_SEP) >= 0:
				conf_end = True
				continue

			# load conf line:
			# (FORMAT): mount /dev/md1p1 /mnt/Share/udv1
			if conf_start and not conf_end:
				nas_dev = line.split()[1]
				mnt_path = line.split()[-1]
				nas_conf_list.append((nas_dev, mnt_path))
	except:
		pass
	finally:
		f.close()
	return nas_conf_list

def nas_conf_get_list():
	nas_conf_list = []
	try:
		for nas_dev,mnt_path in __nas_conf_get_list():
			nas_conf = NasVolumeAttr()
			nas_conf.path = mnt_path
			nas_conf.volume_name = __get_udv_name_by_dev(nas_dev) # conv /dev/md1p1 => udv1
			nas_conf.state = 'mounted'
			nas_conf.fmt_percent = 0
			nas_conf.capacity = __get_nas_volume_capacity(nas_conf.path)
			nas_conf.occupancy = __get_nas_volume_occupancy(nas_conf.path)
			nas_conf.remain = __get_nas_volume_remain(nas_conf.path)
			nas_conf.fs_type = __get_nas_volume_fstype(nas_conf.path)
			nas_conf_list.append(nas_conf.__dict__)
	except:
		pass
	return nas_conf_list



"""
格式化相关函数
"""
# 获取格式化列表
def nas_fmt_get_list():
	nas_fmt_list = []
	try:
		text = commands.getoutput('ps -au')
		for x in text.split('\n'):
			if x.find('nas-mkfs.py') < 0:
				continue
			mkfs_pid = x.split()[1]
			mkfs_tmp_dir = '%s/%s' % (TMP_DIR, mkfs_pid)
			if not os.path.exists(mkfs_tmp_dir):
				continue
			nas_fmt = NasVolumeAttr()
			nas_fmt.path = nas_tmpfs_get_value('%s/path' % mkfs_tmp_dir)
			nas_fmt.volume_name = nas_tmpfs_get_value('%s/volume_name' % mkfs_tmp_dir)
			nas_fmt.state = nas_tmpfs_get_value('%s/state' % mkfs_tmp_dir)
			fmt_per = nas_tmpfs_get_value('%s/fmt_percent' % mkfs_tmp_dir)
			if fmt_per != '':
				nas_fmt.fmt_percent = float(fmt_per)
			else:
				nas_fmt.fmt_percent = 0.0
			nas_fmt.fs_type = nas_tmpfs_get_value('%s/fs_type' % mkfs_tmp_dir)
			nas_fmt.capacity = __get_nas_volume_capacity(nas_fmt.path)
			nas_fmt.occupancy = __get_nas_volume_occupancy(nas_fmt.path)
			nas_fmt.remain = __get_nas_volume_remain(nas_fmt.path)
			nas_fmt_list.append(nas_fmt)
	except:
		pass
	return nas_fmt_list

"""
已经加载卷相关函数
"""
# 获取已经加载的卷列表
def nas_mount_get_list():
	nas_mount_list = []
	try:
		mount_result = os.popen('mount')
		for line in mount_result:
			if line.find('/mnt/Share/') > 0:
				tmp_nas_dev = line.split()[0]
				nas_mount = NasVolumeAttr()
				nas_mount.path = line.split()[2]
				nas_mount.volume_name = __get_udv_name_by_dev(tmp_nas_dev)
				nas_mount.state = 'mounted'
				nas_mount.fmt_percent = 0
				nas_mount.capacity = __get_nas_volume_capacity(nas_mount.path)
				nas_mount.occupancy = __get_nas_volume_occupancy(nas_mount.path)
				nas_mount.remain = __get_nas_volume_remain(nas_mount.path)
				nas_mount.fs_type = line.split()[4]
				nas_mount_list.append(nas_mount)
	except:
		pass
	return nas_mount_list

"""
API
"""
# 获取指定或者所有NAS卷列表
def nasGetList(volume_name):
	nas_list = nas_conf_get_list() + nas_fmt_get_list()
	if volume_name == '':
		return nas_list
	tmp_list = []
	for x in nas_list:
		if x['volume_name'] == volume_name:
			tmp_list.append(x)
			break
	return tmp_list

# 映射NAS卷
def nasMapping(udv_name, filesystem = 'ext4'):
	# 检查udv是否存在

	# 检查是否已经映射
	if isNasVolume(udv_name):
		return False,'用户数据卷 %s 已经映射为NAS卷!' % udv_name
	# 获取udv对应的设备节点
	dev = __get_udv_dev_by_name(udv_name)
	# 调用外部程序映射
	if dev=='':
		return False, '无法获取用户数据卷对应的设备节点名称!'
	mount_dir = '/mnt/Share/%s' % udv_name
	os.popen('/usr/local/bin/nas-mkfs.py --udv %s --dev %s --mount %s --filesystem %s &' % (udv_name, dev, mount_dir, filesystem))
	return True, '映射NAS卷开始，请耐心等待格式化结束!'

# 解除NAS卷映射
def nasUnmapping(volume_name):
	nas_volume_path = '/mnt/Share/%s' % volume_name
	try:
		umount_ret, umount_result = commands.getstatusoutput('2>&1 umount %s' % nas_volume_path)
		if umount_ret == 0:
			ret, msg = nas_conf_remove(nas_volume_path)
			if not ret:
				return ret,msg
			return True,'解除NAS卷映射成功!'
		elif umount_result.find('not found') >= 0:
			return False,'NAS卷 %s 不存在!' % volume_name
		elif umount_result.find('device is busy') >= 0:
			return False,'NAS卷 %s 正在被使用，请检查是否有未关闭的文件!'
		elif umount_result.find('not mounted') >= 0:
			return False,'解除NAS卷 %s 映射失败，卷未被挂载!' % volume_name
		else:
			return False,'解除NAS卷 %s 映射失败，原因未知!' % volume_name
	except:
		return False,'解除NAS卷 %s 映射失败，程序异常退出!' % volume_name

# 检查是否为NAS卷
def isNasVolume(volume_name):
	for nas_dev,mnt_path in __nas_conf_get_list():
		if mnt_path.find(volume_name) >= 0:
			return True
	for x in nas_fmt_get_list():
		if x['volume_name'] == volume_name:
			return True
	#for x in nas_mount_list():
	#	if x.volume_name == volume_name:
	#		return True
	return False

if __name__ == '__main__':
	#for x in nas_fmt_get_list():
	#	print x.__dict__
	#for x in nas_mount_get_list():
	#	print x.__dict__
	print nasGetList('Udv299_1')
"""
	for x in nas_conf_get_list():
		print x

	sys.exit(0)
	ret,msg = nas_conf_add('/dev/md1p2', '/mnt/Share/udv2')
	print msg
	ret,msg = nas_conf_remove('/mnt/Share/udv2')
	print msg
"""
"""

	if nas_conf_is_exist('/mnt/Share/udv2'):
		print 'exist'
	else:
		print 'not exist'
	if nas_conf_is_exist('/mnt/Share/udv1'):
		print 'exist'
	else:
		print 'not exist'

	# test list
	for x in nas_conf_get_list():
		print x.__dict__
"""
