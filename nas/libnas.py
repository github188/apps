#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import os, sys
import statvfs
import json
import commands
import stat
from libcommon import *
from libmd import get_md_by_mduuid, get_mduuid_by_md, get_mdattr_by_mddev
from libudv import get_dev_byudvname, get_udvname_bydev, get_iscsivolname_bydev

reload(sys)
sys.setdefaultencoding('utf8')

NAS_CONF_DIR = CONF_ROOT_DIR + '/nas'
NAS_CONF_FILE = NAS_CONF_DIR + '/nas.conf'
NAS_DIR = '/var/run/nas-info'
NAS_CONF_LOCK = NAS_DIR + '/.lock_conf'
if software_type() == 'IPSAN-NAS':
	MOUNT_ROOT = '/mnt/share'
else:
	MOUNT_ROOT = '/mnt'

NAS_CONF_DEF = """<?xml version="1.0" encoding="UTF-8"?>
<nas_conf>
</nas_conf>
"""

# 获取nas卷容量
def get_nasvol_size(mount_dir):
	size = 0
	try:
		vfs = os.statvfs(mount_dir)
		size = (vfs.f_blocks-(vfs.f_bfree-vfs.f_bavail)) * vfs.f_bsize
	except:
		pass
	return size

# 获取nas卷已经剩余空间
def get_nasvol_free(mount_dir):
	free = 0
	try:
		vfs = os.statvfs(mount_dir)
		free = vfs.f_bavail * vfs.f_bsize
	except:
		pass
	return free

# 获取nas卷已经使用空间
def get_nasvol_used(mount_dir):
	size = 0
	try:
		vfs = os.statvfs(mount_dir)
		size = (vfs.f_blocks-vfs.f_bfree) * vfs.f_bsize
	except:
		pass
	return size

#------------------------------------------------------------------------------
class NasVolume:
	def __init__(self):
		self.udv_dev = ''
		self.path = ''		# 被挂载的路径 eg. /mnt/share/udv1
		self.volume_name = ''	# 卷名称，实际为udv名称
		self.vg_name = ''
		self.state = ''		# NAS卷状态: formatting,mounted,formatted
		self.fmt_percent = 0	# 格式化进度，取值 0 ~ 100
		self.capacity = 0	# 容量，单位：字节
		self.occupancy = 0	# 已经使用容量，单位：字节
		self.remain = 0		# 剩余容量，单位：字节
		self.fs_type = ''	# 文件系统类型

# 增加配置项
def nas_conf_add(md_uuid, part_num, state, filesystem, mount_dir):
	f_lock = lock_file(NAS_CONF_LOCK)

	doc = xml_load(NAS_CONF_FILE)
	if None == doc:
		unlock_file(f_lock)
		return False

	root = doc.documentElement
	impl = minidom.getDOMImplementation()
	dom = impl.createDocument(None, 'volume', None)
	vol_node = dom.createElement('volume')
	vol_node.setAttribute('md_uuid', md_uuid)
	vol_node.setAttribute('part_num', part_num)
	vol_node.setAttribute('state', state)
	vol_node.setAttribute('filesystem', filesystem)
	vol_node.setAttribute('mount_dir', mount_dir)
	root.appendChild(vol_node)

	ret = xml_save(doc, NAS_CONF_FILE)
	unlock_file(f_lock)
	return ret

# 删除配置项
def nas_conf_remove(md_uuid, part_num):
	f_lock = lock_file(NAS_CONF_LOCK)

	ret = True
	update_conf = False
	doc = xml_load(NAS_CONF_FILE)
	if None == doc:
		unlock_file(f_lock)
		return False

	root = doc.documentElement
	for item in root.getElementsByTagName('volume'):
		if item.getAttribute('md_uuid') == md_uuid and item.getAttribute('part_num') == part_num:
			mount_dir = item.getAttribute('mount_dir')
			os.system('rm -rf %s' % mount_dir)
			root.removeChild(item)
			update_conf = True
			break

	if update_conf:
		ret = xml_save(doc, NAS_CONF_FILE)

	unlock_file(f_lock)
	return ret

# 更新配置项
def nas_conf_update(md_uuid, part_num, state, filesystem, mount_dir):
	f_lock = lock_file(NAS_CONF_LOCK)

	ret = True
	update_conf = False
	doc = xml_load(NAS_CONF_FILE)
	if None == doc:
		unlock_file(f_lock)
		return False

	root = doc.documentElement
	for item in root.getElementsByTagName('volume'):
		if item.getAttribute('md_uuid') == md_uuid and item.getAttribute('part_num') == part_num:
			item.setAttribute('state', state)
			item.setAttribute('filesystem', filesystem)
			item.setAttribute('mount_dir', mount_dir)
			update_conf = True
			break

	if update_conf:
		ret = xml_save(doc, NAS_CONF_FILE)

	unlock_file(f_lock)
	return ret

def get_mduuid_partnum_byudvdev(udv_dev):
	val = basename(udv_dev).split('p')
	if len(val) != 2:
		return '', ''

	md = val[0]
	part_num = val[1]
	md_uuid = get_mduuid_by_md(md)
	if '' == md_uuid:
		return '', ''

	return md_uuid, part_num

def nas_conf_add_bydev(udv_dev, state, filesystem, mount_dir):
	md_uuid, part_num = get_mduuid_partnum_byudvdev(udv_dev)
	if md_uuid != '':
		return nas_conf_add(md_uuid, part_num, state, filesystem, mount_dir)

	return False

def nas_conf_remove_bydev(udv_dev):
	md_uuid, part_num = get_mduuid_partnum_byudvdev(udv_dev)
	if md_uuid != '':
		return nas_conf_remove(md_uuid, part_num)

	return False

def nas_conf_update_bydev(udv_dev, state, filesystem, mount_dir):
	md_uuid, part_num = get_mduuid_partnum_byudvdev(udv_dev)
	if md_uuid != '':
		return nas_conf_update(md_uuid, part_num, state, filesystem, mount_dir)

	return False

# 获取指定或者所有NAS卷列表
def get_nasvol_list(volume_name = '', state = 'all', not_fail = False):
	nasvol_list_tmp = []
	nasvol_list = []

	if volume_name != '':
		udv_dev = get_dev_byudvname(volume_name)
		if '' == udv_dev:
			return nasvol_list

		md_uuid_input, part_num_input = get_mduuid_partnum_byudvdev(udv_dev)
		if '' == md_uuid_input:
			return nasvol_list

	found = False
	f_lock = lock_file(NAS_CONF_LOCK)
	doc = xml_load(NAS_CONF_FILE)
	unlock_file(f_lock)
	if None == doc:
		return nasvol_list

	root = doc.documentElement
	for item in root.getElementsByTagName('volume'):
		md_uuid = item.getAttribute('md_uuid')
		part_num = item.getAttribute('part_num')
		if volume_name != '':
			if md_uuid_input != md_uuid or part_num_input != part_num:
				continue
			else:
				found = True

		md = get_md_by_mduuid(md_uuid)
		if md != '':
			vol_info = NasVolume()
			vol_info.udv_dev = '/dev/%sp%s' % (md, part_num)
			vol_info.state = item.getAttribute('state')
			vol_info.fs_type = item.getAttribute('filesystem')
			vol_info.path = item.getAttribute('mount_dir')
			nasvol_list_tmp.append(vol_info)

		if found:
			break

	for vol_info in nasvol_list_tmp:
		mdattr = get_mdattr_by_mddev(vol_info.udv_dev.split('p')[0])
		if not_fail and 'fail' == mdattr.raid_state:
			continue
		if state != 'all' and state != vol_info.state:
			continue
		if 'fail' == mdattr.raid_state:
			vol_info.state = 'fail'
		vol_info.volume_name = get_udvname_bydev(vol_info.udv_dev)
		vol_info.vg_name = mdattr.name
		vol_info.fmt_percent = 'N/A'
		if vol_info.state == 'mounted':
			vol_info.capacity = get_nasvol_size(vol_info.path)
			vol_info.occupancy = get_nasvol_used(vol_info.path)
			vol_info.remain = get_nasvol_free(vol_info.path)
		elif vol_info.state == 'formatting':
			vol_info.fmt_percent = nas_fmt_record_get(vol_info.volume_name)

		nasvol_list.append(vol_info)

	return nasvol_list

# 挂载NAS卷
def nas_vol_mount(udv_dev, mount_dir):
	if not os.path.exists(mount_dir):
		os.makedirs(mount_dir)

	cmd = 'mount %s %s >/dev/null && mount -o remount,acl %s %s >/dev/null' % (udv_dev, mount_dir, udv_dev, mount_dir)
	ret,msg = commands.getstatusoutput(cmd)
	if ret != 0:
		os.rmdir(mount_dir)
		return False

	# 设置访问权限 777
	os.chmod(mount_dir, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
	return True

# 卸载NAS卷
def nas_vol_umount(mount_dir):
	ret,msg = commands.getstatusoutput('umount ' + mount_dir)
	if ret != 0:
		return False

# 记录格式化进度
def nas_fmt_record_set(volume_name, val):
	nas_dir = NAS_DIR + os.sep + volume_name
	if not os.path.isdir(nas_dir):
		os.mkdir(nas_dir)

	fs_attr_write(nas_dir + '/fmt_percent', val)

# 获取格式化进度
def nas_fmt_record_get(volume_name):
	record_file = NAS_DIR + os.sep + volume_name + '/fmt_percent'
	if os.path.exists(record_file):
		return fs_attr_read(record_file)

	return ''

# 删除格式化记录
def nas_fmt_record_remove(volume_name):
	record_file = NAS_DIR + os.sep + volume_name + '/fmt_percent'
	if os.path.exists(record_file):
		os.remove(record_file)

def nas_vol_format(udv_name, udv_dev, filesystem, mount_dir):
	nas_fmt_record_set(udv_name, '0.00')
	cmd =  'nas_mkfs --udv %s --dev %s --mount %s --filesystem %s' % (udv_name, udv_dev, mount_dir, filesystem)
	os.popen('%s &' % cmd)

# 添加NAS卷, 格式化并挂载
def nas_vol_add(udv_name, udv_dev = '', filesystem = 'ext4', mount_dir = ''):
	if software_type() == 'IPSAN-NAS':
		err_msg = '添加NAS卷 %s 映射失败' % udv_name
	else:
		err_msg = '添加文件系统 %s 失败' % udv_name

	# 检查文件系统
	fs_list = ['ext3', 'ext4', 'xfs']
	if filesystem not in fs_list:
		return False, err_msg + ', 不支持 %s 类型的文件系统' % filesystem

	# 检查挂载目录
	if mount_dir != '':
		if not os.path.isabs(mount_dir):
			return False, err_msg + ', %s 不是绝对路径' % mount_dir

		if os.path.ismount(mount_dir):
			return False, err_msg + ', %s 已经挂载' % mount_dir
	else:
		mount_dir = MOUNT_ROOT + os.sep + udv_name

	# 获取udv对应的设备节点
	if '' == udv_dev:
		udv_dev = get_dev_byudvname(udv_name)
		if '' == udv_name or '' == udv_dev:
			return False, err_msg + ', 用户数据卷不存在'

	# 检查是否已经映射
	if is_nasvolume(udv_name):
		return False, err_msg + ', 用户数据卷已经映射为NAS卷'

	if get_iscsivolname_bydev(udv_dev) != '':
		return False, err_msg + ', 用户数据卷已经映射为iSCSI卷'

	if not nas_conf_add_bydev(udv_dev, 'formatting', filesystem, mount_dir):
		return False, err_msg + ', 更新配置文件失败'

	# 启动格式化
	nas_vol_format(udv_name, udv_dev, filesystem, mount_dir)

	if software_type() == 'IPSAN-NAS':
		return True, '映射NAS卷 %s 开始, 请耐心等待格式化结束' % udv_name
	else:
		return True, '添加文件系统 %s 成功, 请耐心等待格式化结束' % udv_name

# 删除NAS卷
def nas_vol_remove(volume_name):
	if software_type() == 'IPSAN-NAS':
		err_msg = '解除NAS卷 %s 映射失败' % volume_name
	else:
		err_msg = '删除文件系统 %s 失败' % volume_name

	udv_dev = get_dev_byudvname(volume_name)
	if '' == udv_dev:
		if software_type() == 'IPSAN-NAS':
			return False, err_msg + ', NAS卷不存在'
		else:
			return False, err_msg + ', 用户数据卷不存在'

	cmd = 'pid=`ps -ef | grep "nas-mkfs.sh %s " |grep -v grep | awk \'{ print $2 }\'`; [ ! -z "$pid" ] && kill -9 $pid' % udv_dev
	os.system(cmd)
	cmd = 'pid=`ps -ef | grep "mkfs\..* %s$" |grep -v grep | awk \'{ print $2 }\'`; [ ! -z "$pid" ] && kill -9 $pid' % udv_dev
	os.system(cmd)

	cmd = 'mount | grep -q ' + udv_dev
	if os.system(cmd) == 0:
		ret, msg = commands.getstatusoutput('2>&1 umount ' + udv_dev)
		if ret != 0:
			if msg.find('device is busy') >= 0:
				if software_type() == 'IPSAN-NAS':
					return False, err_msg + ', NAS卷正在使用'
				else:
					return False, err_msg + ', 文件系统正在使用'
			else:
				return False, err_msg + ', 卸载目录失败, 未知原因'

	if not nas_conf_remove_bydev(udv_dev):
		return False, err_msg + ', 更新配置文件失败'

	if software_type() == 'IPSAN-NAS':
		return True, '解除NAS卷 %s 映射成功' % volume_name
	else:
		return True, '删除文件系统 %s 成功' % volume_name

# 检查是否为NAS卷
def is_nasvolume(udv_name):
	if '' == udv_name:
		return False

	udv_dev = get_dev_byudvname(udv_name)
	if '' == udv_dev:
		return False

	md_uuid, part_num = get_mduuid_partnum_byudvdev(udv_dev)
	if '' == md_uuid:
		return False

	found = False
	f_lock = lock_file(NAS_CONF_LOCK)
	doc = xml_load(NAS_CONF_FILE)
	unlock_file(f_lock)
	if None == doc:
		return False

	root = doc.documentElement
	for item in root.getElementsByTagName('volume'):
		if item.getAttribute('md_uuid') == md_uuid and item.getAttribute('part_num') == part_num:
			found = True
			break

	return found

def nas_conf_load():
	if not os.path.isdir(NAS_DIR):
		os.mkdir(NAS_DIR)

	if not os.path.isdir(MOUNT_ROOT):
		os.mkdir(MOUNT_ROOT)

	f_lock = lock_file(NAS_CONF_LOCK)

	if not os.path.isfile(NAS_CONF_FILE):
		if not os.path.isdir(NAS_CONF_DIR):
			os.makedirs(NAS_CONF_DIR)

		fd = open(NAS_CONF_FILE, 'w')
		fd.write(NAS_CONF_DEF)
		fd.close()
		unlock_file(f_lock)
		return True, 'Create default NAS conf OK'

	update_conf = False
	doc = xml_load(NAS_CONF_FILE)
	if None == doc:
		unlock_file(f_lock)
		return False, 'Load NAS conf failed, open %s error' % NAS_CONF_FILE

	root = doc.documentElement
	for item in root.getElementsByTagName('volume'):
		md_uuid = item.getAttribute('md_uuid')
		part_num = item.getAttribute('part_num')
		state = item.getAttribute('state')
		filesystem = item.getAttribute('filesystem')
		mount_dir = item.getAttribute('mount_dir')

		udv_dev = ''
		udv_name = ''
		if md_uuid != '' and part_num != '':
			md = get_md_by_mduuid(md_uuid)
			if md != '':
				udv_dev = '/dev/%sp%s' % (md, part_num)
				udv_name = get_udvname_bydev(udv_dev)

		if '' == udv_name or '' == state or '' == filesystem:
			root.removeChild(item)
			update_conf = True
			continue

		if 'mounted' == state:
			nas_vol_mount(udv_dev, mount_dir)
		else:
			nas_vol_format(udv_name, udv_dev, filesystem, mount_dir)

	if update_conf:
		xml_save(doc, NAS_CONF_FILE)

	unlock_file(f_lock)
	return True,'Load NAS Conf OK'

def nas_show_mount_root():
	print MOUNT_ROOT
	sys.exit(0)

if __name__ == '__main__':
	sys.exit(0)
