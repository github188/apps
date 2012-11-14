#!/usr/bin/env python
# -*- coding: utf-8 -*-

import commands
from libcommon import *

def disk_name(slot):
	cmd = "us_cmd disk name " + slot + " 2>/dev/null"
	out = commands.getoutput(cmd).strip()
	if (out.find("/dev/sd") == -1):
		return None
	return out

def disk_slot(name):
	cmd = "us_cmd disk slot " + name + " 2>/dev/null"
	out = commands.getoutput(cmd)
	if (out.find(":") == -1):
		return None
	return out

def disk_name_update(names):
	#TODO: update specified disks
	#We update all so far
	cmd = "us_cmd disk update"
	commands.getoutput(cmd)

def disk_slot_update(slots):
	try:
		for slot in slots.split():
			cmd = 'us_cmd disk update %s' % slot
			commands.getoutput(cmd)
	except:
		pass

def disks_from_slot(slots):
	devs = [];
	failed_slot = []
	slot_list = slots.split()
	for slot in slot_list:
		disk = disk_name(slot)
		if (disk):
			devs.append(disk)
		else:
			failed_slot.append(slot)
	return devs,failed_slot

def md_get_mddev(mdname):
	mddevs = list_files("/dev", "md[0-9]+")
	for md in mddevs:
		cmd = "mdadm -Ds %s |grep %s" % (md, mdname)
	sts,out = commands.getstatusoutput(cmd)
	if sts == 0:
		return md
	return None

def set_disk_free(diskname):
	cmd = "mdadm --zero-superblock %s 2>&1" % diskname
	sts,out = commands.getstatusoutput(cmd)

	# 修改判断清空superblock的条件
	# 常见的出错提示
	#   mdadm: Unrecognised md component device - /dev/sdb
	#   mdadm: Unrecognised md component device - /dev/sdg
	# 以上出错mdadm返回值均为0
	if len(out) == 0:
		return True
	else:
		return False

def set_spare(mdname, slots):
	disks,failed = disks_from_slot(slots)
	if (len(disks) == 0):
		return False, "未找到磁盘"
	if len(failed) != 0:
		return False, "未找到磁盘'%s'" % " ".join(failed)
	mddev = md_get_mddev(mdname)
	if mddev == None:
		return False, "未找到卷组'%s'" % mdname

	cmd = "mdadm -a %s" % (mddev)
	for i in disks:
		cmd += " " + i
	cmd += " 2>/dev/null"
	sts,out = commands.getstatusoutput(cmd)
	if sts != 0:
		return False,"设置'%s'为热备盘失败" % slots;
	return True, "设置'%s'为热备盘成功" % slots

def set_slots_free(slots):
	if len(slots) == 0:
		return False,"请输入设置空闲盘的磁盘槽位号!"

	failed = []
	for slot in slots:
		disk = disk_name(slot)
		if disk == None:
			failed.append(slot)
			continue
		ret = set_disk_free(disk)
		if ret == False:
			failed.append(slot)

	if len(failed) != 0:
		return False,"设置'%s'为空闲盘失败" % " ".join(failed)
	return True,"设置'%s'为空闲盘成功" % slots

def set_disks_free(disks):
	res = ""
	for dev in disks:
		err = set_disk_free(dev)
		if err == False:
			res += " " + dev
	disk_name_update(disks)
	return res
