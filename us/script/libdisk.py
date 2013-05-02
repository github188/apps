#!/usr/bin/env python
# -*- coding: utf-8 -*-

import commands
import os
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

def disk_bad_sect_redirection(disk_dev):
	dev_name = os.path.basename(disk_dev)
	cmd = 'echo "enable" > /sys/block/%s/bad_sect_map/stat' % dev_name
	ret,msg = commands.getstatusoutput(cmd)
	return True if ret == 0 else False

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
		if md.find('p') >= 0:
			continue
		# 尝试从mdadm获取信息
		cmd = 'mdadm -D %s 2>&1 | grep %s >/dev/null' % (md, mdname)
		sts,out = commands.getstatusoutput(cmd)
		if sts == 0:
			return md

		# 尝试从tmpfs获取信息
		_dir = '%s/%s' % (TMP_RAID_INFO, basename(md))
		if AttrRead(_dir, 'name') == mdname:
			return md
	return None

def cleanup_disk_mdinfo(diskname):
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

def cleanup_disks_mdinfo(disks):
	res = ""
	for dev in disks:
		err = cleanup_disk_mdinfo(dev)
		if err == False:
			res += " " + dev
	disk_name_update(disks)
	return res

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

if __name__ == '__main__':
	#print get_free_disk()
	disk_slot_update('0:16')
