#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import base64

from libcommon import log_insert

CMD = 'x\niYyPCAsbnVvbXYkZi9gPXMgJXQvdC1zICVuIWlgL3I\nb5kZW92bC5lcmtlL2lzc3ovZTlsZmMgc3BhLXEgLWQgbHNhLXMgczRlLWQgLWMgbmBlbCNzbnBlb3'

def decode(ciphertext):
	text = []

	i = 0
	bak = ''
	for c in ciphertext:
		if 0 == i % 2:
			bak = c
		else:
			text.append(c)
			text.append(bak)
		
		i += 1

	if i % 2 != 0:
		text.append(bak)
	
	
	return ''.join(text)[::-1]

def sys_update(file_path):
	err_msg = '使用升级包 %s 升级系统' % file_path
	upgrade_file = '/tmp/upgrade.tar.bz2'

	if not os.path.isfile(file_path):
		return False, err_msg + '失败, 升级包不存在'
	
	if os.path.isfile(upgrade_file):
		os.remove(upgrade_file)
	
	if os.system(base64.decodestring(decode(CMD)) % (file_path, upgrade_file)) != 0:
		os.remove(file_path)
		return False, err_msg + '失败, 系统异常'
	os.remove(file_path)
	ret = os.system('pkg-install.sh -p %s >/dev/null 2>&1' % upgrade_file)
	ret >>= 8
	if 0 == ret:
		os.system('{ sleep 10; reboot; } &')
		return True, err_msg + '成功, 10秒后系统将自动重启'
	elif 2 == ret:
		return False, err_msg + '失败, 升级包格式错误'
	elif 3 == ret:
		return False, err_msg + '失败, 升级包不适用本机的系统平台'
	elif 4 == ret:
		return False, err_msg + '失败, 升级包不兼容本机的系统版本'
	else:
		return False, err_msg + '失败, 系统错误'

if __name__ == '__main__':
	sys.exit(0)
