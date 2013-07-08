#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands, re, os, time, copy
from libsysmon import sysmon_event

from libcommon import *
from libsysalarm import alarm_email_send

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

DISK_HOTREP_CONF = CONF_ROOT_DIR + '/disk/hotreplace.xml'
DISK_HOTREP_DFT_CONTENT="""<?xml version="1.0" encoding="UTF-8"?>
<hot_replace>
</hot_replace>
"""

DISK_TYPE_MAP = {'Free':'空闲盘', 'Special':'专用热备盘', 'Global':'全局热备盘'}

RAID_DIR = '/tmp/.raid-info'
RAID_DIR_LOCK = RAID_DIR + '/lock'
RAID_DIR_BYMD = RAID_DIR + '/by-md'
RAID_DIR_BYNAME = RAID_DIR + '/by-name'
RAID_DIR_BYUUID = RAID_DIR + '/by-uuid'
RAID_DIR_BYDISK = RAID_DIR + '/by-disk'

# vg日志封装
def vg_log(event, msg):
	log_insert('VG', 'Auto', event, msg)

class md_attr:
	def __init__(self):
		self.name = ''
		self.dev = ''
		self.raid_level = ''
		self.raid_state = ''	# raid0需要根据disk_cnt与disk_total关系计算
		self.raid_strip = ''	# raid1需要特殊处理
		self.raid_rebuild = ''
		self.capacity = 0
		self.remain = 0		# 剩余空间
		self.max_single = 0	# 最大连续空间
		self.disk_cnt = 0	# 当前磁盘个数
		self.disk_list = []	# 当前磁盘列表, raid1需要特殊处理
		self.raid_uuid = ''	# 供磁盘上下线检测对应RAID使用
		self.disk_total = 0	# raid应该包含的磁盘个数

def get_mdattr_by_mddev(mddev):
	mdattr = md_attr()
	mdattr.dev = mddev
	if '' == mddev or os.system('[ -b %s ]' % mddev) != 0:
		return mdattr

	md = basename(mddev)
	sysdir='/sys/block/' + md
	
	mdattr.name = fs_attr_read(sysdir + '/md/array_name')
	mdattr.raid_uuid = fs_attr_read(sysdir + '/md/array_uuid')
	mdattr.raid_level = fs_attr_read(sysdir + '/md/array_level')
	
	val = fs_attr_read(sysdir + '/md/raid_disks')
	if val.isdigit():
		mdattr.disk_total = int(val)

	val = fs_attr_read(sysdir + '/md/chunk_size')
	if '0' == val:
		mdattr.raid_strip = 'N/A'
	elif val.isdigit():
		mdattr.raid_strip = str(int(val)/1024)
	else:
		mdattr.raid_strip = 'N/A'
	
	val = fs_attr_read(sysdir + '/size')
	if val.isdigit():
		mdattr.capacity = int(val)*512
		
	mdattr.remain = mdattr.capacity
	sts,output = commands.getstatusoutput('cat /sys/block/%s/%sp*/size' % (md, md))
	if 0 == sts:
		for val in output.split():
			mdattr.remain -= int(val)*512
	if mdattr.remain < 100*1024*1024:
		mdattr.remain = 0

	if mdattr.raid_level in ('1', '5', '6'):
		val = list_dir(sysdir + '/slaves')
		mdattr.disk_list = [disk_dev2slot('/dev/'+x) for x in val]
		mdattr.disk_cnt = len(mdattr.disk_list)
		
		if '5' == mdattr.raid_level:
			max_degraded = 1
		elif '6' == mdattr.raid_level:
			max_degraded = 2
		else:	# raid1
			max_degraded = mdattr.disk_total

		val = fs_attr_read(sysdir + '/md/sync_action')
		if 'recover' == val:
			mdattr.raid_state = 'rebuild'
		elif 'resync' == val:
			mdattr.raid_state = 'initial'
		else:
			val = fs_attr_read(sysdir + '/md/degraded')
			degraded = int(val)
			if 0 == degraded:
				mdattr.raid_state = 'normal'
			elif degraded <= max_degraded:
				mdattr.raid_state = 'degrade'
			else:
				mdattr.raid_state = 'fail'
		
		if 'initial' == mdattr.raid_state or 'rebuild' == mdattr.raid_state:
			faulty_disks = mdattr.disk_total - mdattr.disk_cnt
			if faulty_disks > max_degraded:
				mdattr.raid_state = 'fail'
			elif faulty_disks == max_degraded:
				mdattr.raid_state = 'degrade'
		
		if mdattr.raid_state != 'normal' and  '1' == mdattr.raid_level:
			fail = True
			for entry in list_child_dir(sysdir + '/md'):
				if entry[:2] == 'rd':
					fail = False
					break
			if fail:
				mdattr.raid_state = 'fail'
		
		if 'initial' == mdattr.raid_state or 'rebuild' == mdattr.raid_state:
			val = fs_attr_read(sysdir + '/md/sync_completed')
			if 'none' == val:
				mdattr.raid_rebuild = '100.0'
			else:
				list_tmp = val.split('/')
				resync = float(list_tmp[0])
				max_sectors = float(list_tmp[1])
				mdattr.raid_rebuild = '%.1f' % (resync*100/max_sectors)

	else:	# raid0, jbod
		f_lock = lock_file('%s/%s_tmpfs' % (RAID_DIR_LOCK, basename(mdattr.dev)))
		mdattr.disk_list = list_file('%s/%s/disk-list' % (RAID_DIR_BYMD, md))
		mdattr.disk_cnt = len(mdattr.disk_list)
		if mdattr.disk_cnt < mdattr.disk_total:
			mdattr.raid_state = 'fail'
		else:
			mdattr.raid_state = 'normal'
		unlock_file(f_lock)

	return mdattr

def md_list():
	cmd = 'ls /sys/block/ | grep md[0-9]'
	sts,output = commands.getstatusoutput(cmd)
	if sts != 0:
		return []
	return output.split()

def get_free_md():
	mds = md_list()
	for i in xrange(1, 255):
		md = "md%u" % i
		if md not in mds:
			return md
	return None

def get_md_by_name(raid_name):
	return fs_attr_read(RAID_DIR_BYNAME + os.sep + raid_name)
	
def get_md_by_mduuid(mduuid):
	return fs_attr_read(RAID_DIR_BYUUID + os.sep + mduuid)

def get_mduuid_by_md(md):
	return fs_attr_read('/sys/block/%s/md/array_uuid' % md)

def get_mdattr_by_name(raid_name):
	md = get_md_by_name(raid_name)
	if '' == md:
		return None
	return get_mdattr_by_mddev('/dev/' + md)

# 使用磁盘dev节点名称查找所在的卷组信息
def get_mdattr_by_disk(dev):
	slot = disk_dev2slot(dev)
	if None == slot:
		return None
	md = fs_attr_read(RAID_DIR_BYDISK + os.sep + slot)
	if '' == md:
		return None
	return get_mdattr_by_mddev('/dev/' + md)

# 使用mduuid查找所在卷组信息
def get_mdattr_by_mduuid(mduuid):
	md = get_md_by_mduuid(mduuid)
	if '' == md:
		return None
	return get_mdattr_by_mddev('/dev/' + md)
	
def get_mdattr_all():
	mdattr_list = []
	mds = md_list()
	for md in mds:
		mdattr = get_mdattr_by_mddev('/dev/' + md)
		mdattr_list.append(mdattr)
	return mdattr_list

def tmpfs_add_md(mddev):
	if '' == mddev or os.system('[ -b %s ]' % mddev) != 0:
		return

	md = basename(mddev)
	f_lock = lock_file('%s/%s_tmpfs' % (RAID_DIR_LOCK, md))

	sysdir = '/sys/block/%s/md' % md
	raid_name = fs_attr_read(sysdir + '/array_name')
	raid_uuid = fs_attr_read(sysdir + '/array_uuid')
	raid_level = fs_attr_read(sysdir + '/array_level')

	# raid md dir
	raid_dir_bymd = RAID_DIR_BYMD + os.sep + md
	if not os.path.exists(raid_dir_bymd):
		os.makedirs(raid_dir_bymd)
	
	fs_attr_write(raid_dir_bymd + '/name', raid_name)
	fs_attr_write(raid_dir_bymd + '/uuid', raid_uuid)
	
	val = list_dir('/sys/block/%s/slaves' % md)
	disk_list = [disk_dev2slot('/dev/'+x) for x in val]

	if raid_level == '0' or raid_level == 'JBOD':
		disks_list_dir = raid_dir_bymd + '/disk-list'
		if not os.path.exists(disks_list_dir):
			os.makedirs(disks_list_dir)

		for disk in disk_list:
			fs_attr_write(disks_list_dir + os.sep + disk, disk)
	
	# raid name dir
	fs_attr_write(RAID_DIR_BYNAME + os.sep + raid_name, md)

	# raid uuid dir
	fs_attr_write(RAID_DIR_BYUUID + os.sep + raid_uuid, md)
	
	# raid disk dir
	for disk in disk_list:
		fs_attr_write(RAID_DIR_BYDISK + os.sep + disk, md)
	
	unlock_file(f_lock)

	# check vg state, notify to sysmon
	mdattr = get_mdattr_by_mddev(mddev)
	if mdattr.raid_state == 'degrade':
		msg = '卷组 %s 降级' % mdattr.name
		sysmon_event('vg', 'degrade', mdattr.name, msg)
		vg_log('Warning', msg)
		
		# 重建raid
		md_rebuild(mdattr)
	elif mdattr.raid_state == 'fail':
		msg = '卷组 %s 失效' % mdattr.name
		sysmon_event('vg', 'fail', mdattr.name, msg)
		vg_log('Error', msg)
	
	return

def tmpfs_remove_md(mddev):
	md = basename(mddev)
	f_lock = lock_file('%s/%s_tmpfs' % (RAID_DIR_LOCK, md))

	raid_dir_bymd = RAID_DIR_BYMD + os.sep + md
	raid_name = fs_attr_read(raid_dir_bymd + '/name')
	raid_uuid = fs_attr_read(raid_dir_bymd + '/uuid')
	disk_list = list_file(raid_dir_bymd + '/disk-list')

	# raid md dir
	os.popen('rm -fr ' + raid_dir_bymd)

	# raid name dir
	_file = RAID_DIR_BYNAME + os.sep + raid_name
	if os.path.isfile(_file):
		os.unlink(_file)

	# raid uuid dir
	_file = RAID_DIR_BYUUID + os.sep + raid_uuid
	if os.path.isfile(_file):
		os.unlink(_file)
	
	# raid disk dir
	for disk in disk_list:
		_file = RAID_DIR_BYDISK + os.sep + disk
		if os.path.isfile(_file):
			os.unlink(_file)

	unlock_file(f_lock)

def tmpfs_remove_disk_from_md(mddev, slot):
	f_lock = lock_file('%s/%s_tmpfs' % (RAID_DIR_LOCK, basename(mddev)))
	# raid md dir
	_file = '%s/%s/disk-list/%s' % (RAID_DIR_BYMD, basename(mddev), slot)
	if os.path.isfile(_file):
		os.unlink(_file)
	
	# raid disk dir
	_file = RAID_DIR_BYDISK + os.sep + slot
	if os.path.isfile(_file):
		os.unlink(_file)
	unlock_file(f_lock)

def tmpfs_add_disk_to_md(mddev, slot):
	md = basename(mddev)
	f_lock = lock_file('%s/%s_tmpfs' % (RAID_DIR_LOCK, md))
	# raid md dir
	fs_attr_write('%s/%s/disk-list/%s' % (RAID_DIR_BYMD, md, slot), slot)
	
	# raid disk dir
	fs_attr_write('%s/%s' % (RAID_DIR_BYDISK, slot), md)
	unlock_file(f_lock)

def md_create(raid_name, level, chunk, slots):
	f_lock = lock_file(RAID_REBUILD_LOCK)
	ret,msg = __md_create(raid_name, level, chunk, slots)
	unlock_file(f_lock)
	if ret:
		vg_log('Info', '使用磁盘 %s 创建RAID级别为 %s 的卷组 %s 成功' % (slots, level, raid_name))
	else:
		vg_log('Error', '使用磁盘 %s 创建RAID级别为 %s 的卷组 %s 失败%s' % (slots, level, raid_name, msg))
	return ret,msg

def __md_create(raid_name, level, chunk, slots):
	#create raid
	md = get_free_md()
	if md == None:
		return False,"RIAD数达到最大限制"
	mddev = '/dev/' + md
	
	# 检查磁盘是否仍为空闲盘
	slot_list = slots.split()
	disk_info_list = json.loads(commands.getoutput('disk --list'))['rows']
	for disk_info in disk_info_list:
		if disk_info['slot'] in slot_list:
			if disk_info['state'] != 'Free' and disk_info['state'] != 'Invalid':
				return False, "磁盘 %s 不是空闲盘或无效RAID盘" % disk_info['slot']

			slot_list.remove(disk_info['slot'])
	
	if len(slot_list) > 0:
		return False, "未找到磁盘 %s, 可能已掉线" % slot_list[0]
	
	dev_list = disks_slot2dev(slots.split())
	if len(dev_list) == 0:
		return False, "没有磁盘"
	devs = " ".join(dev_list)

	# enable all disk bad sect redirection
	for dev in dev_list:
		disk_bad_sect_remap_enable(basename(dev))

	if level.lower() == 'jbod':
		level = 'linear'

	cmd = "2>&1 mdadm -CR %s -l %s -n %u %s --metadata=1.2 --homehost=%s -f" % (mddev, level, len(dev_list), devs, raid_name)
	if level != 'linear':
		cmd += ' -c %s' % chunk
	if level in ('5', '6'):
		cmd += " --bitmap=internal"
	if level in ('1', '5', '6'):
		sts,size = commands.getstatusoutput('head -n 1 /tmp/disk_use_size')
		if sts != 0:
			size = '0'
		if size == 'clean':
			cmd += " --assume-clean"
		elif size.isdigit() and int(size) >= 1000000:
			cmd += " -z " + size

	sts,out = commands.getstatusoutput(cmd)
	if sts != 0:
		# try to remove mddev
		md_stop(mddev)
		cleanup_disks_mdinfo(dev_list)
		disk_update_by_slots(disks_dev2slot(dev_list))
		return False, "创建卷组失败"

	msg = ''

	retry_cnt = 10
	while retry_cnt > 0:
		# 强制重写分区表
		cmd = 'sys-manager udv --force-init-vg %s >/dev/null 2>&1' % mddev
		if os.system(cmd) == 0:
			break
		
		time.sleep(0.5)
		retry_cnt -= 1
	
	if 0 == retry_cnt:
		msg = ' 初始化分区表失败'

	return True, '创建卷组成功%s' % msg

def md_is_used(raid_name):
	try:
		d = json.loads(commands.getoutput('sys-manager udv --list --vg %s' % raid_name))
		if d['total'] == 0:
			return False
	except:
		pass
	return True

def md_stop(mddev):
	cmd = "mdadm -S %s 2>&1" % mddev
	sts,out = commands.getstatusoutput(cmd)
	if out.find('mdadm: stopped') < 0:
		return False
	return True

def md_del(raid_name):
	ret,msg = __md_del(raid_name)
	if ret:
		msg = '删除卷组 %s 成功' % raid_name
		vg_log('Info', msg)
	else:
		vg_log('Error', '删除卷组 %s 失败, %s' % (raid_name, msg))
	return ret,msg

def __md_del(raid_name):
	md = get_md_by_name(raid_name)
	if (md == ''):
		return False, "卷组 %s 不存在" % raid_name
	mddev = '/dev/' + md
	try:
		mdattr = get_mdattr_by_mddev(mddev)
		md_uuid = mdattr.raid_uuid
		if mdattr.raid_state != 'fail' and md_is_used(raid_name):
			return False, '卷组存在未删除的用户数据卷'
	except:
		md_uuid = ''
	dev_list = disks_slot2dev(mdattr.disk_list)
	if not md_stop(mddev):
		return False,"停止%s失败, 设备正在使用中" % raid_name

	# 专用热备盘设置为空闲盘
	f_lock = lock_file(RAID_REBUILD_LOCK)
	if f_lock != None:
		for slot in get_specials_by_mduuid(md_uuid):
			disk_set_type(slot, 'Free')
		unlock_file(f_lock)

	cleanup_disks_mdinfo(dev_list)
	disk_update_by_slots(mdattr.disk_list)

	sysmon_event('vg', 'remove', mdattr.name, '卷组 %s 删除成功' % mdattr.name)
	sysmon_event('disk', 'led_off', 'disks=%s' % list2str(disks_dev2slot(dev_list), ','), '')
	return True,"删除卷组成功"

def disk_serial2slot(serial):
	try:
		cmd = 'sys-manager disk --list'
		disk_list = json.loads(commands.getoutput(cmd))
		for disk in disk_list['rows']:
			if disk['serial'] == serial:
				return str(disk['slot'])
	except:
		pass
	return None

def disk_slot2serial(slot):
	_disk_serial = None
	try:
		cmd = 'sys-manager disk --list --slot-id %s' % slot
		_disk_info = json.loads(commands.getoutput(cmd))
		_disk_serial = str(_disk_info['serial'])
	except:
		pass
	return _disk_serial

# 获取磁盘状态
# 返回的状态:
#	* Free  - 空闲盘		 (*)
#	* Special - 专用热备盘   (*)
#	* Global  - 全局热备盘   (*)
#	* Invalid - 无效RAID盘   (*)
#	* RAID	- RAID数据盘
#	* N/A	 - 获取状态失败
def disk_get_state(slot):
	state = 'N/A'
	try:
		cmd = 'sys-manager disk --list --slot-id %s' % slot
		result = json.load(os.popen(cmd))
		state = result['state']
	except:
		pass
	return state

# 检查磁盘热备盘配置, 如果不存在就创建默认配置
def check_disk_hotrep_conf():
	if not os.path.isfile(DISK_HOTREP_CONF):
		d,f = os.path.split(DISK_HOTREP_CONF)
		os.makedirs(d) if not os.path.isdir(d) else None
		fd = open(DISK_HOTREP_CONF, 'w')
		fd.write(DISK_HOTREP_DFT_CONTENT)
		fd.close()
	return

# 设置磁盘管理类型：
#	* Global   - 全局热备盘
#	* Special  - 专用热备盘
#	* Free     - 空闲盘
def disk_set_type(slot, disk_type, raid_name=''):

	if slot == '':
		return False, '请输入磁盘槽位号'

	state = disk_get_state(slot)
	if state == 'N/A':
		return False, '无法获取槽位号为 %s 的磁盘状态' % slot
	elif state == 'RAID':
		return False, '槽位号为 %s 的磁盘是RAID盘, 无法设置%s' % (slot, DISK_TYPE_MAP[disk_type])
	elif state == disk_type and disk_type != 'Special':
		return True, '槽位号为 %s 磁盘已经是%s, 无需设置' % (slot, DISK_TYPE_MAP[state])

	md_uuid = ''
	if disk_type == 'Special':
		if raid_name == '':
			return False, '参数不正确,设置专用热备盘必须指定卷组名称'
		mdattr = get_mdattr_by_name(raid_name)
		if mdattr != None:
			md_uuid = mdattr.raid_uuid
		else:
			return False, '卷组 %s 不存在, 请检查参数' % raid_name
	elif disk_type == 'Free':
		remove_hotrep_by_slot(slot)
		cleanup_disk_mdinfo(disk_slot2dev(slot))
		disk_update_by_slots(slot)
		# 通知监控进程
		sysmon_event('disk', 'led_off', 'disks=%s' % slot, '设置槽位号为 %s 的磁盘为空闲盘' % slot)
		sysmon_event('disk', 'buzzer_off', slot, '')
		vg_log('Info', "设置磁盘 %s 为 空闲盘" % slot)
		return True, '设置槽位号为 %s 的磁盘为空闲盘成功' % slot
	elif disk_type != 'Global':
		return False, '参数不正确:请指定需要设置的磁盘类型'

	check_disk_hotrep_conf()

	doc = xml_load(DISK_HOTREP_CONF)
	if None == doc:
		return False, '打开配置文件 %s 失败' % DISK_HOTREP_CONF

	disk_serial = disk_slot2serial(slot)

	set_exist = False
	root = doc.documentElement
	for item in root.getElementsByTagName('disk'):
		# 更新已经存在的节点
		if disk_serial == item.getAttribute('serial'):
			item.setAttribute('type', disk_type)
			item.setAttribute('md_uuid', md_uuid)
			item.setAttribute('md_name', raid_name)
			set_exist = True
			break

	# 增加新节点
	if not set_exist:
		impl = minidom.getDOMImplementation()
		dom = impl.createDocument(None, 'disk', None)
		disk_node = dom.createElement('disk')
		disk_node.setAttribute('serial', disk_serial)
		disk_node.setAttribute('type', disk_type)
		disk_node.setAttribute('md_uuid', md_uuid)
		disk_node.setAttribute('md_name', raid_name)
		root.appendChild(disk_node)

	# 更新xml配置文件
	xml_save(doc, DISK_HOTREP_CONF)

	# 清除磁盘上的superblock信息
	cleanup_disk_mdinfo(disk_slot2dev(slot))
	disk_update_by_slots(slot)

	msg = '设置磁盘 %s 为' % slot
	if disk_type == 'Special':
		msg += '卷组 %s 的专用热备盘' % raid_name
	else:
		msg += ' 全局热备盘'
	vg_log('Info', msg)

	# 通知监控进程
	sysmon_event('disk', 'led_on', 'disks=%s' % slot, msg)
	sysmon_event('disk', 'buzzer_off', slot, '')

	return True, msg

def hotrep_conf_load():
	check_disk_hotrep_conf()
	return xml_load(DISK_HOTREP_CONF)

# 获取指定RAID所有专用热备盘
def get_specials_by_mduuid(md_uuid=''):
	spec_list = []

	if md_uuid == '':
		return spec_list

	doc = hotrep_conf_load()
	if doc == None:
		return spec_list
	root = doc.documentElement
	try:
		for item in root.getElementsByTagName('disk'):
			if item.getAttribute('md_uuid') == md_uuid and item.getAttribute('type') == 'Special':
				serial = item.getAttribute('serial')
				spec_list.append(disk_serial2slot(serial))
	except:
		pass
	return spec_list

# 获取热备盘
# 优先返回专用热备盘, 如果没有则返回全局热备盘, 如果没有则返回None
def get_hotrep_by_mduud(md_uuid=''):
	disk_info = {}
	tmp_info = {}
	update_conf = False
	global_exist = 0
	
	doc = hotrep_conf_load()
	if doc == None:
		return disk_info
	root = doc.documentElement
	try:
		for item in root.getElementsByTagName('disk'):
			tmp_info['serial'] = item.getAttribute('serial')
			tmp_info['type'] = item.getAttribute('type')
			
			slot = disk_serial2slot(tmp_info['serial'])
			if slot == None:
				root.removeChild(item)
				update_conf = True
				continue

			# 专用热备盘
			if md_uuid == item.getAttribute('md_uuid'):
				disk_info = tmp_info
				disk_info['type'] = '专用热备盘'
				break
			# 全局热备盘
			if global_exist == 0 and tmp_info['type'] == 'Global':
				disk_info = copy.deepcopy(tmp_info)
				disk_info['type'] = '全局热备盘'
				global_exist = 1
	except:
		pass
	
	if update_conf:
		xml_save(doc, DISK_HOTREP_CONF)

	return disk_info

def remove_hotrep_by_serial(serial):
	update_conf = False
	doc = hotrep_conf_load()
	if doc == None:
		return False

	root = doc.documentElement
	for item in root.getElementsByTagName('disk'):
		if serial == item.getAttribute('serial'):
			root.removeChild(item)
			update_conf = True
			break

	if update_conf:
		return xml_save(doc, DISK_HOTREP_CONF)

	return False

def remove_hotrep_by_slot(slot):
	disk_serial = disk_slot2serial(slot)
	if disk_serial != None:
		return remove_hotrep_by_serial(disk_serial)
	else:
		return False

RAID_REBUILD_LOCK = RAID_DIR_LOCK + '/raid_rebuild'
def md_rebuild(mdattr, hotrep_disk_slot = ''):
	# 使用文件锁同步多个raid重建, 防止争抢全局热备盘和空闲盘
	f_lock = lock_file(RAID_REBUILD_LOCK)
	if None == f_lock:
		vg_log('Error', '系统异常: 文件 %s 加锁失败' % RAID_REBUILD_LOCK)
		return

	rebuild_ok = False
	event = 'Error'
	msg = ''
	subject = '卷组%s启动重建失败' % mdattr.name
	disk_type = 'Hot'
	disk = get_hotrep_by_mduud(mdattr.raid_uuid)
	if disk == {}:
		disk = get_free_disk()
		disk_type = 'Free'
	if disk == {}:
		msg = '未找到热备盘和空闲盘重建卷组 %s' % mdattr.name
	else:
		slot = disk_serial2slot(disk['serial'])
		diskdev = disk_slot2dev(slot)
		if add_disk_to_md(mdattr.dev, diskdev) == 0:
			rebuild_ok = True
			msg = '%s %s 加入卷组 %s 成功' % (disk['type'], slot, mdattr.name)
			subject = '卷组%s启动重建成功' % mdattr.name
			
			if disk_type != 'Free':
				remove_hotrep_by_serial(disk['serial'])
			
			# 空闲盘也要及时更新状态, 防止状态未更新又被用来重建其他raid
			disk_update_by_slots(slot)
		else:
			msg =  '%s %s 加入卷组 %s 失败' % (disk['type'], slot, mdattr.name)
	
	unlock_file(f_lock)
	
	if rebuild_ok:
		event = 'Info'
		if hotrep_disk_slot != '':
			msg += ', 由磁盘 %s 坏块过多触发, 卷组存在降级风险, 预先使用源盘重建' % hotrep_disk_slot
		else:
			msg += ', 由卷组降级触发'
	else:
		if hotrep_disk_slot != '':
			msg += ', 由磁盘 %s 坏块过多触发, 卷组存在降级风险, 请尽快添加或更换热备盘' % hotrep_disk_slot
		else:
			msg += ', 由卷组降级触发, 请尽快添加或更换热备盘, 并尝试手动重建'

	vg_log(event, msg)
	alarm_email_send(subject, msg)
	return rebuild_ok

def inc_md_rebuilder_cnt(md):
	filepath = '%s/%s/rebuilder_cnt' % (RAID_DIR_BYMD, md)
	cnt = 1
	f_lock = lock_file('%s/%s_rebuilder' % (RAID_DIR_LOCK, md))
	if os.path.isfile(filepath):
		val = fs_attr_read(filepath)
		if val.isdigit():
			cnt = int(val) + 1
	
	fs_attr_write(filepath, str(cnt))
	unlock_file(f_lock)
	return cnt

def dec_md_rebuilder_cnt(md):
	filepath = '%s/%s/rebuilder_cnt' % (RAID_DIR_BYMD, md)
	cnt = 0
	f_lock = lock_file('%s/%s_rebuilder' % (RAID_DIR_LOCK, md))
	if os.path.isfile(filepath):
		val = fs_attr_read(filepath)
		if val.isdigit():
			cnt = int(val) - 1
	
	fs_attr_write(filepath, str(cnt))
	unlock_file(f_lock)

def get_md_rebuilder_cnt(md):
	filepath = '%s/%s/rebuilder_cnt' % (RAID_DIR_BYMD, md)
	cnt = 0
	f_lock = lock_file('%s/%s_rebuilder' % (RAID_DIR_LOCK, md))
	if os.path.isfile(filepath):
		val = fs_attr_read(filepath)
		if val.isdigit():
			cnt = int(val)

	unlock_file(f_lock)
	return cnt

# -------- 磁盘信息定义 -----------
class DiskInfo():
	def __init__(self):
		self.dev = ''		# e.g. /dev/sdb
		self.slot = ''
		self.uuid = ''
		self.md_uuid = ''

def get_disk_info(dev):
	info = DiskInfo()
	info.dev = dev
	info.slot = disk_dev2slot(dev)
	ret,txt = commands.getstatusoutput('mdadm -E %s' % dev)
	if ret == 0:
		for line in txt.split('\n'):
			if line.find('Device UUID : ') >= 0:
				info.uuid = line.split('Device UUID : ')[-1]
			elif line.find('Array UUID : ') >= 0:
				info.md_uuid = line.split('Array UUID : ')[-1]
	return info

def disk_slot2dev(slot):
	cmd = "us_cmd disk name " + slot + " 2>/dev/null"
	out = commands.getoutput(cmd).strip()
	if (out.find("/dev/sd") == -1):
		return None
	return out

def disks_slot2dev(slots):
	list = [];
	for slot in slots:
		dev = disk_slot2dev(slot)
		list.append(dev)

	return list

def disk_dev2slot(dev):
	cmd = "us_cmd disk slot " + dev + " 2>/dev/null"
	out = commands.getoutput(cmd)
	if (out.find(":") == -1):
		return None
	return out

def disks_dev2slot(devs):
	list = [];
	for dev in devs:
		slot = disk_dev2slot(dev)
		list.append(slot)

	return list

def disk_update_by_slots(slots):
	if isinstance(slots, list):
		slot_list = slots
	else:
		slot_list = slots.split()
		
	for slot in slot_list:
		try:
			cmd = 'us_cmd disk update %s' % slot
			commands.getoutput(cmd)
		except:
			pass

def disk_bad_sect_remap_enable(disk):
	cmd = 'echo "enable" > /sys/block/%s/bad_sect_map/stat' % basename(disk)
	ret,msg = commands.getstatusoutput(cmd)
	return True if ret == 0 else False

def cleanup_disk_mdinfo(dev):
	cmd = "mdadm --zero-superblock %s 2>&1" % dev
	sts,out = commands.getstatusoutput(cmd)

def cleanup_disks_mdinfo(devs):
	if isinstance(devs, str):
		dev_list = devs.split()
	else:
		dev_list = devs

	for dev in dev_list:
		cleanup_disk_mdinfo(dev)

def get_free_disk():
	disk_info = {}
	try:
		_cmd = 'us_cmd disk --list'
		ret,text = commands.getstatusoutput(_cmd)
		if ret != 0:
			return disk_info
		disk_list = json.loads(text)
		for x in disk_list['rows']:
			if x['state'] == 'Free':
				disk_info['type'] = '空闲盘'
				disk_info['serial'] = x['serial']
				break
	except:
		pass
	return disk_info

def faulty_disk_in_md(mddev, diskdev):
	cmd = 'mdadm --set-faulty %s %s 2>&1' % (mddev, basename(diskdev))
	os.system(cmd)

# 从指定卷组删除磁盘
def remove_disk_from_md(mddev, diskdev):
	retry_cnt = 10
	while retry_cnt > 0:
		cmd = 'mdadm --remove %s %s 2>&1' % (mddev, basename(diskdev))
		if os.system(cmd) == 0:
			break
		time.sleep(0.5)
		retry_cnt -= 1	
	
	tmpfs_remove_disk_from_md(mddev, disk_dev2slot(diskdev))

# 将磁盘加入指定卷组
def add_disk_to_md(mddev, diskdev):
	disk_bad_sect_remap_enable(diskdev)
	cmd = 'mdadm --add %s %s 2>&1' % (mddev, diskdev)
	ret,msg = commands.getstatusoutput(cmd)
	
	tmpfs_add_disk_to_md(mddev, disk_dev2slot(diskdev))
	return ret
	

# -----------------------------------------------------------------------------
if __name__ == "__main__":
	sys.exit(0)
