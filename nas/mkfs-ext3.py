#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shlex
import subprocess as sp
import time
import re
import sys
import threading
import getopt
from libnas import *


"""
需要记录的有：
挂载 path
格式化进度 fmt_percent
卷名称 volume_name
设备名称 dev
"""

"""
state:
	format-starting	正在启动格式化
	formating	正在格式化
	format-finished	正在结束格式化
	format-error	格式化出错
	mounting	正在挂载
	mounted		已经挂载并且加入到配置文件
	mount-error	挂载失败
	conf-error	设置配置文件失败
"""


def mkfs_ext3(dev):
	cmd = 'mkfs-ext3.sh %s' % dev
	args = shlex.split(cmd)
	calc_start = False  # 检查 Writing inode tables
	progress = 0.00

	__tmpfs_set_value('state', 'format-starting')
	p = sp.Popen(args, stdout=sp.PIPE)

	__tmpfs_set_value('state', 'formating')
	while True:
		ret = sp.Popen.poll(p)
		if ret == 0:	# 程序正常结束
			progress = 100.00
			__tmpfs_set_value('fmt_percent', '%.2f' % progress)
			__tmpfs_set_value('state', 'format-finished')
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
			progress = line.split('/')
			if calc_start and len(progress) == 2:
				curr = float(progress[0])
				total = float(progress[1])
				progress = ((curr / total) * 100.0)
				__tmpfs_set_value('fmt_percent', '%.2f' % progress)
		else:	# 程序异常退出
			return False

def do_run(dev, mnt):
	try:
		# 格式化
		if not mkfs_ext3(dev):
			__tmpfs_set_value('state', 'format-error')
			return
		# 挂载
		__tmpfs_set_value('state', 'mounting')
		ret,msg = commands.getstatusoutput('mount %s %s' % (dev, mnt))
		if ret != 0:
			__tmpfs_set_value('state', 'mount-error')
			return

		# 加入配置文件
		ret,msg = nas_conf_add(dev, mnt)
		if not ret:
			__tmpfs_set_value('state', 'conf-error')

		# 操作成功，退出
		__tmpfs_set_value('state', 'mounted')
		sys.exit(0)
	except:
		pass

def mkfs_ext3_usage():
	print """
mkfs_ext3.py --udv <udv_name> --dev <dev_name> --mount <mount_dir>
"""
	sys.exit(-1)

mkfs_long_opt = ['udv=', 'dev=', 'mount=']

# 主函数入口
def main():
	dev = ''
	udv = ''
	mount = ''
	try:
		opts,args = getopt.gnu_getopt(sys.argv[1:], '', mkfs_long_opt)
	except getopt.GetoptError,e:
		mkfs_ext3_usage()

	for opt,arg in opts:
		if opt == '--udv':
			udv = arg
		elif opt == '--dev':
			dev = arg
		elif opt == '--mount':
			mount = arg

	if dev!='' and udv!='' and mount!='':
		__tmpfs_set_value('volume_name', udv)
		__tmpfs_set_value('path', mount)
		__tmpfs_set_value('fs_type', 'ext3')
		do_run(dev, mount)
	else:
		mkfs_ext3_usage()

if __name__ == '__main__':
	#mkfs_ext3('/dev/sda1')
	main()
