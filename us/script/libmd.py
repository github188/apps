#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands, re, os
from libdisk import *
from xml.dom import minidom
from libsysmon import sysmon_event
import xml

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

DISK_HOTREP_CONF='/opt/jw-conf/disk/hotreplace.xml'
DISK_HOTREP_DFT_CONTENT="""<?xml version="1.0" encoding="UTF-8"?>
<hot_replace>
</hot_replace>
"""
DISK_TYPE_MAP = {'Free':'空闲盘', 'Special':'专用热备盘', 'Global':'全局热备盘'}


def disk_list_str(dlist=[]):
	return ','.join([str(x) for x in dlist])

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
		slots.append(disk_slot(name))
	return slots

def __find_attr(output, reg, post=__def_post):
	p = re.findall(reg, output)
	return post(p)

def __attr_read(path, attr):
	content = ''
	try:
		attr_path = path + os.sep + attr
		f = open(attr_path)
		content = f.readline().strip()
		f.close()
	except:
		pass
	return content

def __get_sys_attr(dev, attr):
	if dev.find('/dev/md') >= 0:
		dev_name = dev.split('/dev/')[-1]
	else:
		dev_name = dev
	sys_path = '/sys/block/' + dev_name
	return __attr_read(sys_path, attr)

# 目前先调用外部程序，以后考虑使用函数级调用的方式实现
# sys-manager udv --remain-capacity --vg /dev/md1
# 输出格式：
# {"vg":"/dev/md1","max_avaliable":212860928,"max_single":212860928}
def __get_remain_capacity(md_name):
	try:
		json_result = os.popen('sys-manager udv --remain-capacity --vg %s' % md_name).readline()
		udv_result = json.loads(json_result)
		return udv_result['max_avaliable']
	except:
		return 0

class raid_attr:
	def __init__(self):
		self.name = ''		# raid1需要特殊处理
		self.dev = ''
		self.raid_level = ''
		self.raid_state = ''	# raid1需要根据disk_cnt与disk_specs关系计算
		self.raid_strip = ''	# raid1需要特殊处理
		self.raid_rebuild = ''
		self.capacity = 0
		self.remain = 0
		self.disk_cnt = 0	# 当前磁盘个数, raid1需要计算实际的disk_list
		self.disk_list = []	# 当前磁盘列表, raid1需要特殊处理
		self.raid_uuid = ''	# 供磁盘上下线检测对应RAID使用, raid1需要特殊处理
		#self.disk_working = 0	# 考虑使用disk_cnt替代
		self.disk_specs = 0	# raid应该包含的磁盘个数，对应mdadm -D的'Raid Devices'字段, raid1需要特殊处理

def __listdir_files(_dir):
	if not os.path.isdir(_dir):
		return []
	_list = []
	for x in os.listdir(_dir):
		if not os.path.isfile('%s/%s' % (_dir, x)):
			continue
		_list.append(x)
	return _list

def __raid0_jobd_state(dspecs, dcnt):
	return 'normal' if dcnt == dspecs else 'fail'

def __raid1_state(dspecs, dcnt):
	if dcnt == 0:
		return 'fail'
	elif dcnt < dspecs:
		return 'degrade'
	return 'normal'


# 不同RAID级别在磁盘完全掉线后会导致部分信息缺失需要记录在tmpfs供查询使用
def __md_fill_tmpfs_attr(attr = raid_attr()):
	_dir = '%s/%s' % (TMP_RAID_INFO, dev_trim(attr.dev))

	# 以下是raid级别0,1,5,6,JBOD需要获取的信息
	if attr.name == 'Unknown' or attr.name == '':
		attr.name = AttrRead(_dir, 'name')
	if attr.raid_uuid == '':
		attr.raid_uuid = AttrRead(_dir, 'raid-uuid')
	
	if attr.raid_level == '5' or attr.raid_level == '6':
		return attr.__dict__

	# 特殊处理: raid1,jbod没有strip属性
	if attr.raid_level == '1' or attr.raid_level == 'JBOD':
		attr.raid_strip = 'N/A'

	# raid 0,1,jobd的磁盘列表需要单独处理
	attr.disk_list = __listdir_files('%s/disk-list' % _dir)
	attr.disk_cnt = len(attr.disk_list)

	# raid 0,1,jbod的状态在掉盘后需要手动判断
	if attr.raid_level == '0' or attr.raid_level == 'JBOD':
		attr.raid_state = __raid0_jobd_state(attr.disk_specs, attr.disk_cnt)
	#elif attr.raid_level == '1':
	#	attr.raid_state = __raid1_state(attr.disk_specs, attr.disk_cnt)

	return attr.__dict__

def __md_fill_mdadm_attr(mddev):
	cmd = 'mdadm -D %s 2>/dev/null' % mddev
	sts,output = commands.getstatusoutput(cmd)

	if sts != 0:
		return None

	attr = raid_attr()
	attr.name = __find_attr(output, "Name : (.*)", __name_post)
	attr.dev = __find_attr(output, "^(.*):")
	attr.raid_level = __find_attr(output, "Raid Level : (.*)", __level_post)
	attr.raid_state = __find_attr(output, "State : (.*)", __state_post)
	attr.raid_strip = __find_attr(output, "Chunk Size : ([0-9]+[KMG])", __chunk_post)
	rebuild_per = __find_attr(output, "Rebuild Status : ([0-9]+)\%")
	resync_per = __find_attr(output, "Resync Status : ([0-9]+)\%")

	if rebuild_per:
		attr.raid_rebuild = rebuild_per
	elif resync_per:
		attr.raid_rebuild = resync_per
	else:
		attr.raid_rebuild = '0'

	attr.capacity = int(__get_sys_attr(attr.dev, "size")) * 512
	attr.remain = __get_remain_capacity(attr.name)
	attr.disk_list = __find_attr(output, "([0-9]+\s*){4}.*(/dev/.+)", __disk_post)
	attr.disk_cnt = len(attr.disk_list)
	attr.raid_uuid = __find_attr(output, "UUID : (.*)")
	attr.disk_specs = int(__find_attr(output, "Raid Devices : ([0-9]+)"))

	return attr


def mddev_get_attr(mddev):
	attr = __md_fill_mdadm_attr(mddev)
	if None == attr:
		return None
	return __md_fill_tmpfs_attr(attr)

def tmpfs_remove_disk_from_md(mdinfo, diskinfo):
	_file = '%s/%s/disk-list/%s' % (TMP_RAID_INFO, dev_trim(mdinfo['dev']), diskinfo.slot)
	return os.unlink(_file) if os.path.isfile(_file) else False

def tmpfs_add_disk_to_md(mdinfo, diskinfo):
	_dir = '%s/%s/disk-list' % (TMP_RAID_INFO, dev_trim(mdinfo['dev']))
	return AttrWrite(_dir, diskinfo.slot, diskinfo.slot)

# 作用：区分创建RAID时获取md信息和重组RAID时获取信息的问题
# 产生原因：启动时重组RAID后，如果盘较多，/dev/md[x]节点出现会滞后，
#           需要在handle-md脚本中通过add事件响应；对于创建RAID操作，
#           可以直接更新RAID信息

def __create_lock():
	_dir = os.path.dirname(TMP_RAID_LOCK)
	if not os.path.exists(_dir):
		os.makedirs(_dir)
	try:
		f = open(TMP_RAID_LOCK, 'w')
		f.write('')
		f.close()
	except:
		return False
	return True

def __create_unlock():
	try:
		os.remove(TMP_RAID_LOCK)
	except:
		return False
	return True

# 检查是否被创建函数加锁
def __try_create_lock():
	return os.path.isfile(TMP_RAID_LOCK)

# mddev - /dev/md<x>
def tmpfs_add_md_info(mddev):
	if __try_create_lock():
		return

	attr = __md_fill_mdadm_attr(mddev)
	if None == attr:
		return
	_dir = '%s/%s' % (TMP_RAID_INFO, dev_trim(mddev))
	if not os.path.exists(_dir):
		os.makedirs(_dir)
	AttrWrite(_dir, 'name', attr.name)
	AttrWrite(_dir, 'raid-uuid', attr.raid_uuid)

	# check vg state, notify to sysmon
	if attr.raid_state == 'degrade':
		sysmon_event('vg', 'degrade', 'disks=%s' % disk_list_str(attr.disk_list), '卷组 %s 降级' % attr.name)
	elif attr.raid_state == 'fail':
		sysmon_event('vg', 'fail', 'disks=%s' % disk_list_str(attr.disk_list), '卷组 %s 失效' % attr.name)
	elif attr.raid_state == 'normal':
		sysmon_event('vg', 'good', 'disks=%s' % disk_list_str(attr.disk_list), '卷组 %s 状态正常' % attr.name)
	elif attr.raid_state == 'rebuild':
		sysmon_event('vg', 'rebuild', 'disks=%s' % disk_list_str(attr.disk_list), '卷组 %s 状态正常' % attr.name)

	if attr.raid_level == '5' or attr.raid_level == '6':
		return

	_list_dir = '%s/disk-list' % _dir
	if not os.path.exists(_list_dir):
		os.makedirs(_list_dir)
	for x in attr.disk_list:
		AttrWrite(_list_dir, x, x)
	return

# mddev - /dev/md<x>
def tmpfs_remove_md_info(mddev):
	os.popen('rm -fr %s/%s' % (TMP_RAID_INFO, dev_trim(mddev)))


def md_list_mddevs():
	#return list_files("/dev", "md[0-9]+")
	# 解决正则表达式匹配md1p1设备的问题
	dev_list = []
	try:
		for dev in os.listdir('/dev'):
			if (dev.find('md') == 0) and (len(dev.split('p')) == 1) and (len(dev)>2):
				dev_list.append('/dev/' + dev)
	except:
		pass
	finally:
		return dev_list

def md_find_free_mddev():
	mddevs = md_list_mddevs()
	for i in xrange(1, 255):
		md = "/dev/md%u" % i
		if not (md in mddevs):
			return md
	return None

def mddev_get_disks(mddev):
	reg = re.compile(r"(sd[a-z]+)\[[0-9]+\]")
	cmd = "cat /proc/mdstat |grep %s 2>/dev/null" % (os.path.basename(mddev))
	sts,out = commands.getstatusoutput(cmd)
	if sts != 0:
		return []
	disks = reg.findall(out)
	rdisks = ["/dev/" + x for x in disks]

	return rdisks

def md_get_disks(mdname):
	mddev = get_mddev(mdname)
	if mddev == None:
		return []
	return mddev_get_disks(mddev)

def md_stop(mddev):
	cmd = "mdadm -S %s 2>&1" % mddev
	sts, out = commands.getstatusoutput(cmd)
	if out.find('mdadm: stopped') < 0:
		return -1,'设备正在被占用!'
	cmd = "rm -f %s >/dev/null 2>&1" % mddev
	sts,out = commands.getstatusoutput(cmd)
	if sts != 0:
		return -1,'无法删除设备节点!'
	return sts,''

def __raid_level(_level):
	return 'linear' if _level.lower() == 'jbod' else _level

def md_create(mdname, level, chunk, slots):
	ret,msg = __md_create(mdname, level, chunk, slots)
	__create_unlock()
	if ret:
		LogInsert('VG', 'Auto', 'Info', '使用磁盘 %s 创建RAID级别为 %s 的卷组 %s 成功！卷组初始化开始！' % (slots, level, mdname))
	else:
		LogInsert('VG', 'Auto', 'Error', '使用磁盘 %s 创建RAID级别为 %s 的卷组 %s 失败！%s' % (slots, level, mdname, msg))
	return ret,msg

def __md_create(mdname, level, chunk, slots):
	__create_lock()
	#create raid
	mddev = md_find_free_mddev()
	if mddev == None:
		return False,"没有空闲的RAID槽位"
	devs,failed = disks_from_slot(slots)
	if len(devs) == 0:
		return False, "没有磁盘"
	dev_list = " ".join(devs)

	# enable all disk bad sect redirection
	for d in dev_list.split():
		disk_bad_sect_redirection(d)

	cmd = " >/dev/null 2>&1 mdadm -CR %s -l %s -c %s -n %u %s --metadata=1.2 --homehost=%s -f" % (mddev, __raid_level(level), chunk, len(devs), dev_list, mdname)
	if level in ('3', '4', '5', '6', '10', '50', '60'):
		cmd += " --bitmap=internal"
	sts,out = commands.getstatusoutput(cmd)
	# 更新热备盘配置
	for slot in slots.split():
		disk_state = disk_get_state(slot)
		if disk_state == 'Special' or disk_state == 'Global':
			disk_clean_hotrep(slot)
	disk_slot_update(slots)
	if sts != 0 :
		# try to remove mddev
		os.popen('mdadm -S %s 2>&1 >/dev/null' % mddev)
		os.popen('rm -f %s 2>&1 >/dev/null' % mddev)
		return False, "创建卷组失败"

	msg = ''
	try:
		# 强制重写分区表
		cmd = 'sys-manager udv --force-init-vg %s' % mdname
		sts,out = commands.getstatusoutput(cmd)
		if sts != 0:
			force = json.loads(out)
			msg = force['msg']
	except:
		msg = '初始化卷组未知错误!'
		pass
	__create_unlock()
	tmpfs_add_md_info(mddev)
	return True, '创建卷组成功!%s' % msg

def __md_remove_devnode(mddev):
	try:
		os.remove(mddev)
	except:
		pass
	return

def __md_used(mdname):
	try:
		d = json.loads(commands.getoutput('sys-manager udv --remain-capacity --vg %s' % mdname))
		if d['max_avaliable'] == d['max_single']:
			return False
	except:
		pass
	return True

def md_del(mdname):
	ret,msg = __md_del(mdname)
	if ret:
		LogInsert('VG', 'Auto', 'Info', '删除卷组 %s 成功！' % mdname)
	else:
		LogInsert('VG', 'Auto', 'Error', '删除卷组 %s 失败！%s' % (mdname, msg))
	return ret,msg

def __md_del(mdname):
	mddev = md_get_mddev(mdname)
	if (mddev == None):
		return False, "卷组 %s 不存在!" % mdname
	if __md_used(mdname):
		return False, '卷组 %s 存在未删除的用户数据卷，请先删除！' % mdname

	try:
		mdinfo = md_info(mdname)['rows'][0]
		md_uuid = mdinfo['raid_uuid']
	except:
		md_uuid = ''
	disks = mddev_get_disks(mddev)
	sts,msg = md_stop(mddev)
	if sts != 0:
		return False,"停止%s失败!%s" % (mdname, msg)
	# 删除设备节点
	__md_remove_devnode(mddev)

	tmpfs_remove_md_info(mddev)

	# 专用热备盘设置为空闲盘
	for slot in md_get_special(md_uuid):
		disk_set_type(slot, 'Free')
	res = set_disks_free(disks)
	if res != "":
		return False,"清除磁盘信息失败，请手动清除"

	sysmon_event('vg', 'remove', 'disks=%s' % _disk_slot_list_str(disks), '卷组 %s 删除成功!' % mdinfo['name'])
	return True,"删除卷组成功"

def md_info_mddevs(mddevs=None):
	if (mddevs == None):
		mddevs = md_list_mddevs()
	md_attrs = [];
	for mddev in mddevs:
		attr = mddev_get_attr(mddev)
		if (attr):
			md_attrs.append(attr)
	return {"total": len(md_attrs), "rows": md_attrs}

def md_info(mdname=None):
	if (mdname == None):
		mddevs = None;
	else:
		mddevs = [md_get_mddev(mdname)];
	return md_info_mddevs(mddevs);

def md_restore():
	for mddev in md_list_mddevs():
		tmpfs_add_md_info(mddev)
	return

# -----------------------------------------------------------------------------
# 供磁盘自动重建使用
# -----------------------------------------------------------------------------

def disk_serial2slot(serial):
	try:
		cmd = 'sys-manager disk --list'
		disk_list = json.loads(commands.getoutput(cmd))
		for disk in disk_list['rows']:
			if disk['serial'] == serial:
				return disk['slot']
	except:
		pass
	return None

def disk_serial2name(serial):
	return disk_name(disk_serial2slot(serial))

	return

def disk_slot2serial(slot):
	_disk_serial = None
	try:
		cmd = 'sys-manager disk --list --slot-id %s' % slot
		_disk_info = json.loads(commands.getoutput(cmd))
		_disk_serial = _disk_info['serial']
	except:
		pass
	return _disk_serial

def disk_name2serial(name):
	return

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

# 检查磁盘热备盘配置，如果不存在就创建默认配置
def __check_disk_hotrep_conf():
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

def _rebuild_md(mdinfo, disk_slot, disk_type):
	name = disk_name(disk_slot)
	ret,msg = commands.getstatusoutput('mdadm --add %s %s 2>&1' % (mdinfo['dev'], name))
	if ret == 0:
		_event = 'Info'
		_content = '使用槽位号为 %s 的%s加入卷组 %s 重建操作成功!' % (disk_slot, disk_type, mdinfo['name'])
		disk_clean_hotrep(disk_slot)
		disk_slot_update(disk_slot)
	else:
		_event = 'Error'
		_content = '使用槽位号为 %s 的%s加入卷组 %s 重建操作失败!' % (disk_slot, disk_type, mdinfo['name'])
	LogInsert('VG', 'Auto', _event, _content)
	return

# 手动重建
def _manually_rebuild(slot, disk_type, mdname):
	# check special first
	if 'Special' == disk_type:
		if '' == mdname:
			return
		_tmp = md_info(mdname)['rows'];
		if len(_tmp) <= 0:
			return
		mdinfo = _tmp[0]
		if mdinfo['name'] != mdname:
			return
		if mdinfo['raid_state'] == 'degrade':
			_rebuild_md(mdinfo, slot, '专用热备盘')
		return
	# for global spare
	for mdinfo in md_info()['rows']:
		if mdinfo['raid_state'] != 'degrade':
			continue
		_rebuild_md(mdinfo, slot, '全局热备盘')
		break
	return

# 设置磁盘管理类型：
#	* Global   - 全局热备盘
#	* Special  - 专用热备盘
#       * Free     - 空闲盘
def disk_set_type(slot, disk_type, mdname=''):

	if slot == '':
		return False, '请输入磁盘槽位号!'

	state = disk_get_state(slot)
	if state == 'N/A':
		return False, '无法获取槽位号为 %s 的磁盘状态!' % slot
	elif state == 'RAID':
		return False, '槽位号为 %s 的磁盘是RAID盘，无法设置%s!' % (slot, DISK_TYPE_MAP[disk_type])
	elif state == disk_type:
		return True, '槽位号为 %s 磁盘已经是%s，无需设置!' % (slot, DISK_TYPE_MAP[state])

	md_uuid = ''
	if disk_type == 'Special':
		if mdname == '':
			return False, '参数不正确,设置专用热备盘必须指定卷组名称!'
		for mdinfo in md_info(mdname)['rows']:
			if mdinfo['name'] == mdname:
				md_uuid = mdinfo["raid_uuid"]
		if md_uuid == '':
			return False, '卷组 %s 不存在，请检查参数!' % mdname
	elif disk_type == 'Free':
		disk_clean_hotrep(slot)
		set_disk_free(disk_name(slot))
		disk_slot_update(slot)
		return True, '设置槽位号为 %s 的磁盘为空闲盘成功!' % slot
	elif disk_type != 'Global':
		return False, '参数不正确:请指定需要设置的磁盘类型'

	__check_disk_hotrep_conf()

	try:
		doc = minidom.parse(DISK_HOTREP_CONF)
	except IOError,e:
		return False, '读取配置分区出错！%s' % e
	except xml.parsers.expat.ExpatError, e:
		return False, '磁盘配置文件格式出错！%s' % e
	except e:
		return False, '无法解析磁盘配置文件！%s' % e

	disk_serial = disk_slot2serial(slot)

	set_exist = False
	root = doc.documentElement
	for item in __get_xmlnode(root, 'disk'):
		# 更新已经存在的节点
		if disk_serial == __get_attrvalue(item, 'serial'):
			__set_attrvalue(item, 'type', disk_type)
			__set_attrvalue(item, 'md_uuid', md_uuid)
			__set_attrvalue(item, 'md_name', mdname);
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
		__set_attrvalue(disk_node, 'md_name', mdname);
		root.appendChild(disk_node)

	# 更新xml配置文件
	f = open(DISK_HOTREP_CONF, 'w')
	doc.writexml(f, encoding='utf-8')
	f.close()

	# 清除磁盘上的superblock信息
	set_disk_free(disk_name(slot))

	# 通知disk监控进程
	disk_slot_update(slot)

	_content = '设置槽位号为 %s 的磁盘为热备盘成功！' % slot
	LogInsert('VG', 'Auto', 'Info', _content)

	# 通知监控进程
	sysmon_event('disk', 'spare', 'disks=%s' % slot, '设置槽位号为 %s 的磁盘为热备盘' % slot)

	# 尝试手动重建
	_manually_rebuild(slot, disk_type, mdname)

	return True, _content

def __xml_load(fname):
	__check_disk_hotrep_conf()
	try:
		doc = minidom.parse(fname)
	except:
		return None
	return doc.documentElement

# 获取指定RAID所有专用热备盘
def md_get_special(md_uuid=''):
	spec_list = []

	if md_uuid == '':
		return spec_list

	doc_root = __xml_load(DISK_HOTREP_CONF)
	try:
		for item in __get_xmlnode(doc_root, 'disk'):
			if __get_attrvalue(item, 'md_uuid') == md_uuid and __get_attrvalue(item, 'type') == 'Special':
				spec_list.append(disk_serial2slot(__get_attrvalue(item, 'serial')))
	except:
		pass
	return spec_list

# 获取热备盘
# 优先返回专用热备盘，如果没有则返回全局热备盘，如果没有则返回None
def md_get_hotrep(md_uuid=''):
	disk_info = {}
	tmp_info = {}
	doc_root = __xml_load(DISK_HOTREP_CONF)
	try:
		for item in __get_xmlnode(doc_root, 'disk'):
			tmp_info['serial'] = __get_attrvalue(item, 'serial')
			tmp_info['type'] = __get_attrvalue(item, 'type')

			# 专用热备盘
			if md_uuid == __get_attrvalue(item, 'md_uuid'):
				disk_info = tmp_info
				disk_info['type'] = '专用热备盘'
				break
			# 全局热备盘
			if tmp_info['type'] == 'Global':
				disk_info = tmp_info
	except:
		pass
	return disk_info

# 设置热备盘被使用
def disk_clean_hotrep(slot):
	__check_disk_hotrep_conf()
	try:
		doc = minidom.parse(DISK_HOTREP_CONF)
	except IOError,e:
		return False, '读取配置分区出错！%s' % e
	except xml.parsers.expat.ExpatError, e:
		return False, '磁盘配置文件格式出错！%s' % e
	except e:
		return False, '无法解析磁盘配置文件！%s' % e

	disk_serial = disk_slot2serial(slot)
	is_set = False
	root = doc.documentElement
	for item in __get_xmlnode(root, 'disk'):
		if disk_serial == __get_attrvalue(item, 'serial'):
			root.removeChild(item)
			is_set = True

	if is_set:
		f = open(DISK_HOTREP_CONF, 'w')
		doc.writexml(f, encoding='utf-8')
		f.close()
		return True, '移除磁盘 %s 的热备盘配置成功!' % slot

	return False, '移除磁盘 %s 的热备盘失败，配置不存在!' % slot

# -----------------------------------------------------------------------------

def _disk_slot_list_str(dlist=[]):
	return ','.join([disk_slot(x) for x in dlist])

if __name__ == "__main__":
	import sys
	sys.exit(0)
	print md_get_hotrep('8884de17:62750eb4:213d13ef:3e7c8dff')
	sys.exit(0)

	ret,msg = disk_set_type('0:11', 'Special', 'VG_4a04')
	print msg
	sys.exit(0)

	print 'lock: ', __create_lock()
	print 'try lock: ', __try_create_lock()
	print 'unlock: ', __create_unlock()
	sys.exit(0)

	attr = __md_fill_mdadm_attr('/dev/md1')
	print disk_list_str(attr.disk_list)
	disks = mddev_get_disks('/dev/md1')
	print _disk_slot_list_str(disks)

	mdinfo =  mddev_get_attr('/dev/md1')
	print disk_list_str(mdinfo['disk_list'])
	#sysmon_event('vg', 'remove', 'disks=%s' % _disk_slot_list_str(disks), '卷组 删除成功!')
	#sysmon_event('vg', 'degrade', 'disks=%s' % disk_list_str(attr.disk_list), '卷组 %s 降级' % attr.name)
	#sysmon_event('vg', 'fail', 'disks=%s' % disk_list_str(attr.disk_list), '卷组 %s 失效' % attr.name)
	sysmon_event('vg', 'good', 'disks=%s' % disk_list_str(attr.disk_list), '卷组 %s 状态正常' % attr.name)
	#sysmon_event('vg', 'rebuild', 'disks=%s' % disk_list_str(attr.disk_list), '卷组 %s 状态正常' % attr.name)
	sys.exit(0)

	md_restore()
	sys.exit(0)

	print md_info('slash')
	sys.exit(0)

	x = mddev_get_attr('/dev/md1')
	print x
	sys.exit(0)

	print '------', md_get_hotrep('f11ee90f:548a70c7:bf5b57cf:91230c43')
	sys.exit(0)
	mdinfo = md_info('abc123')['rows'][0]
	print mdinfo['raid_uuid']
	sys.exit(0)

	for slot in md_get_special('f11ee90f:548a70c7:bf5b57cf:91230c43'):
		print 'slot = ', slot
		disk_set_type(slot, 'Free')
	sys.exit(0)
	print disk_serial2name('S1D50WED')
	print disk_serial2slot('S1D50WED')
	ret,msg = disk_set_type('0:6', 'Global')
	print msg

	ret,msg = disk_set_type('0:6', 'Special', 'RD2012117135019')
	print msg

	ret,msg = disk_get_hotrep_by_md('RD2012117135019')
	print msg

	ret,msg = disk_set_hotrep_used('0:6')
	print msg


	#test
	if len(sys.argv) >= 2:
		md_name = sys.argv[1]
	else:
		md_name = "debianx"

	print "Test none:"
	print md_info(None)
	print md_info("ddd")
	print md_info(md_name)
