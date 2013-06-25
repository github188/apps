#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# 文件名称: handle_disk
# 作用: 处理磁盘上下线事件
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 输入参数格式:
#     argv[0] - (this program)
#     argv[1] - disk dev (eg. /dev/sdb)
#     argv[2] - action <add|remove|change>
# -----------------------------------------------------------------------------

import sys,os
import time
from libmd import *

reload(sys)
sys.setdefaultencoding('utf8')

# 磁盘上线事件处理
def handle_disk_add(diskinfo):
	msg = '磁盘 %s 上线' % diskinfo.slot
	vg_log('Info', msg)

	if diskinfo.slot == None:
		return
	ret,text = commands.getstatusoutput('disk --list --slot-id %s' % diskinfo.slot)
	if ret != 0:
		return
	disk_info = json.loads(text)
	if disk_info['SMART'] == 'Bad':
		msg = '磁盘 %s 故障' % diskinfo.slot
		vg_log('Error', msg)
		sysmon_event('disk', 'led_blink1s4', 'disks=%s' % diskinfo.slot, '')
		sysmon_event('disk', 'buzzer_on', '%s' % diskinfo.slot, '')
		return
	elif disk_info['SMART'] == 'LowHealth':
		msg = '磁盘 %s 健康度低' % diskinfo.slot
		vg_log('Error', msg)
		sysmon_event('disk', 'led_blink2s1', 'disks=%s' % diskinfo.slot, '')
		return
	elif disk_info['state'] == 'Global' or disk_info['state'] == 'Special':
		sysmon_event('disk', 'led_on', 'disks=%s' % diskinfo.slot, '')
	elif disk_info['state'] != 'Invalid':
		return

	mdattr = get_mdattr_by_mduuid(diskinfo.md_uuid)
	if mdattr == None:
		return

	if mdattr.raid_state != 'degrade':
		return
	
	if add_disk_to_md(mdattr.dev, diskinfo.dev) == 0:
		vg_log('Warning', '卷组 %s 所属磁盘 %s 重新加入卷组操作成功' % (mdattr.name, diskinfo.slot))
		mdattr = get_mdattr_by_mddev(mdattr.dev)
		if mdattr.raid_state == 'normal':
			sysmon_event('vg', 'normal', mdattr.name, '卷组 %s 状态正常' % mdattr.name)
	else:
		vg_log('Error', '卷组 %s 所属磁盘 %s 重新加入卷组操作失败' % (mdattr.name, diskinfo.slot))

# 磁盘掉线和被踢事件处理
def handle_disk_remove_kicked(diskinfo, event):
	# 被踢磁盘按故障盘处理
	if event == 'rdkicked':
		msg = '磁盘 %s 故障' % diskinfo.slot
		sysmon_event('disk', 'led_blink1s4', 'disks=%s' % diskinfo.slot, '')
		sysmon_event('disk', 'buzzer_on', '%s' % diskinfo.slot, '')
	elif event == 'remove':
		msg = '磁盘 %s 掉线' % diskinfo.slot
		sysmon_event('disk', 'led_off', 'disks=%s' % diskinfo.slot, '')
		sysmon_event('disk', 'buzzer_off', '%s' % diskinfo.slot, '')
	else:
		return

	mdattr = get_mdattr_by_disk(diskinfo.dev)
	if mdattr == None:
		vg_log('Error', msg)
		return
	
	msg += ', 所属卷组 %s' % mdattr.name
	vg_log('Error', msg)

	if mdattr.raid_level == '0' or mdattr.raid_level == 'JBOD':
		tmpfs_remove_disk_from_md(mdattr.dev, disk_dev2slot(diskinfo.dev))
		# 重新获取状态, raid0 jbod需要根据磁盘数判断状态
		mdattr = get_mdattr_by_mddev(mdattr.dev)
	else:
		if event == 'remove':
			faulty_disk_in_md(mdattr.dev, diskinfo.dev)

		# tmpfs下标示正在处理raid事件, 然后从md删除磁盘
		rebuilder_cn = inc_md_rebuilder_cnt(basename(mdattr.dev))
		remove_disk_from_md(mdattr.dev, diskinfo.dev)
		# 重新获取状态, 磁盘掉线后, raid如果没有读写, 不会马上发现
		retry_cnt = 10
		while retry_cnt > 0:
			mdattr = get_mdattr_by_mddev(mdattr.dev)
			if diskinfo.slot not in mdattr.disk_list:
				break
			time.sleep(0.5)
			retry_cnt -= 1
		
		# 磁盘故障灯可能会被其他掉盘/踢盘事件关掉，重新打开
		if event == 'rdkicked':
			sysmon_event('disk', 'led_blink1s4', 'disks=%s' % diskinfo.slot, '')

		if mdattr.raid_state != 'degrade':
			dec_md_rebuilder_cnt(basename(mdattr.dev))

	if mdattr.raid_state == 'degrade':
		# 针对raid6已经有事件处理降级, 则不再处理
		if rebuilder_cn > 1:
			dec_md_rebuilder_cnt(basename(mdattr.dev))
			return

		msg = '卷组 %s 降级' % mdattr.name
		vg_log('Warning', msg)
		sysmon_event('vg', 'degrade', mdattr.name, msg)
		sysmon_event('disk', 'led_off', 'disks=%s' % list2str(mdattr.disk_list, ','), '')
		
		# 掉盘后等待5分钟, 如果磁盘重新上线可快速重建RAID, 不需要使用热备盘重建
		# 等待后重新获取状态, 如果不再是degrade状态, 则不需要处理
		if event == 'remove':
			sts,seconds = commands.getstatusoutput('head -n 1 /tmp/disk_remove_sleep')
			if sts != 0:
				seconds = 300
			elif seconds.isdigit():
				seconds = int(seconds)
			else:
				seconds = 300
			time.sleep(seconds)
			mdattr = get_mdattr_by_mddev(mdattr.dev)
			if mdattr.raid_state == 'degrade':
				md_rebuild(mdattr)
		else:
			md_rebuild(mdattr)

		dec_md_rebuilder_cnt(basename(mdattr.dev))
		return

	elif mdattr.raid_state == 'fail':
		drop_cache()
		msg = '卷组 %s 失效' % mdattr.name
		vg_log('Error', msg)
		sysmon_event('vg', 'fail',  mdattr.name, msg)
		sysmon_event('disk', 'led_off', 'disks=%s' % list2str(mdattr.disk_list, ','), '')

	# 热替换后, 源盘被踢出raid, 如果没有其他盘出错, raid状态正常

	return

# args [0]  - self
#      [1]  - dev eg. /dev/sdb
#      [2]  - action 'add', 'remove' ...
def main():

	if len(sys.argv) != 3:
		return

	diskinfo = get_disk_info(sys.argv[1])  # argv[1] - disk_dev
	event = sys.argv[2]
	if event == 'add':
		handle_disk_add(diskinfo)
	else:
		handle_disk_remove_kicked(diskinfo, event)

if __name__ == "__main__":
	main()
