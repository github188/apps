#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import statvfs
import json
import commands
import stat
from libcommon import LogInsert

reload(sys)
sys.setdefaultencoding('utf8')

NAS_CONF_FILE = '/opt/jw-conf/nas/last-conf'
NAS_CONF_TEMP = '/opt/jw-conf/nas/.nas_tmp_conf'
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
	except:
		pass
	return

def nas_tmpfs_get_value(key):
	content = ''
	try:
		f = open(key)
		content = f.readline().strip()
		f.close()
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

def __touch_default_nas_conf():
	return

#  增加配置项
def nas_conf_add(conf):
	try:
		exist = False
		if os.path.isfile(NAS_CONF_FILE):
			f = open(NAS_CONF_FILE)
			for x in f.readlines():
				y = json.loads(x)
				if conf.volume_name == y['volume_name']:
					exist = True
					break
			f.close()

		if exist:
			return False, '增加记录失败，记录已经存在'

		f = open(NAS_CONF_FILE, 'wr+')
		f.seek(0, os.SEEK_END)
		f.write('%s\n' % json.dumps(conf.__dict__))
		f.close()
	except:
		return False, '增加记录失败!'
	return True, '增加记录成功!'

# 删除指定配置项
def nas_conf_remove(volume_name):
	try:
		s = open(NAS_CONF_FILE)
		d = open(NAS_CONF_TEMP, 'w')
		for x in s.readlines():
			conf = json.loads(x)
			if conf['volume_name'] != volume_name:
				d.write(x)
		s.close()
		d.close()
		os.rename(NAS_CONF_TEMP, NAS_CONF_FILE)
	except:
		return False,'删除配置文件记录失败!'
	return True, '删除配置文件记录成功!'


"""
格式化相关函数
"""
# 获取格式化列表
def nas_fmt_get_list():
	nas_fmt_list = []
	try:
		text = commands.getoutput('ps ax')
		for x in text.split('\n'):
			if x.find('nas-mkfs.py') < 0:
				continue
			mkfs_pid = x.split()[0]
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
		#mount_result = os.popen('mount')
		for line in os.popen('mount').readlines():
			if line.find('/mnt/Share/') > 0:
				tmp_nas_dev = line.split()[0]
				nas_mount = NasVolumeAttr()
				nas_mount.path = line.split()[2]
				#nas_mount.volume_name = __get_udv_name_by_dev(tmp_nas_dev)
				nas_mount.volume_name = os.path.basename(nas_mount.path)
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

def _check_remove_duplicate(fmt_list, volume):
	for f in fmt_list:
		if f.volume_name == volume:
			fmt_list.remove(f)
			break
	return

# 获取指定或者所有NAS卷列表
def nasGetList(volume_name = ''):
	# 仅查看已经加载的nas卷列表
	if volume_name == '':
		_mnt_list = nas_mount_get_list()
		_fmt_list = nas_fmt_get_list()
		# 避免在nas-mkfs.py挂载后更新列表出现重复条目
		for m in _mnt_list:
			_check_remove_duplicate(_fmt_list, m.volume_name)
		return _mnt_list + _fmt_list

	_nas_list = []
	for x in nas_mount_get_list():
		if x.volume_name == volume_name:
			_nas_list.append(x)
			break
	if len(_nas_list) > 0:
		return _nas_list
	for x in nas_fmt_get_list():
		if x.volume_name == volume_name:
			_nas_list.append(x)
			break
	return _nas_list

# 映射NAS卷
def nasMapping(udv_name, filesystem = 'ext4'):
	# 检查udv是否存在
	if udv_name == '':
		return False, '请设置需要映射的用户数据卷名称!'

	# 检查是否已经映射
	if isNasVolume(udv_name):
		return False,'用户数据卷 %s 已经映射为NAS卷!' % udv_name
	# 获取udv对应的设备节点
	dev = __get_udv_dev_by_name(udv_name)
	# 调用外部程序映射
	if dev=='':
		return False, '无法获取用户数据卷对应的设备节点名称!'
	mount_dir = '/mnt/Share/%s' % udv_name
	cmd =  '/usr/local/bin/nas-mkfs.py --udv %s --dev %s --mount %s --filesystem %s' % (udv_name, dev, mount_dir, filesystem)
	os.popen('%s &' % cmd)
	return True, '映射NAS卷开始，请耐心等待格式化结束!'

# 解除NAS卷映射
def nasUnmapping(volume_name):
	nas_volume_path = '/mnt/Share/%s' % volume_name
	try:
		umount_ret, umount_result = commands.getstatusoutput('2>&1 umount %s' % nas_volume_path)
		if umount_ret == 0:
			nas_conf_remove(volume_name)
			LogInsert('NAS', 'Auto', 'Info', 'NAS卷 %s 解除映射成功!' % volume_name)
			return True,'解除NAS卷映射成功!'
		elif umount_result.find('not found') >= 0:
			LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 解除映射失败! NAS卷不存在' % volume_name)
			return False,'NAS卷 %s 不存在!' % volume_name
		elif umount_result.find('device is busy') >= 0:
			LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 解除映射失败! NAS卷正在被使用' % volume_name)
			return False,'NAS卷 %s 正在被使用，请检查是否有未关闭的文件!'
		elif umount_result.find('not mounted') >= 0:
			LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 解除映射失败! NAS卷未挂载' % volume_name)
			return False,'解除NAS卷 %s 映射失败，卷未被挂载!' % volume_name
		else:
			LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 解除映射失败!未知原因' % volume_name)
			return False,'解除NAS卷 %s 映射失败，原因未知!' % volume_name
	except:
		LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 解除映射失败!程序异常退出' % volume_name)
		return False,'解除NAS卷 %s 映射失败，程序异常退出!' % volume_name

# 检查是否为NAS卷
def isNasVolume(volume_name):
	for x in nas_mount_get_list() + nas_fmt_get_list():
		if x.volume_name == volume_name:
			return True
	return False

def nasUpdateCFG():
	try:
		f = open(NAS_CONF_TEMP, 'w')
		for x in nasGetList():
			f.write('%s\n' % json.dumps(x.__dict__))
		f.close()
		os.rename(NAS_CONF_TEMP, NAS_CONF_FILE)
	except:
		LogInsert('NAS', 'Auto', 'Error', '更新NAS配置失败!')
		return False, '更新配置文件失败!'
	LogInsert('NAS', 'Auto', 'Info', '更新NAS配置成功!')
	return True, '更新配置文件成功'

"""
{"capacity": 66932322304, "remain": 63343767552, "occupancy": 3588554752, "state": "mounted",
"fs_type": "ext4", "volume_name": "Udv9_2", "path": "/mnt/Share/Udv9_2", "fmt_percent": 0}
"""
def _load_conf(conf):
	udv_dev = __get_udv_dev_by_name(conf['volume_name'])
	if udv_dev == '':
		LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 挂载失败！用户数据卷不存在！' % conf['volume_name'])
		return False
	if conf['state'] == 'formatting':
		cmd = '/usr/local/bin/nas-mkfs.py'
		cmd = cmd + ' --udv %s' % conf['volume_name']
		cmd = cmd + ' --dev %s' % udv_dev
		cmd = cmd + ' --mount %s' % conf['path']
		cmd = cmd + ' --filesystem %s' % conf['fs_type']
		os.popen('2>&1 %s >/dev/null &' % cmd)
	else:
		cmd = 'mount %s %s' % (udv_dev, conf['path'])
		ret,msg = commands.getstatusoutput(cmd)
		if ret == 0:
			LogInsert('NAS', 'Auto', 'Info', 'NAS卷 %s 挂载成功!' % conf['volume_name'])
		else:
			LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 挂载失败!' % conf['volume_name'])
	return True

def nasRestoreCFG():
	try:
		f = open(NAS_CONF_FILE)
		for x in f.readlines():
			_load_conf(json.loads(x))
		f.close()
	except:
		False, 'Fail to Load NAS Conf!'
	return True,'Load NAS Conf OK!'


if __name__ == '__main__':
	conf = NasVolumeAttr()
	conf.volume_name = 'Udv8_31'
	print nas_conf_add(conf)
	#nasUpdateCFG()
	#print nas_conf_remove('Udv13_2')
