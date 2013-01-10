#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import commands
from libiscsicommon import SCST
from libmd import md_info_mddevs
from libtarget import iSCSISetDefaultTarget

# 将SCST配置文件中的md节点名称替换为UUID
def iSCSI_SCST_cfg_convert():
	try:
		f = open(SCST.CFG)
		xx = f.read()
		f.close()

		mddev_list = re.findall('\/dev\/md\d+', xx)
		if len(mddev_list) == 0:
			return
		for mdinfo in md_info_mddevs()['rows']:
			if mdinfo['dev'] in mddev_list:
				xx = xx.replace(mdinfo['dev'], mdinfo['raid_uuid'])
		f = open(SCST.CFG, 'w')
		f.write(xx)
		f.close()

		os.rename(tmp_file, SCST.CFG)
	except:
		pass
	return

# 将SCST配置文件中的UUID名称转换为节点名称
# 并且检查对应的分区是否存在，如果不存在，则记录日志删除对应的配置
def iSCSI_SCST_cfg_restore():
	tmp_file = '/tmp/.iscsi-scst-conf'
	try:
		f = open(SCST.CFG)
		xx = f.read()
		f.close()

		uuid_list = re.findall('\w{8}:\w{8}:\w{8}:\w{8}', xx)
		if len(uuid_list) == 0:
			return
		for mdinfo in md_info_mddevs()['rows']:
			if mdinfo['raid_uuid'] in uuid_list:
				xx = xx.replace(mdinfo['raid_uuid'], mdinfo['dev'])

		f = open(tmp_file, 'w')
		f.write(xx)
		f.close()
	except:
		pass
	return tmp_file

def iSCSIUpdateCFG():
	try:
		_cmd = 'scstadmin -write_config %s' % SCST.CFG
		ret,msg = commands.getstatusoutput(_cmd)
		if ret == 0:
			iSCSI_SCST_cfg_convert()
			return True, '写入配置文件成功'
		else:
			return False, msg
	except:
		return False, '写入配置文件失败，未知原因'

def iSCSIReloadCFG():
	try:
		_cmd = 'scstadmin -config %s' % iSCSI_SCST_cfg_restore()
		ret,msg = commands.getstatusoutput(_cmd)
		print _cmd
		print ret
		if ret == 0:
			return True, '加载iSCSI配置成功'
		# 设置默认配置，保证target能启动
		iSCSISetDefaultTarget(force = True)
		_cmd = 'scstadmin -config %s' % SCST.CFG
		ret,msg = commands.getstatusoutput(_cmd)
		if ret == 0:
			return True, '加载用户iSCSI配置失败，尝试加载默认配置成功'
		else:
			return False, '加载用户iSCSI配置失败，尝试加默认配置失败'
	except:
		return False, '加载iSCSI配置失败，未知原因'

if __name__ == '__main__':
	#print iSCSIUpdateCFG()
	#iSCSI_SCST_cfg_restore()
	print iSCSIReloadCFG()
