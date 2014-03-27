#!/usr/bin/env python2.6
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

# module  event            param
# ----------------------------------------
#   disk  online
#         offline          disk-slot
#         fail             disk-slot
#         spare            disk-slot
#         smart-health     disk-slot
#     vg  add              disk-slot-list
#         remove           disk-slot-list
#         normal           disk-slot-list
#         degrade          disk-slot-list
#         fail             disk-slot-list
#         initial          disk-slot-list
#         rebuild          disk-slot-list
#  power  fail
def sysmon_event(module, event, param, msg):
	_ev = ev()
	_ev.module = module
	_ev.event = event
	_ev.param = param
	_ev.msg = msg

	ev_msg = json.dumps(_ev.__dict__)

	try:
		client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
		client.connect(SYSMON_ADDR)
		client.send(ev_msg)
		client.close()
	except:
		return False
	return True

if __name__ == '__main__':
	sysmon_event('disk', 'online', '0:1', '磁盘上线')
