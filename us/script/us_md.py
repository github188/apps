#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, commands, json
import getopt

from libdisk import *
from libmd import *

def do_create(argv):
    opts = ["name=", "level=", "strip=", "disk="]
    try:
        pair = getopt.getopt(argv, '', opts)
    except:
        return False,"参数非法"

    name = None
    level = None
    strip = None
    disks = None
    for opt,arg in pair[0]:
        if opt == "--name":
            name = arg
        elif opt == "--level":
            level = arg
        elif opt == "--strip":
            strip = arg
        elif opt == "--disk":
            disks = arg
    if name == None:
        return False,"未指定名称"
    if level == None:
        return False,"未指定级别"
    if strip == None:
        return False,"未指定条带大小"
    if disks == None:
        return False,"未指定磁盘槽位"
    return md_create(name, level, strip, disks)

def main(argv):
    ret = ""
    if len(argv) < 2:
        usage()

    cmd = argv[1]
    res = ""
    if cmd == "--list":
        if len(argv) >= 3:
            mdname = argv[2]
        else:
            mdname = None
        ret = md_info(mdname)
        json_dump(ret)
        res = None
    elif cmd == "--create":
        res = do_create(argv[2:])
    elif cmd == "--delete":
        if len(argv) < 3:
            usage()
        else:
            mdname = argv[2]
            res = md_del(mdname)
    else:
        usage()
    return res;

def usage():
    help_str="""
Usage:
	--create --name=<vg_name> --level=<0|1|5|6> --strip=<64|128|256> --disk='<disk-slot-list>'
        --delete <vg_name>
        --list [vg_name]
"""
    #return False,help_str
    print help_str
    sys.exit(-1)

if __name__ == "__main__":
    res = main(sys.argv)
    debug_status(res)
