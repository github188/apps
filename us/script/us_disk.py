#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, commands

from libdisk import *
from libmd import *

#argv: namd opt <slot>
def main(argv):
    if len(argv) < 2:
        return usage()

    cmd = argv[1]
    if cmd == "info":
        cmd = "--list"
        argv[1] = cmd
    res = ""

    if cmd == "--list" or cmd == "name" or cmd == "slot" or cmd == "--get-detail":
        # pass through to us_cmd
        cmd_us = "us_cmd disk " + " ".join(argv[1:])
        sts,output = commands.getstatusoutput(cmd_us)
        res = None
        if (sts == 0):
            print output;
        else:
            print json.dumps({"total": 0, "rows":[]})
            #是否需要返回错误信息
        #else:
        #res = output;
    elif cmd == "--set-spare" :
        if len(argv) < 4:
            usage()
        mdname = argv[2];
        slots = argv[3];
        res = set_spare(mdname, slots)
    elif cmd == "--set-free":
        if (len(argv)) < 3:
            usage()
        slots = argv[2]
        res = set_slots_free(slots)
    else:
        res = usage()
    return res

def usage():
    help_str="""
Usage:
        --list [slot]
        --get-detail <slot>
        --set-spare md_name <slots>
        --set-free <slots>
        info [slot]
        name <slot>
        slot <name>
"""
    return False,help_str

if __name__ == "__main__":
    res = main(sys.argv)
    debug_status(res)
