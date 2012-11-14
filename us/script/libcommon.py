#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, json

def list_files(path, reg):
    if not path.endswith("/"):
        path += "/"

    r = re.compile(reg)
    names = os.listdir(path)
    f = [path + x for x in names if r.match(x)]
    return f

def json_dump(obj):
    print json.dumps(obj, ensure_ascii=False, sort_keys=True, indent = 4)

def debug_status(res):
    if res:
        msg = {"status": res[0], "msg": res[1] }
        print json.dumps(msg, ensure_ascii=False)

