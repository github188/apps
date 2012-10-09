#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shlex
import subprocess as sp
import time
import re
import sys
import threading
from libnascommon import *

"""
需要记录的有：
挂载 path
格式化进度 fmt_percent
卷名称 volume_name
设备名称 dev
"""

# Global
fmt_obj = NasVolumeAttr()

"""
mkfs_ext3.py --udv [udv_name] --dev [dev_name] --mount-point [mount_name]
"""

"""
cmmand:
	get path (c)
	get fmt_percent (c)
	get volume_name (c)
	get dev (c)
	get fs_type (c)
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
	global fmt_obj
	cmd = 'mkfs-ext3.sh %s' % dev
	args = shlex.split(cmd)
	calc_start = False  # 检查 Writing inode tables
	progress = 0.00

	fmt_obj.state = 'format-starting'
	p = sp.Popen(args, stdout=sp.PIPE)

	fmt_obj.state = 'formating'
	while True:
		ret = sp.Popen.poll(p)
		if ret == 0:	# 程序正常结束
			progress = 100.00
			fmt_obj.fmt_percent = progress
			fmt_obj.state = 'format-finshed'
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
				fmt_obj.fmt_percent = progress
		else:	# 程序异常退出
			return False

# 业务线程
class work_thread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self, dev, mnt):
		try:
			# 格式化
			if not mkfs_ext3(dev):
				fmt_obj.state = 'format-error'
				return
			# 挂载
			fmt_obj.state = 'mounting'
			ret,msg = commands.getstatusoutput('mount %s %s' % (dev, mnt))
			if ret != 0:
				fmt_obj.state = 'mount-error'
				return

			# 加入配置文件
			ret,msg = nas_conf_add(dev, mnt)
			if not ret:
				fmt_obj.state = 'mount-conf-error'

			# 操作成功，退出
			fmt_obj.state = 'mounted'
			sys.exit(0)
		except:
			pass

# 后台通信线程
class communicate(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):

# 主函数入口
def main():
	worker = work_thread()
	comm = communicate()
	worker.start()
	comm.start()
	worker.join()
	comm.join()

if __name__ == '__main__':
	#mkfs_ext3('/dev/sda1')
	main()
