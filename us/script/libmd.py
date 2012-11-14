#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands, re, os
from libdisk import *
from xml.dom import minidom
import xml

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

DISK_HOTREP_CONF='/opt/disk/disk-hotreplace.xml'
DISK_HOTREP_DFT_CONTENT="""<?xml version="1.0" encoding="UTF-8"?>
<hot_replace>
</hot_replace>
"""

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
		return "degraded"
	elif state.find("FAILED") != -1:
		return "fail"
	elif state.find("resyncing") != -1:
		return "initial"
	else:
		return "normal"

def __name_post(p):
	if len(p) == 0:
		return "Unknown"
	name=p[0];
	return name.split(":")[0]

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

def __md_fill_attr(str):
	attr = {}
	attr["name"] = __find_attr(str, "Name : (.*)", __name_post)
	attr["dev"] = __find_attr(str, "^(.*):")
	attr["raid_level"] = __find_attr(str, "Raid Level : (.*)", __level_post)
	attr["raid_state"] = __find_attr(str, "State : (.*)", __state_post)
	attr["raid_strip"] = __find_attr(str, "Chunk Size : ([0-9]+[KMG])",
			__chunk_post)
	rebuild_per = __find_attr(str, "Rebuild Status : ([0-9]+)\%")
	resync_per = __find_attr(str, "Resync Status : ([0-9]+)\%")
	if rebuild_per:
		attr["raid_rebuild"] = rebuild_per
	elif resync_per:
		attr["raid_rebuild"] = resync_per
	else:
		attr["raid_rebuild"] = '0'

	attr["capacity"] = int(__get_sys_attr(attr["dev"], "size")) * 512
	attr["remain"] = __get_remain_capacity(attr["name"])
	attr["disk_cnt"] = int(__find_attr(str, "Total Devices : ([0-9]+)"))
	attr["disk_list"] = __find_attr(str, "([0-9]+\s*){4}.*(/dev/.+)",
			__disk_post)

	# 增加uuid供磁盘上下线使用
	attr["raid_uuid"] = __find_attr(str, "UUID : (.*)")
	attr["disk_working"] = int(__find_attr(str, "Working Devices : ([0-9]+)"))

	return attr

def mddev_get_attr(mddev):
	md_attr = {}
	cmd = "mdadm -D %s" % mddev
	sts,output = commands.getstatusoutput(cmd)
	if (sts != 0) :
		return None
	md_attr = __md_fill_attr(output)
	return md_attr

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

def md_create(mdname, level, chunk, slots):
	#create raid
	mddev = md_find_free_mddev()
	if mddev == None:
		return False,"没有空闲的RAID槽位"
	devs,failed = disks_from_slot(slots)
	if len(devs) == 0:
		return False, "没有磁盘"
	dev_list = " ".join(devs)
	cmd = " >/dev/null 2>&1 mdadm -CR %s -l %s -c %s -n %u %s --metadata=1.2 --homehost=%s -f" % (mddev, level, chunk, len(devs), dev_list, mdname)
	if level in ('3', '4', '5', '6', '10', '50', '60'):
		cmd += " --bitmap=internal"
	sts,out = commands.getstatusoutput(cmd)
	disk_slot_update(slots)
	if sts != 0 :
		return False, "创建卷组失败"
	return True, "创建卷组成功"

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
	mddev = md_get_mddev(mdname)
	if (mddev == None):
		return False, "卷组 %s 不存在!" % mdname
	if __md_used(mdname):
		return False, '卷组 %s 存在未删除的用户数据卷，请先删除！' % mdname
	disks = mddev_get_disks(mddev)
	sts,msg = md_stop(mddev)
	if sts != 0:
		return False,"停止%s失败!%s" % (mdname, msg)
	__md_remove_devnode(mddev)
	res = set_disks_free(disks)
	if res != "":
		return False,"清除磁盘信息失败，请手动清除"
	return True,"删除卷组成功"

def md_info_mddevs(mddevs=None):
	if (mddevs == None):
		mddevs = md_list_mddevs()
	md_no = len(mddevs)
	md_attrs = [];
	for mddev in mddevs:
		attr = mddev_get_attr(mddev)
		if (attr):
			md_attrs.append(attr)
	return {"total": md_no, "rows": md_attrs}

def md_info(mdname=None):
	if (mdname == None):
		mddevs = None;
	else:
		mddevs = [md_get_mddev(mdname)];
	return md_info_mddevs(mddevs);

# -----------------------------------------------------------------------------
# 供磁盘自动重建使用
# -----------------------------------------------------------------------------

def disk_serial2name(serial):
	return

def disk_serial2slot(serial):
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

# 设置磁盘管理类型：
#	* global   - 全局热备盘
#	* special  -  专用热备盘
def disk_set_type(slot, disk_type, mdname=''):

	disk_type_map = {'Free':'空闲盘', 'Special':'专用热备盘', 'Global':'全局热备盘'}

	if slot == '':
		return False, '请输入磁盘槽位号!'

	state = disk_get_state(slot)
	if state == 'N/A':
		return False, '无法获取槽位号为 %s 的磁盘状态!' % slot
	elif state == 'RAID':
		return False, '槽位号为 %s 的磁盘是RAID盘，无法设置热备盘!' % slot
	elif state == disk_type:
		return False, '槽位号为 %s 磁盘已经是%s，无需设置!' % (slot, disk_type_map[state])

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
			set_exist = True
			# TODO 通知us_d进程
			break

	# 增加新节点
	if not set_exist:
		impl = minidom.getDOMImplementation()
		dom = impl.createDocument(None, 'disk', None)
		disk_node = dom.createElement('disk')
		__set_attrvalue(disk_node, 'serial', disk_serial)
		__set_attrvalue(disk_node, 'md_uuid', md_uuid)
		__set_attrvalue(disk_node, 'type', disk_type)
		root.appendChild(disk_node)

	# 更新xml配置文件
	f = open(DISK_HOTREP_CONF, 'w')
	doc.writexml(f, encoding='utf-8')
	f.close()

	# 通知disk监控进程
	disk_slot_update(slot)
	return True, '设置槽位号为 %s 的磁盘为热备盘成功！' % slot

# 获取热备盘
# 优先返回专用热备盘，如果没有则返回全局热备盘，如果没有则返回None
def disk_get_hotrep_by_md(name):

	md_uuid = ''
	try:
		doc = minidom.parse(DISK_HOTREP_CONF)
	except IOError,e:
		return False, '读取配置分区出错！%s' % e
	except xml.parsers.expat.ExpatError, e:
		return False, '磁盘配置文件格式出错！%s' % e
	except e:
		return False, '无法解析磁盘配置文件！%s' % e

	for mdinfo in md_info(name)['rows']:
		if mdinfo['name'] == name:
			md_uuid = mdinfo['raid_uuid']
	if md_uuid == '':
		return False, '卷组 %s 不存在，请检查参数!' % name

	root = doc.documentElement
	for item in __get_xmlnode(root, 'disk'):
		if md_uuid == __get_attrvalue(item, 'md_uuid'):
			return True, __get_attrvalue(item, 'serial')
	return False, '未配置热备盘!'

# 设置热备盘被使用
def disk_clean_hotrep(slot):
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

if __name__ == "__main__":
	import sys

	ret,msg = disk_set_type('0:6', 'Global')
	print msg
	sys.exit(0)

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
