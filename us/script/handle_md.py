#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from libmd import *

def handle_md_sync(mddev):
	md = basename(mddev)
	f_lock = lock_file('%s/%s_sync' % (RAID_DIR_LOCK, md))

	mdattr = get_mdattr_by_mddev(mddev)

	msg = '卷组 %s ' % mdattr.name
	if mdattr.raid_state == 'initial':
		msg += '初始化 开始'
	elif mdattr.raid_state == 'rebuild':
		msg += '重建 开始'
	elif mdattr.raid_state == 'reshape':
		msg += '扩容 开始'
	else:
		unlock_file(f_lock)
		return None
	
	dir = RAID_DIR_BYMD + '/' + md
	if not os.path.exists(dir):
		os.makedirs(dir)
	# raid6 初始化/重建时掉盘内核会重启resync线程, 此时忽略事件
	if os.path.isfile(dir + '/sync_action'):
		unlock_file(f_lock)
		return None

	cmd = 'echo ' + mdattr.raid_state + ' > ' + dir + '/sync_action'
	os.system(cmd)

	vg_log('Info', msg)
	sysmon_event('vg', 'rebuild', mdattr.name, msg)
	sysmon_event('disk', 'led_blink1s1', 'disks=%s' % list2str(mdattr.disk_list, ','), '')
	# 最后再解锁，防止日志顺序错乱
	unlock_file(f_lock)
	return

def handle_md_syncdone(mddev):
	mdattr = get_mdattr_by_mddev(mddev)
	# raid6 初始化/重建时掉盘内核会重启resync线程, 此时忽略事件
	if mdattr.raid_state == 'initial' or mdattr.raid_state == 'rebuild' or mdattr.raid_state == 'reshape':
		return None

	log_level = 'Info'
	md = basename(mddev)
	f_lock = lock_file('%s/%s_sync' % (RAID_DIR_LOCK, md))

	cmd = 'cat ' + RAID_DIR_BYMD + '/' + md + '/sync_action'
	sts,sync_action = commands.getstatusoutput(cmd)
	if sts != 0:
		sync_action = ''
	else:
		os.remove(RAID_DIR_BYMD + '/' + md + '/sync_action')
	unlock_file(f_lock)

	msg = '卷组 %s ' % mdattr.name
	if sync_action == 'initial':
		msg += '初始化' 
	elif sync_action == 'rebuild':
		msg += '重建'
	elif sync_action == 'reshape':
		msg += '扩容'
	else:
		return None
	
	if sync_action == 'reshape':
		if mdattr.raid_state != 'normal':
			update_mdattr = 0
			dev_sdx_paths = commands.getoutput('ls -d /sys/block/%s/md/dev-sd* 2>/dev/null' % md)
			for dev_sdx_path in dev_sdx_paths.split():
				dev_state = commands.getoutput('cat %s/state 2>/dev/null' % dev_sdx_path)
				if dev_state.find('faulty') >= 0:
					update_mdattr = 1
					i = dev_sdx_path.find('-')
				 	remove_disk_from_md(mdattr.dev, '/dev/' + dev_sdx_path[i+1:])
			if update_mdattr:
				mdattr = get_mdattr_by_mddev(mddev)

		if mdattr.raid_state != 'fail':
			msg += ' 完成'
			# 添加bitmap
			cmd = 'mdadm --grow %s --bitmap=internal 2>&1' % mdattr.dev
			os.system(cmd)
		else:
			log_level = 'Error'
			msg += ' 失败'
	else:
		# 如果raid6坏2块盘, 第一块盘重建完后, 第二快盘开始重建, 
		# 如果没有启动第二块盘重建, 则认为重建失败
		if mdattr.raid_level == '6':
			if mdattr.raid_state == 'normal':
				msg += ' 完成'
			elif mdattr.raid_state == 'degrade':
				log_level = 'Warning'
				msg += ' 中止'
			else:
				log_level = 'Error'
				msg += ' 失败'
		else:
			if mdattr.raid_state == 'normal':
				msg += ' 完成'
			else:
				log_level = 'Error'
				msg += ' 失败'
	
	vg_log(log_level, msg)
	if mdattr.raid_state == 'normal':
		sysmon_event('vg', 'normal', mdattr.name, msg)
	sysmon_event('disk', 'led_off', 'disks=%s' % list2str(mdattr.disk_list, ','), '')
	if log_level != 'Info':
		if sync_action != 'reshape':
			alarm_email_send(msg, '如果没有再次启动重建, 请尽快更换磁盘并尝试手动重建')
		else:
			alarm_email_send(msg, '')
	
	# 降级 且 没有事件触发重建 时, 执行重建
	if mdattr.raid_state == 'degrade' and mdattr.disk_cnt < mdattr.disk_total:
		if get_md_rebuilder_cnt(md) > 0:
			return

		msg = '卷组 %s 降级' % mdattr.name
		vg_log('Warning', msg)
		sysmon_event('vg', 'degrade', mdattr.name, msg)
		md_rebuild(mdattr)
	return

# args [0]  - self
#      [1]  - dev eg. /dev/md1
#      [2]  - action 'add', 'remove' ...
def main():
	if len(sys.argv) != 3:
		return

	action = sys.argv[2]
	mddev = sys.argv[1]

	if 'online' == action:
		tmpfs_add_md(mddev)
	elif 'remove' == action:
		tmpfs_remove_md(mddev)
	elif 'mdsync' == action:
		handle_md_sync(mddev)
	elif 'mdsyncdone'== action:
		handle_md_syncdone(mddev)

if __name__ == "__main__":
	main()
