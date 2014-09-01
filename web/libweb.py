#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys
import os
import stat
import commands
import getopt
import json
import ConfigParser
import subprocess
import codecs

reload(sys)
sys.setdefaultencoding('utf8')

LIGHTTPD_CONF_FILE = '/etc/lighttpd/lighttpd.conf'
WEB_CONF_DIR = '/opt/etc/lighttpd'
WEB_CONF_FILE = WEB_CONF_DIR + '/web.conf'

DEFAULT_LIST = ['defaults']
DEFAULT_NAME = 'defaults'

OPT_NAME = 'name'
OPT_DOC = "document-root"
OPT_IDX = "index-file.names"
OPT_PORT = "server.port"

DEFAULT_PORT = '80'
DEFAULT_DOC = '"/var/www"'
DEFAULT_INDEX = '( "index.php", "index.html","index.htm", "default.htm", "index.lighttpd.html" )'

LIGHTTPD_CONF_DEF = """#请不要直接修改本配置文件
#修改lighttpd配置请使用 web 命令\n
server.modules = (
        "mod_access",
        "mod_alias",
        "mod_compress",
        "mod_redirect",
#       "mod_rewrite",
        "mod_fastcgi"
)

server.port                 = %s
server.document-root        = %s
server.upload-dirs          = ( "/var/cache/lighttpd/uploads" )
server.errorlog             = "/var/log/lighttpd/error.log"
server.pid-file             = "/var/run/lighttpd.pid"
server.username             = "www-data"
server.groupname            = "www-data"

index-file.names            = %s

url.access-deny             = ( "~", ".inc" )

static-file.exclude-extensions = ( ".php", ".pl", ".fcgi" )

#include_shell "/usr/share/lighttpd/use-ipv6.pl"

dir-listing.encoding        = "utf-8"
server.dir-listing          = "disable"

compress.cache-dir          = "/var/cache/lighttpd/compress/"
compress.filetype           = ( "application/x-javascript", "text/css", "text/html", "text/plain" )

include_shell "/usr/share/lighttpd/create-mime.assign.pl"
include_shell "/usr/share/lighttpd/include-conf-enabled.pl"

fastcgi.server = ( ".php" =>
                     ( "localhost" =>
                         (
                             "socket" => "/tmp/php.socket",
                             "bin-path" => "/usr/bin/php5-cgi"
                         )
                     )
                 )
"""

OTHER_LIGHTTPD_CONF = """$SERVER["socket"] == ":%s" {
	server.document-root	= "%s"
	index-file.names	= ( "%s" )
}\n
"""

class web_site_info:
	def __init__(self):
		self.name = ''
		self.document_root = ''
		self.index_file = ''
		self.port = ''

def Export(ret = True, msg = ''):
	ret_msg = {'status':True, 'msg':''}
	ret_msg['status'] = ret
	ret_msg['msg'] = msg
	print json.dumps(ret_msg, encoding="utf-8", ensure_ascii=False)
	sys.exit(-1)

def deviant(config, name, field):
	result = ''
	if field != '':
		try:
			result = config.get(name, field)
		except:
			pass
	return result

def update_conf():
	conf_str = ''
	default_str = ''
	other_str = ''

	config = ConfigParser.ConfigParser()
	config.read(WEB_CONF_FILE)
	olist = config.sections()
	olist.sort()
	for name in olist:
		if name in DEFAULT_LIST:
			port_str = deviant(config, name, OPT_PORT)
			if port_str == '':
				port_str = DEFAULT_PORT
			doc_str = deviant(config, name, OPT_DOC)
			if doc_str == '':
				doc_str = DEFAULT_DOC
			idx_str = deviant(config, name, OPT_IDX)
			if idx_str == '':
				idx_str = DEFAULT_IDX
			default_str = LIGHTTPD_CONF_DEF % (port_str, doc_str, idx_str)
		else:
			port_str = deviant(config, name, OPT_PORT)
			doc_str = deviant(config, name, OPT_DOC)
			idx_str = deviant(config, name, OPT_IDX)
			other_str_tmp = OTHER_LIGHTTPD_CONF % (port_str, doc_str, idx_str)
			other_str = other_str + other_str_tmp + '\n'

	conf_str = default_str + other_str

	#~ generate the configuration file which lighttpd used
	lighttpd_conf_file = open(LIGHTTPD_CONF_FILE, 'w')
	try:
		lighttpd_conf_file.write(conf_str)
	finally:
		lighttpd_conf_file.close()

#~#### 恢复默认值
def set_default():
	config = ConfigParser.ConfigParser()
	name="defaults"
	config.add_section(name)
	config.set(name, OPT_NAME, 'defaults')
	config.set(name, OPT_DOC, '%s' % DEFAULT_DOC)
	config.set(name, OPT_PORT, '%s' % DEFAULT_PORT)
	config.set(name, OPT_IDX, '%s' % DEFAULT_INDEX)
	config.write(open(WEB_CONF_FILE, 'w'))

	update_conf()

#~#### 保存配置
def save_conf():
	config.write(open(WEB_CONF_FILE, 'w'))
	update_conf()

def check_default():
	#~ 当站点配置文件不存在时，创建默认文件
	if os.path.exists(WEB_CONF_FILE) == False:
		set_default()

def restart_lighttpd_service():
	cmd = '/etc/init.d/lighttpd restart 2>&1'
	ret,msg = commands.getstatusoutput(cmd)
	return ret, msg

# get the web sites list or specified one if site_name is not null
def get_web_service_list(site_name = ''):
	web_list = []
	check_default()
	config = ConfigParser.ConfigParser()
	config.read(WEB_CONF_FILE)
	olist = config.sections()
	olist.sort()
	for name in olist:
		web_info = web_site_info()
		web_info.name = deviant(config, name, OPT_NAME)
		web_info.document_root = deviant(config, name, OPT_DOC)
		web_info.index_file = deviant(config, name, OPT_IDX)
		web_info.port = deviant(config, name, OPT_PORT)
		if site_name != '':
			if site_name == web_info.name:
				web_list.append(web_info)
				break
		else:
			web_list.append(web_info)

	return web_list

# create a new web site
def create_web_service(site_name):
	if '' == site_name:
		return False, "请输入站点名称."

	check_default()
	config = ConfigParser.ConfigParser()
	config.read(WEB_CONF_FILE)
	if config.has_section(site_name) == False:
		config.add_section(site_name)
		config.set(site_name, OPT_NAME, site_name)
		config.set(site_name, OPT_DOC, '')
		config.set(site_name, OPT_PORT, '')
		config.set(site_name, OPT_IDX, '')
		config.write(open(WEB_CONF_FILE, 'w'))

		update_conf()
		return True, "创建站点%s成功." % (site_name)
	else:
		return False, "创建失败,站点%s已经存在!" % (site_name)

def is_port_used(port):
	config = ConfigParser.ConfigParser()
	config.read(WEB_CONF_FILE)
	olist = config.sections()
	olist.sort()
	for name in olist:
		if port == deviant(config, name, OPT_PORT):
			return True
	return False

# set the web site attributes
def modify_web_service(site_name, arg_attr, arg_value):
	check_default()
	config = ConfigParser.ConfigParser()
	config.read(WEB_CONF_FILE)
	if config.has_section(site_name) == True:
		if OPT_DOC == arg_attr:
			if not os.path.exists(arg_value):
				return False, '设置站点属性失败，%s 不存在' % arg_value
			elif not os.path.isabs(arg_value):
				return False, '设置站点属性失败，%s 不是绝对路径' % arg_value
		elif OPT_PORT == arg_attr:
			if is_port_used(arg_value):
				return False, "设置站点属性失败，端口号%s已被使用!" % arg_value

		config.set(site_name, arg_attr, arg_value)
		config.write(open(WEB_CONF_FILE, 'w'))
		update_conf()

		return True, "设置站点属性成功."
	else:
		return False, "设置站点属性失败，站点%s不存在!"

# remove the web site specified
def remove_web_service(site_name):
	if DEFAULT_NAME == site_name:
		return False, "站点%s不允许删除！" % site_name
	check_default()
	config = ConfigParser.ConfigParser()
	config.read(WEB_CONF_FILE)
	if config.has_section(site_name) == True:
		ret = config.remove_section(site_name)
		if ret:
			config.write(open(WEB_CONF_FILE, 'w'))
			update_conf()
		else:
			return False, "删除站点%s失败!" % (site_name)

	return True, "删除站点%s成功." % (site_name)

# restore the default configuration of website
def restore_web_service():
	set_default()
