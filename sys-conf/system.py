#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getopt
import sys
from libsysinfo import *
from libsysalarm import *
from libsysparam import *

reload(sys)
sys.setdefaultencoding('utf-8')

def json_dump(obj):
	if os.environ.get('SUDO_USER') == 'www-data' or os.environ.get('LOGNAME') == 'www-data':
		print json.dumps(obj, ensure_ascii=False, sort_keys=True)
	else:
		print json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=4)

def __alarm_email_conf_todict(email):
	_email_dict = {}
	_email_dict['alarm'] = 'email'
	if email.switch:
		_email_dict['value'] = email.switch
	else:
		_email_dict['value'] = 'disable'
	if email.smtp_host and email.smtp_port and email.receiver and email.ssl:
		_email_attr = {}
		_email_attr['receiver'] = email.receiver
		_email_attr['smtp_host'] = email.smtp_host
		_email_attr['smtp_port'] = email.smtp_port
		_email_attr['with_ssl'] = email.ssl
		if email.auth == 'enable':
			_attr_auth = {}
			_attr_auth['user'] = email.auth_user
			_attr_auth['password'] = email.auth_password
			_email_attr['auth'] = _attr_auth
		_email_dict['attrs'] = _email_attr
	return _email_dict

def __systemExit(ret = True, msg = ''):
	ret_msg = {'status':True, 'msg':''}
	ret_msg['status'] = ret
	ret_msg['msg'] = msg
	print json.dumps(ret_msg, encoding="UTF-8", ensure_ascii=False)
	if ret:
		sys.exit(0)
	sys.exit(-1)

def __system_usage():
	print 'system --get-info [--item <name>]'
	print '            info item support: %s' % get_info_item()
	print '       --get-status [--item <name>]'
	print '            status item support: %s' % get_stat_item()
	print '       --set <module> --value <module-dependent-value>'
	print '            module: %s' % get_param_item()
	print '       --alarm --email --set <enable|disable> [--receiver <email_list> --smtp-host <ip|domain> --smtp-port <xx> --with-ssl <enable|disable> --with-auth <enable|disable> [--auth-user <xx> --auth-password <xx>]]'
	print '       --alarm --email --get'
	print '       --alarm --email --test'
	print '       --alarm --email --send --subject <email subject> --content <email content>'
	print '       --alarm --set <module> --switch <enable|disable> [--category <buzzer|sys-led|email>]'
	print '            module: %s' % get_alarm_module()
	print '            category: %s' % get_alarm_category()
	print '       --alarm --get [--module <name>]'
	sys.exit(-1)

OP_MODE = ['--get-info', '--get-status', '--alarm']
system_long_opt = ['get-info', 'item=', 'get-status', 'set=', 'value=', 'alarm', 'email',
'receiver=', 'smtp-host=', 'smtp-port=', 'with-ssl=', 'with-auth=', 'auth-user=', 'auth-password=',
'get', 'test', 'module=', 'category=', 'switch=', 'send', 'subject=', 'content=']


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
	_email = email_conf()

	try:
		opts,args = getopt.gnu_getopt(sys.argv[1:], '', system_long_opt)
	except getopt.GetoptError, e:
		__systemExit(False, '%s' % e)

	for opt,arg in opts:
		if opt in OP_MODE:
			_mode = opt
		elif opt == '--item':
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
			# 加载旧配置
			ret,conf = alarm_email_get()
			if ret:
				_email = conf
			_email_arg = True
		elif opt == '--receiver':
			_email.receiver = arg
		elif opt == '--smtp-host':
			_email.smtp_host = arg
		elif opt == '--smtp-port':
			_email.smtp_port = arg
		elif opt == '--with-ssl':
			_email.ssl = arg
		elif opt == '--with-auth':
			_email.auth = arg
		elif opt == '--auth-user':
			_email.auth_user = arg
		elif opt == '--auth-password':
			_email.auth_password = arg
		elif opt == '--module':
			_module = arg
		elif opt == '--category':
			_category = arg
		elif opt == '--subject':
			_subject = arg
		elif opt == '--content':
			_content = arg

	# mode check
	if _mode == '--get-info':
		#print json.dumps(sys_global(get_sys_info(_sys_item)))
		json_dump(sys_global(get_sys_info(_sys_item)))
		sys.exit(0)
	elif _mode == '--get-status':
		#print json.dumps(sys_global(get_sys_stat(_sys_item)))
		json_dump(sys_global(get_sys_stat(_sys_item)))
		sys.exit(0)
	elif _mode == '--alarm':
		if _email_arg:
			if _get_arg:
				_ret,_msg = alarm_email_get()
				if ret:
					print json.dumps(__alarm_email_conf_todict(_msg))
					sys.exit(0)
				__systemExit(_ret, _msg)
			elif _set_arg:
				_ret,_msg = alarm_email_set(_email)
				__systemExit(_ret, _msg)
			elif _test_arg:
				_ret,_msg = alarm_email_test()
				__systemExit(_ret, _msg)
			elif _send_arg:
				if _subject == None:
					_systemExit(False, '邮件主题不能为空!')
				if _content == None:
					_systemExit(False, '邮件内容不能为空!')

				_ret,_msg = alarm_email_send(_subject, _content)
			else:
				__systemExit(False, '请输入email的配置项')
		elif _get_arg:
			_ret,_msg = alarm_get(_module)
			if _ret:
				print json.dumps(sys_global(_msg))
				sys.exit(0)
			__systemExit(_ret, _msg)
		elif _set_arg:
			_ret,_msg = alarm_set(_set_arg, _switch, _category)
			__systemExit(_ret, _msg)
		else:
			__systemExit(False, '请输入正确的告警参数!')
	elif _set_arg:
		_ret,_msg = sys_param_set(_set_arg, _value_arg)
		__systemExit(_ret, _msg)

	__system_usage()

if __name__ == '__main__':
	main()
