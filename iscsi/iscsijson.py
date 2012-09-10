#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libtarget import *
from libvolume import *
from liblun import *

import json

class UniReturnFormat:
	def __init__(self):
		self.rows = []
		self.total = 0

uni_dict = {"total":0, "rows": []}

if __name__ == '__main__':
	sl = []
	ss = iSCSIVolume()
	sl.append(ss.__dict__)
	tt = iSCSIVolume()
	sl.append(tt.__dict__)
	#uni_dict['rows'].append(ss.__dict__)
	uni_dict['rows'] = sl
	uni_dict['total'] = len(uni_dict['rows'])
	print json.dumps(uni_dict, sort_keys = False, indent = 2)
