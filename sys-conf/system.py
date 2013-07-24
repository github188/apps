#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import sys

from libcommon import *
from libsysinfo import *
from libsysalarm import *
from libsysparam import *
from libsysupdate import sys_update

reload(sys)
sys.setdefaultencoding('utf-8')

def alarm_email_output():
	alarm_email = alarm_email_get()
	if alarm_email is None:
		comm_exit(False, '获取邮件告警配置失败')

	email_dict = {}
	email_dict['alarm'] = 'email'
	if alarm_email.switch:
		email_dict['value'] = alarm_email.switch
	else:
		email_dict['value'] = 'disable'
	if alarm_email.smtp_host and alarm_email.smtp_port and alarm_email.receiver and alarm_email.ssl:
		email_attr = {}
		email_attr['receiver'] = alarm_email.receiver
		email_attr['smtp_host'] = alarm_email.smtp_host
		email_attr['smtp_port'] = alarm_email.smtp_port
		email_attr['with_ssl'] = alarm_email.ssl

		attr_auth = {}
		attr_auth['user'] = alarm_email.auth_user
		attr_auth['password'] = alarm_email.auth_password
		email_attr['auth'] = attr_auth
		email_dict['attrs'] = email_attr
	
	print json.dumps(email_dict)
	sys.exit(0)

def __system_usage():
	print 'system --get-info [--item <name>]'
	print '            info item support: %s' % get_info_item()
	print ''
	print '       --get-status [--item <name>]'
	print '            status item support: %s' % get_stat_item()
	print ''
	print '       --set <module> --value <module-dependent-value>'
	print '            module: %s' % get_param_item()
	print ''
	print '       --alarm --email --set enable|disable [--receiver <email_list> --smtp-host <ip|domain> --smtp-port <xx> --with-ssl enable|disable --with-auth enable|disable [--auth-user <xx> --auth-password <xx>]]'
	print '       --alarm --email --get'
	print '       --alarm --email --test'
	print '       --alarm --email --send --subject <email subject> --content <email content>'
	print ''
	print '       --alarm --set <module> --switch enable|disable'
	print '       --alarm --get [--module <name>]'
	print '            module: %s' % get_alarm_module()
	print ''
	print '       --update <file_path>'
	sys.exit(-1)

OP_MODE = ['--get-info', '--get-status', '--alarm', '--update']
system_long_opt = ['get-info', 'item=', 'get-status', 'set=', 'value=', 'alarm', 'email', 'switch=',
'receiver=', 'smtp-host=', 'smtp-port=', 'with-ssl=', 'with-auth=', 'auth-user=', 'auth-password=',
'get', 'test', 'module=', 'category=', 'switch=', 'send', 'subject=', 'content=', 'update=']


def main():

	_mode = None
	_sys_item = None  # for get-info , get-status
	_set_arg = None
	_value_arg = None
	_get_arg = None
	_email_arg = None
	_test_arg = None
	_send_arg = None
	_module = None
	_category = None
	_switch = None
	_subject = None
	_content = None
	_email = AlarmEmailConf()
	_file_path = None

	try:
		opts,args = getopt.gnu_getopt(sys.argv[1:], '', system_long_opt)
	except getopt.GetoptError, e:
		comm_exit(False, '%s' % e)

	for opt,arg in opts:
		if opt in OP_MODE:
			_mode = opt

		if opt == '--item':
			_sys_item = arg
		elif opt == '--set':
			_set_arg = arg
			_email.switch = arg
		elif opt == '--value':
			_value_arg = arg
		elif opt == '--get':
			_get_arg = True
		elif opt == '--test':
			_test_arg = True
		elif opt == '--send':
			_send_arg = True
		elif opt == '--email':
			_email_arg = True
		elif opt == '--receiver':
			_email.receiver = arg
		elif opt == '--smtp-host':
			_email.smtp_host = arg
		elif opt == '--smtp-port':
			_email.smtp_port = arg
		elif opt == '--with-ssl':
			_email.ssl = arg
		elif opt == '--auth-user':
			_email.auth_user = arg
		elif opt == '--auth-password':
			_email.auth_password = arg
		elif opt == '--module':
			_module = arg
		elif opt == '--switch':
			_switch = arg
		elif opt == '--category':
			_category = arg
		elif opt == '--subject':
			_subject = arg
		elif opt == '--content':
			_content = arg
		elif opt == '--update':
			_file_path = arg

	# mode check
	if _mode == '--get-info':
		CommOutput(get_sys_info(_sys_item), dict_dump)
		sys.exit(0)
	elif _mode == '--get-status':
		CommOutput(get_sys_stat(_sys_item), dict_dump)
		sys.exit(0)
	elif _mode == '--alarm':
		if _email_arg:
			if _get_arg:
				alarm_email_output()
			elif _set_arg:
				ret,msg = alarm_email_set(_email)
				log_insert('SysConf', 'Auto', 'Info' if ret else 'Error', msg)
				comm_exit(ret, msg)
			elif _test_arg:
				ret,msg = alarm_email_test()
				log_insert('SysConf', 'Auto', 'Info' if ret else 'Error', msg)
				comm_exit(ret, msg)
			elif _send_arg:
				if _subject == None:
					comm_exit(False, '邮件主题不能为空!')
				if _content == None:
					comm_exit(False, '邮件内容不能为空!')

				ret,msg = alarm_email_send(_subject, _content)
				log_insert('SysConf', 'Auto', 'Info' if ret else 'Error', msg)
				comm_exit(ret, msg)
			else:
				comm_exit(False, '请输入email的配置项')
		elif _get_arg:
			CommOutput(alarm_get(_module), dict_dump)
		elif _set_arg:
			ret,msg = alarm_set(_set_arg, _switch)
			comm_exit(ret, msg)
		else:
			comm_exit(False, '请输入正确的告警参数!')

	elif _set_arg:
		ret,msg = sys_param_set(_set_arg, _value_arg)
		comm_exit(ret, msg)

	elif _mode == '--update':
		ret,msg = sys_update(_file_path)
		log_insert('SysConf', 'Auto', 'Info' if ret else 'Error', msg)
		comm_exit(ret, msg)

	__system_usage()

if __name__ == '__main__':
	main()
