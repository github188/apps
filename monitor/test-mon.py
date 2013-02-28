#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from libsysmon import sysmon_event

disk_slot = 'disk=0:1'
#disk_slots = "disks=[0:1, 0:2, 0:3, 0:4, 0:5]"
disk_slots = "disks=0:1,0:2,0:3,0:4,0:5"

if __name__ == '__main__':
	args = len(sys.argv)
	if args < 3:
		print 'no args'
		sys.exit(1)

	module = sys.argv[1]
	event = sys.argv[2]

	print 'raise: %s %s' % (module, event)
	if 'disk' == module:
		sysmon_event(module, event, disk_slot, '磁盘事件')
	else:
		sysmon_event(module, event, disk_slots, '磁盘事件')

