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
from libcommon import LogInsert

MOUNT_ROOT = '/mnt/Share'

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


def nas_mkfs(dev, filesystem):
	cmd = 'nas-mkfs.sh %s %s' % (dev, filesystem)
	args = shlex.split(cmd)
	calc_start = False  # 检查 Writing inode tables
	progress = 0.00
	conf_added = False
	counter = 3

	nas_tmpfs_set_value('state', 'format-starting')
	p = sp.Popen(args, stdout=sp.PIPE)

	nas_tmpfs_set_value('state', 'formatting')
	while True:
		ret = sp.Popen.poll(p)
		if ret == 0:	# 程序正常结束
			progress = 100.00
			nas_tmpfs_set_value('fmt_percent', '%.2f' % progress)
			nas_tmpfs_set_value('state', 'format-finished')
			return True
		elif ret is None:	# 程序正在运行
			if progress > 90.0 and counter > 0:
				LogInsert('NAS', 'Auto', 'Info', 'NAS卷格式化进度超过 90% 已经接近完成，请耐心等待')
				counter = counter - 1
			elif progress >= 70.0 and counter > 0:
				LogInsert('NAS', 'Auto', 'Info', 'NAS卷格式化进度超过 70% 请耐心等待')
				counter = counter - 1
			elif progress >= 30.0 and counter > 0:
				LogInsert('NAS', 'Auto', 'Info', 'NAS卷格式化进度超过 30% 请耐心等待')
				counter = counter - 1

			if not conf_added and progress > 0.00:
				conf = NasVolumeAttr()
				tmp_dir = nas_tmpfs_get_dir()
				conf.state = nas_tmpfs_get_value('%s/state' % tmp_dir)
				conf.volume_name = nas_tmpfs_get_value('%s/volume_name'% tmp_dir)
				conf.fs_type = nas_tmpfs_get_value('%s/fs_type' % tmp_dir)
				ret,msg = nas_conf_add(conf)
				conf_added = ret
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
				nas_tmpfs_set_value('fmt_percent', '%.2f' % progress)
		else:	# 程序异常退出
			return False

def _name(mnt):
	return mnt.split('/')[-1]

def _remove_udv(mnt):
	udv_name = mnt.split('/')[-1]
	os.popen('sys-manager udv --delete %s' % udv_name)
	return

def do_run(dev, mnt, filesystem):
	try:
		# 格式化
		LogInsert('NAS', 'Auto', 'Info', 'NAS卷 %s 格式化开始!' % _name(mnt))
		if not nas_mkfs(dev, filesystem):
			nas_tmpfs_set_value('state', 'format-error')
			LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 格式化失败!' % _name(mnt))
			_remove_udv(mnt)
			return

		# 挂载
		nas_tmpfs_set_value('state', 'mounting')
		if not os.path.exists(MOUNT_ROOT):
			os.mkdir(MOUNT_ROOT)
		if not os.path.exists(mnt):
			os.mkdir(mnt)
		ret,msg = commands.getstatusoutput('mount %s %s' % (dev, mnt))
		if ret != 0:
			nas_tmpfs_set_value('state', 'mount-error')
			LogInsert('NAS', 'Auto', 'Error', 'NAS卷 %s 挂载失败！' % _name(mnt))
			_remove_udv(mnt)
			return

		# 设置访问权限 777
		os.chmod(mnt, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)

		# 操作成功，退出
		nas_tmpfs_set_value('state', 'mounted')
		LogInsert('NAS', 'Auto', 'Info', 'NAS卷 %s 挂载成功!' % _name(mnt))

		nasUpdateCFG()
		sys.exit(0)
	except:
		pass

def nas_mkfs_usage():
	print """
nas_mkfs.py --udv <udv_name> --dev <dev_name> --mount <mount_dir> --filesystem <ext3|ext4>
"""
	sys.exit(-1)

mkfs_long_opt = ['udv=', 'dev=', 'mount=', 'filesystem=']

# 主函数入口
def main():
	dev = ''
	udv = ''
	mount = ''
	filesystem = 'ext4'	# set default to ext4
	try:
		opts,args = getopt.gnu_getopt(sys.argv[1:], '', mkfs_long_opt)
	except getopt.GetoptError,e:
		nas_mkfs_usage()

	for opt,arg in opts:
		if opt == '--udv':
			udv = arg
		elif opt == '--dev':
			dev = arg
		elif opt == '--mount':
			mount = arg
		elif opt == '--filesystem':
			filesystem = arg

	if dev!='' and udv!='' and mount!='':
		nas_tmpfs_set_value('volume_name', udv)
		nas_tmpfs_set_value('path', mount)
		nas_tmpfs_set_value('fs_type', filesystem)
		do_run(dev, mount, filesystem)
	else:
		nas_mkfs_usage()

if __name__ == '__main__':
	main()
