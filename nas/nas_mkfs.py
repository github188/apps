#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shlex
import subprocess as sp
import time
import re
import sys
import threading
import getopt
import sys, os

from libnas import *
from libcommon import log_insert

def nas_mkfs(udv_name, udv_dev, filesystem):
	progress_file = NAS_DIR + os.sep + udv_name + '/fmt_percent'
	cmd = 'nas-mkfs.sh %s %s' % (udv_dev, filesystem)
	args = shlex.split(cmd)
	calc_start = False  # 检查 Writing inode tables
	progress = 0.00
	fmt_record = [30.0, 70.0, 90.0]
	i = 0

	p = sp.Popen(args, stdout=sp.PIPE)
	while True:
		ret = sp.Popen.poll(p)
		if ret == 0:	# 程序正常结束
			progress = 100.00
			nas_fmt_record_set(udv_name, '%.2f' % progress)
			log_insert('NAS', 'Auto', 'Info', 'NAS卷 %s 格式化完成' % udv_name)
			return True
		elif ret is None:	# 程序正在运行
			p.stdout.flush()
			line = p.stdout.readline().strip()
			if not calc_start and line.find('Writing inode tables') >= 0:
				calc_start = True
				continue
			if calc_start and line.find('Writing superblocks and filesystem accounting information') >= 0:
				calc_start = False
				continue

			val = line.split('/')
			if calc_start and len(val) == 2:
				progress = float(val[0]) * 100.00 / float(val[1])
				nas_fmt_record_set(udv_name, '%.2f' % progress)
			
				if i < len(fmt_record) and progress > fmt_record[i]:
					log_insert('NAS', 'Auto', 'Info', 'NAS卷 %s 格式化进度 %.2f' % (udv_name, progress))
					i += 1

		elif 35072 == ret: # 格式化进程被kill -9杀死, nas卷被删除, 直接退出
			sys.exit(0)
		else:	# 格式化失败
			return False

def do_run(udv_name, udv_dev, mount_dir, filesystem):
	# 格式化
	log_insert('NAS', 'Auto', 'Info', 'NAS卷 %s 格式化开始' % udv_name)
	if not nas_mkfs(udv_name, udv_dev, filesystem):
		log_insert('NAS', 'Auto', 'Error', 'NAS卷 %s 格式化失败' % udv_name)
		nas_vol_remove(udv_name)
		return

	# 挂载
	if not nas_vol_mount(udv_dev, mount_dir):
		log_insert('NAS', 'Auto', 'Error', 'NAS卷 %s 挂载失败' % udv_name)
		nas_vol_remove(udv_name)
		return

	# 更新配置文件
	if not nas_conf_update_bydev(udv_dev, 'mounted', filesystem):
		log_insert('NAS', 'Auto', 'Info', 'NAS卷 %s 更新配置文件失败' % udv_name)
		nas_vol_remove(udv_name)
		return
	
	log_insert('NAS', 'Auto', 'Info', 'NAS卷 %s 挂载成功' % udv_name)

def nas_mkfs_usage():
	print """
nas_mkfs.py --udv <udv_name> --dev <dev_name> --mount <mount_dir> --filesystem <ext3|ext4>
"""
	sys.exit(-1)

mkfs_long_opt = ['udv=', 'dev=', 'mount=', 'filesystem=']

# 主函数入口
def main():
	udv_dev = ''
	udv_name = ''
	mount_dir = ''
	filesystem = 'ext4'	# set default to ext4
	try:
		opts,args = getopt.gnu_getopt(sys.argv[1:], '', mkfs_long_opt)
	except getopt.GetoptError,e:
		nas_mkfs_usage()

	for opt,arg in opts:
		if opt == '--udv':
			udv_name = arg
		elif opt == '--dev':
			udv_dev = arg
		elif opt == '--mount':
			mount_dir = arg
		elif opt == '--filesystem':
			filesystem = arg

	if udv_dev != '' and udv_name != '' and mount_dir != '':
		do_run(udv_name, udv_dev, mount_dir, filesystem)
	else:
		nas_mkfs_usage()

if __name__ == '__main__':
	main()
