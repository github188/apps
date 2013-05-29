#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands, re, os, time, copy
from xml.dom import minidom
from libsysmon import sysmon_event
import xml

from libcommon import *

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

DISK_HOTREP_CONF = CONF_ROOT_DIR + '/disk/hotreplace.xml'
DISK_HOTREP_DFT_CONTENT="""<?xml version="1.0" encoding="UTF-8"?>
<hot_replace>
</hot_replace>
"""

DISK_TYPE_MAP = {'Free':'空闲盘', 'Special':'专用热备盘', 'Global':'全局热备盘'}
TMP_RAID_INFO = '/tmp/.raid-info/by-dev'

# vg日志封装
def vg_log(event, msg):
	log_insert('VG', 'Auto', event, msg)

class md_attr:
	def __init__(self):
		self.name = ''		# raid1需要特殊处理
		self.dev = ''
		self.raid_level = ''
		self.raid_state = ''	# raid1需要根据disk_cnt与disk_total关系计算
		self.raid_strip = ''	# raid1需要特殊处理
		self.raid_rebuild = ''
		self.capacity = 0
		self.remain = 0		# 剩余空间
		self.max_single = 0	# 最大连续空间
		self.disk_cnt = 0	# 当前磁盘个数, 对应mdadm -D的'Total Devices'字段, raid1需要计算实际的disk_list
		self.disk_list = []	# 当前磁盘列表, raid1需要特殊处理
		self.raid_uuid = ''	# 供磁盘上下线检测对应RAID使用, raid1需要特殊处理
		self.disk_total = 0	# raid应该包含的磁盘个数, 对应mdadm -D的'Raid Devices'字段, raid1需要特殊处理

def __def_post(p):
	if len(p) == 0:
		return ""
	return p[0]

def __level_post(p):
	if len(p) == 0:
		return "None"
	level = p[0].lower().replace("raid", "")
	if level == "linear":
		level = "JBOD"
	return level

def __chunk_post(p):
	if len(p) == 0:
		return ""
	chunk = p[0].lower().replace("k", "")
	return chunk

def __state_post(p):
	if len(p) == 0:
		return "Unknown"
	state = p[0]
	if state.find("degraded") != -1 :
		if state.find("recovering") != -1:
			return "rebuild"
		return "degrade"
	elif state.find("FAILED") != -1:
		return "fail"
	elif state.find("resyncing") != -1:
		return "initial"
	else:
		return "normal"

def __name_post(p):
	return p[0].split(":")[0] if len(p) > 0 else 'Unknown'

def __disk_post(p):
	if len(p) == 0:
		return ();
	slots = []
	for disk in p:
		name = disk[1]
		slots.append(disk_dev2slot(name))
	return slots

def __find_attr(output, reg, post=__def_post):
	p = re.findall(reg, output)
	return post(p)

def __raid0_jobd_state(dspecs, dcnt):
	return 'normal' if dcnt == dspecs else 'fail'

def get_capacity(dev):
	sectors = fs_attr_read('/sys/block/' + basename(dev) + '/size')
	if sectors.isdigit():
		return int(sectors) * 512
	else:
		return 0

# 目前先调用外部程序, 以后考虑使用函数级调用的方式实现
# sys-manager udv --remain-capacity --vg vg_name
# 输出格式：
# {"vg":"/dev/md1","max_avaliable":212860928,"max_single":212860928}
def get_remain_capacity(raid_name):
	try:
		json_result = os.popen('sys-manager udv --remain-capacity --vg %s' % raid_name).readline()
		udv_result = json.loads(json_result)
		return str(udv_result['max_avaliable']),str(udv_result['max_single'])
	except:
		return 0,0

def raid_level(level):
	if level.lower() == 'jbod':
		level = 'linear'
	return level

def get_mdattr_by_mdadm(mddev):
	mdattr = md_attr()
	mdattr.dev = mddev
	cmd = 'mdadm -D %s 2>/dev/null' % mddev
	sts,output = commands.getstatusoutput(cmd)
	if sts != 0:
		return mdattr

	mdattr.name = __find_attr(output, "Name : (.*)", __name_post)
	mdattr.raid_level = __find_attr(output, "Raid Level : (.*)", __level_post)
	mdattr.raid_state = __find_attr(output, "State : (.*)", __state_post)
	mdattr.raid_strip = __find_attr(output, "Chunk Size : ([0-9]+[KMG])", __chunk_post)
	rebuild_per = __find_attr(output, "Rebuild Status : ([0-9]+)\%")
	resync_per = __find_attr(output, "Resync Status : ([0-9]+)\%")

	if rebuild_per:
		mdattr.raid_rebuild = rebuild_per
	elif resync_per:
		mdattr.raid_rebuild = resync_per
	else:
		mdattr.raid_rebuild = '0'

	mdattr.capacity = get_capacity(mdattr.dev)
	mdattr.remain,mdattr.max_single = get_remain_capacity(mdattr.name)
	mdattr.disk_list = __find_attr(output, "([0-9]+\s*){4}.*(/dev/.+)", __disk_post)
	mdattr.disk_cnt = len(mdattr.disk_list)
	mdattr.raid_uuid = __find_attr(output, "UUID : (.*)")
	mdattr.disk_total = int(__find_attr(output, "Raid Devices : ([0-9]+)"))

	return mdattr

# 不同RAID级别在磁盘完全掉线后会导致部分信息缺失需要记录在tmpfs供查询使用
def fill_mdattr_by_tmpfs(mdattr = md_attr()):
	if mdattr.dev == '':
		return mdattr

	f_lock = lock_file('%s/.lock_%s' % (TMP_RAID_INFO, basename(mdattr.dev)))
	_dir = '%s/%s' % (TMP_RAID_INFO, basename(mdattr.dev))

	# 以下是raid级别0,1,5,6,JBOD需要获取的信息
	if mdattr.name == 'Unknown' or mdattr.name == '':
		mdattr.name = fs_attr_read(_dir + '/name')
	if mdattr.raid_uuid == '':
		mdattr.raid_uuid = fs_attr_read(_dir + '/raid-uuid')
	
	if mdattr.raid_level == '6':
		if mdattr.raid_state == 'degrade' or mdattr.raid_state == 'rebuild':
			if mdattr.disk_cnt < mdattr.disk_total:
				mdattr.raid_state = 'degrade'
			else:
				mdattr.raid_state = 'rebuild'
		unlock_file(f_lock)
		return mdattr

	if mdattr.raid_level == '5':
		unlock_file(f_lock)
		return mdattr

	# 特殊处理: raid1,jbod没有strip属性
	if mdattr.raid_level == '1' or mdattr.raid_level == 'JBOD':
		mdattr.raid_strip = 'N/A'

	# raid 0,1,jobd的磁盘列表需要单独处理
	mdattr.disk_list = list_file('%s/disk-list' % _dir)
	mdattr.disk_cnt = len(mdattr.disk_list)

	# raid 0,jbod的状态在掉盘后需要手动判断
	if mdattr.raid_level == '0' or mdattr.raid_level == 'JBOD':
		mdattr.raid_state = __raid0_jobd_state(mdattr.disk_total, mdattr.disk_cnt)

	unlock_file(f_lock)
	return mdattr

def tmpfs_add_md(mddev):
	mdattr = get_mdattr_by_mdadm(mddev)
	if None == mdattr:
		unlock_file(f_lock)
		return

	_dir = '%s/%s' % (TMP_RAID_INFO, basename(mddev))
	if not os.path.exists(_dir):
		os.makedirs(_dir)
	f_lock = lock_file('%s/.lock_%s' % (TMP_RAID_INFO, basename(mddev)))
	
	fs_attr_write(_dir + '/name', mdattr.name)
	fs_attr_write(_dir + '/raid-uuid', mdattr.raid_uuid)

	if mdattr.raid_level != '5' and mdattr.raid_level != '6':
		_list_dir = '%s/disk-list' % _dir
		if not os.path.exists(_list_dir):
			os.makedirs(_list_dir)
		for x in mdattr.disk_list:
			fs_attr_write(_list_dir + os.sep + x, x)

	unlock_file(f_lock)

	# check vg state, notify to sysmon
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
	f_lock = lock_file('%s/.lock_%s' % (TMP_RAID_INFO, basename(mddev)))
	os.popen('rm -fr %s/%s' % (TMP_RAID_INFO, basename(mddev)))
	unlock_file(f_lock)

def tmpfs_remove_disk_from_md(mddev, slot):
	f_lock = lock_file('%s/.lock_%s' % (TMP_RAID_INFO, basename(mddev)))
	_file = '%s/%s/disk-list/%s' % (TMP_RAID_INFO, basename(mddev), slot)
	if os.path.isfile(_file):
		os.unlink(_file)
	unlock_file(f_lock)

def tmpfs_add_disk_to_md(mddev, slot):
	f_lock = lock_file('%s/.lock_%s' % (TMP_RAID_INFO, basename(mddev)))
	_dir = '%s/%s/disk-list' % (TMP_RAID_INFO, basename(mddev))
	fs_attr_write(_dir + os.sep + slot, slot)
	unlock_file(f_lock)

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
		if not (md in mds):
			return md
	return None

def get_disks_of_mddev(mddev):
	cmd = "ls /sys/block/%s/slaves" % basename(mddev)
	sts,disks = commands.getstatusoutput(cmd)
	if sts != 0:
		return []
	return ["/dev/" + disk for disk in disks.split()]

def get_md_by_name(raid_name):
	mds = md_list()
	for md in mds:
		if raid_name == fs_attr_read('/sys/block/' + md + '/md/array_name'):
			return md
	return ''

def get_mdattr_by_mddev(mddev):
	mdattr = get_mdattr_by_mdadm(mddev)
	return fill_mdattr_by_tmpfs(mdattr)

def get_mdattr_by_md(md=''):
	if (md == ''):
		return None

	return get_mdattr_by_mddev('/dev/' + md)

def get_mdattr_by_name(raid_name=''):
	if (raid_name == ''):
		return None

	md = get_md_by_name(raid_name)
	return get_mdattr_by_md(md)
	
def get_mdattr_all():
	mdattr_list = []
	mds = md_list()
	for md in mds:
		mdattr = get_mdattr_by_mddev('/dev/' + md)
		mdattr_list.append(mdattr)
	return mdattr_list

def md_create(raid_name, level, chunk, slots):
	ret,msg = __md_create(raid_name, level, chunk, slots)
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
	dev_list = disks_slot2dev(slots.split())
	if len(dev_list) == 0:
		return False, "没有磁盘"
	devs = " ".join(dev_list)

	# enable all disk bad sect redirection
	for dev in dev_list:
		disk_bad_sect_remap_enable(basename(dev))

	cmd = "2>&1 mdadm -CR %s -l %s -c %s -n %u %s --metadata=1.2 --homehost=%s -f" % (mddev, raid_level(level), chunk, len(dev_list), devs, raid_name)
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
		return False, "创建卷组失败"

	msg = ''
	try:
		# 强制重写分区表
		cmd = 'sys-manager udv --force-init-vg %s' % raid_name
		sts,out = commands.getstatusoutput(cmd)
		if sts != 0:
			time.sleep(1)
			sts,out = commands.getstatusoutput(cmd)
			if sts != 0:
				force = json.loads(out)
				msg = force['msg']
	except:
		msg = '初始化卷组未知错误'
		pass
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
		vg_log('Error', '删除卷组 %s 失败%s' % (raid_name, msg))
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
			return False, '卷组 %s 存在未删除的用户数据卷, 请先删除' % raid_name
	except:
		md_uuid = ''
	dev_list = get_disks_of_mddev(mddev)
	if not md_stop(mddev):
		return False,"停止%s失败, 设备正在使用中" % raid_name

	# 专用热备盘设置为空闲盘
	f_lock = lock_file(RAID_REBUILD_LOCK)
	if f_lock != None:
		for slot in get_specials_by_mduuid(md_uuid):
			disk_set_type(slot, 'Free')
		unlock_file(f_lock)

	cleanup_disks_mdinfo(dev_list)

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

def __get_xmlnode(node, name):
	return node.getElementsByTagName(name) if node else []

def __get_attrvalue(node, attrname):
	return node.getAttribute(attrname) if node else ''

def __set_attrvalue(node, attr, value):
	return node.setAttribute(attr, value)

def __remove_attr(node, attr):
	return node.removeAttribute(attr)

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
		if mdattr.name == raid_name:
			md_uuid = mdattr.raid_uuid
		else:
			return False, '卷组 %s 不存在, 请检查参数' % raid_name
	elif disk_type == 'Free':
		remove_hotrep_by_slot(slot)
		cleanup_disk_mdinfo(disk_slot2dev(slot))
		# 通知监控进程
		sysmon_event('disk', 'led_off', 'disks=%s' % slot, '设置槽位号为 %s 的磁盘为空闲盘' % slot)
		sysmon_event('disk', 'buzzer_off', slot, '')
		vg_log('Info', "设置磁盘 %s 为 空闲盘" % slot)
		return True, '设置槽位号为 %s 的磁盘为空闲盘成功' % slot
	elif disk_type != 'Global':
		return False, '参数不正确:请指定需要设置的磁盘类型'

	check_disk_hotrep_conf()

	try:
		doc = minidom.parse(DISK_HOTREP_CONF)
	except IOError,e:
		return False, '读取配置分区出错 %s' % e
	except xml.parsers.expat.ExpatError, e:
		return False, '磁盘配置文件格式出错 %s' % e
	except e:
		return False, '无法解析磁盘配置文件 %s' % e

	disk_serial = disk_slot2serial(slot)

	set_exist = False
	root = doc.documentElement
	for item in __get_xmlnode(root, 'disk'):
		# 更新已经存在的节点
		if disk_serial == __get_attrvalue(item, 'serial'):
			__set_attrvalue(item, 'type', disk_type)
			__set_attrvalue(item, 'md_uuid', md_uuid)
			__set_attrvalue(item, 'md_name', raid_name);
			set_exist = True
			break

	# 增加新节点
	if not set_exist:
		impl = minidom.getDOMImplementation()
		dom = impl.createDocument(None, 'disk', None)
		disk_node = dom.createElement('disk')
		__set_attrvalue(disk_node, 'serial', disk_serial)
		__set_attrvalue(disk_node, 'md_uuid', md_uuid)
		__set_attrvalue(disk_node, 'type', disk_type)
		__set_attrvalue(disk_node, 'md_name', raid_name);
		root.appendChild(disk_node)

	# 更新xml配置文件
	f = open(DISK_HOTREP_CONF, 'w')
	doc.writexml(f, encoding='utf-8')
	f.close()

	# 清除磁盘上的superblock信息
	cleanup_disk_mdinfo(disk_slot2dev(slot))

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
	try:
		doc = minidom.parse(DISK_HOTREP_CONF)
	except:
		return None
	return doc

# 获取指定RAID所有专用热备盘
def get_specials_by_mduuid(md_uuid=''):
	spec_list = []

	if md_uuid == '':
		return spec_list

	doc = hotrep_conf_load()
	if doc == None:
		return spec_list
	doc_root = doc.documentElement
	try:
		for item in __get_xmlnode(doc_root, 'disk'):
			if __get_attrvalue(item, 'md_uuid') == md_uuid and __get_attrvalue(item, 'type') == 'Special':
				spec_list.append(disk_serial2slot(__get_attrvalue(item, 'serial')))
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
	doc_root = doc.documentElement
	try:
		for item in __get_xmlnode(doc_root, 'disk'):
			tmp_info['serial'] = __get_attrvalue(item, 'serial')
			tmp_info['type'] = __get_attrvalue(item, 'type')
			
			slot = disk_serial2slot(tmp_info['serial'])
			if slot == None:
				doc_root.removeChild(item)
				update_conf = True
				continue

			# 专用热备盘
			if md_uuid == __get_attrvalue(item, 'md_uuid'):
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
		f = open(DISK_HOTREP_CONF, 'w')
		doc.writexml(f, encoding='utf-8')
		f.close()

	return disk_info

def remove_hotrep_by_serial(serial):
	update_conf = False
	doc = hotrep_conf_load()
	if doc == None:
		return False

	doc_root = doc.documentElement
	for item in __get_xmlnode(doc_root, 'disk'):
		if serial == __get_attrvalue(item, 'serial'):
			doc_root.removeChild(item)
			update_conf = True
			break

	if update_conf:
		f = open(DISK_HOTREP_CONF, 'w')
		doc.writexml(f, encoding='utf-8')
		f.close()
		return True

	return False

def remove_hotrep_by_slot(slot):
	disk_serial = disk_slot2serial(slot)
	if disk_serial != None:
		return remove_hotrep_by_serial(disk_serial)
	else:
		return False

RAID_REBUILD_LOCK = '/tmp/.raid_rebuild_lock'
def md_rebuild(mdattr):
	# 使用文件锁同步多个raid重建, 防止争抢全局热备盘和空闲盘
	f_lock = lock_file(RAID_REBUILD_LOCK)
	if None == f_lock:
		vg_log('Error', '系统异常: 文件 %s 加锁失败' % RAID_REBUILD_LOCK)
		return

	disk_type = 'Hot'
	disk = get_hotrep_by_mduud(mdattr.raid_uuid)
	if disk == {}:
		disk = get_free_disk()
		disk_type = 'Free'
	if disk == {}:
		vg_log('Error', '未找到热备盘和空闲盘重建卷组 %s' % mdattr.name)
		unlock_file(f_lock)
		return

	slot = disk_serial2slot(disk['serial'])
	diskdev = disk_slot2dev(slot)
	if add_disk_to_md(mdattr.dev, diskdev) == 0:
		vg_log('Info', '%s %s 加入卷组 %s 成功' % (disk['type'], slot, mdattr.name))
		if disk_type != 'Free':
			remove_hotrep_by_serial(disk['serial'])
			disk_update_by_slots(slot)
	else:
		vg_log('Error', '%s %s 加入卷组 %s 失败' % (disk['type'], slot, mdattr.name))
	unlock_file(f_lock)

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
	
	disk_update_by_slots(disk_dev2slot(dev))

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

# 从指定卷组删除掉盘的磁盘
def remove_disk_from_md(mddev, diskdev):
	cmd = 'mdadm --set-faulty %s %s 2>&1' % (mddev, basename(diskdev))
	ret,msg = commands.getstatusoutput(cmd)
	
	cmd = 'mdadm --remove %s %s 2>&1' % (mddev, basename(diskdev))
	ret,msg = commands.getstatusoutput(cmd)
	
	tmpfs_remove_disk_from_md(mddev, disk_dev2slot(diskdev))
	return ret

# 将磁盘加入指定卷组
def add_disk_to_md(mddev, diskdev):
	cmd = 'mdadm --add %s %s 2>&1' % (mddev, diskdev)
	ret,msg = commands.getstatusoutput(cmd)
	
	tmpfs_add_disk_to_md(mddev, disk_dev2slot(diskdev))
	return ret

# 使用磁盘dev节点名称查找所在的卷组信息
def get_mdattr_by_disk(dev):
	mdattr = None
	try:
		f = open('/proc/mdstat', 'r')
		for x in f.readlines():
			mddev = re.match('^md\d*', x)
			if mddev is None:
				continue
			if basename(dev) in re.findall('sd\w+', x):
				mdattr = get_mdattr_by_mddev('/dev/%s' % mddev.group())
				break
		f.close()
	except:
		pass
	return mdattr

# 使用mduuid查找所在卷组信息
def get_mdattr_by_mduuid(mduuid):
	for mdattr in get_mdattr_all():
		if mduuid == mdattr.raid_uuid:
			return mdattr
	return None

# -----------------------------------------------------------------------------
if __name__ == "__main__":
	import sys

	print get_mdattr_all()
	print get_mdattr_by_name("abc")

	sys.exit(0)
