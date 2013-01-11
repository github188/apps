#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import json

SYSMON_ADDR = "/tmp/.sys-mon-socket-do-not-remove"

class ev:
	def __init__(self):
		self.module = ''
		self.event = ''
		self.param = ''
		self.msg = ''

def sysmon_event(module, event, param, msg):
	_ev = ev()
	_ev.module = module
	_ev.event = event
	_ev.param = param
	_ev.msg = msg

	ev_msg = json.dumps(_ev.__dict__)

	client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
	client.connect(SYSMON_ADDR)
	client.send(ev_msg)
	client.close()

if __name__ == '__main__':
	sysmon_event('disk', 'online', '0:1', '磁盘上线')
