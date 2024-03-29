#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
import sys
import os
import commands
import getopt
import json
os.chdir(os.path.dirname(sys.argv[0]))

from libsysconfig import *

class IArgs:
	def __init__(self):
		self.switch_set = ''
		self.switch_state = False
		self.hosts_set = ''
		self.hosts_state = False
		self.view_set = False
		self.date_set = False
		self.config_set = False
		self.output_set = 'this'
		self.output_state = False
		self.ntp_set = 'time.nist.gov'
		self.ntp_state = False
		self.now_set = ''
		self.interval_set = ''
		self.zone_set = 'Asia-Shanghai'
		self.zone_state = False
		self.interval_set = '1'
		self.unit_set = '1'

long_opt = ['switch=', 'hosts=', 'view', 'date', 'config', 'output=', 'ntp=', 'now=', 'zone=', 'interval=', 'unit=']

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', long_opt)
	except getopt.GetoptError, e:
		AUsage(e)

	iArgs = IArgs()
	for opt,arg in opts:

		if opt == '--switch':
			iArgs.switch_set = arg
			iArgs.switch_state = True
		elif opt == '--hosts':
			iArgs.hosts_set = arg
			iArgs.hosts_state = True
		elif opt == '--date':
			iArgs.date_set = True
		elif opt == '--output':
			iArgs.output_set = arg
			iArgs.output_state = True
		elif opt == '--config':
			iArgs.config_set = True
		elif opt == '--view':
			iArgs.view_set = True
		elif opt == '--ntp':
			iArgs.ntp_set = arg
			iArgs.ntp_state = True
		elif opt == '--now':
			iArgs.now_set = '"'+arg+'"'
		elif opt == '--zone':
			iArgs.zone_set = arg
			iArgs.zone_state = True
		elif opt == '--interval':
			iArgs.interval_set = arg
		elif opt == '--unit':
			iArgs.unit_set = arg

	if iArgs.switch_state == True:
		switch(iArgs)
	elif iArgs.hosts_state == True:
		hosts(iArgs)
	elif iArgs.view_set == True:
		hosts_view()
	elif iArgs.date_set == True:
		date(iArgs)
	else:
		AUsage()

if __name__ == '__main__':
	main()
