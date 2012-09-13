#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import commands, re, os
from libdisk import *

def __def_post(p):
    if len(p) == 0:
        return ""
    return p[0]

def __level_post(p):
    if len(p) == 0:
        return "NaN"
    level = p[0].lower().replace("raid", "")
    if level == "linear":
        level = "JBOD"
    return level

def __chunk_post(p):
    if len(p) == 0:
        return ""
    chunk = p[0].lower().replace("k", "")
    return chunk

def __state_post(p):
    if len(p) == 0:
        return "Unknown"
    state = p[0]
    if state.find("degraded") != -1 :
        if state.find("recovering"):
            return "rebuild"
        return "degraded"
    elif state.find("FAILED") != -1:
        return "fail"
    elif state.find("resyncing") != -1:
        return "initial"
    else:
        return "normal"

def __name_post(p):
    if len(p) == 0:
        return "Unknown"
    name=p[0];
    return name.split(":")[0]

def __disk_post(p):
    if len(p) == 0:
        return ();
    slots = []
    for disk in p:
        name = disk[1]
        slots.append(disk_slot(name))
    return slots

def __find_attr(output, reg, post=__def_post):
    p = re.findall(reg, output)
    return post(p)

def __md_fill_attr(str):
    attr = {}
    attr["name"] = __find_attr(str, "Name : (.*)", __name_post)
    attr["raid_level"] = __find_attr(str, "Raid Level : (.*)", __level_post)
    attr["raid_state"] = __find_attr(str, "State : (.*)", __state_post)
    attr["raid_strip"] = __find_attr(str, "Chunk Size : ([0-9]+[KMG])",
                                     __chunk_post)
    attr["raid_rebuild"] = __find_attr(str, "Rebuild Status : ([0-9])\%");
    attr["capacity"] = int(__find_attr(str, "Array Size : ([0-9]+)"))
    used_capacity = int(__find_attr(str, "Used Dev Size : ([0-9]+)"))
    attr["remain"] = int(attr["capacity"]) - used_capacity
    attr["disk_cnt"] = int(__find_attr(str, "Total Devices : ([0-9]+)"))
    attr["disk_list"] = __find_attr(str, "([0-9]+\s*){4}.*(/dev/.+)",
                                    __disk_post)

    #注：需要用户卷完成后，该位才有效
    return attr

def mddev_get_attr(mddev):
    md_attr = {}
    cmd = "mdadm -D %s" % mddev
    sts,output = commands.getstatusoutput(cmd)
    if (sts != 0) :
        return None
    md_attr = __md_fill_attr(output)
    # add md dev for create udv
    if md_attr:
	    md_attr["dev"] = mddev
    return md_attr

def md_list_mddevs():
    return list_files("/dev", "md[0-9]+")

def md_find_free_mddev():
    mddevs = md_list_mddevs()
    for i in xrange(1, 255):
        md = "/dev/md%u" % i
        if not (md in mddevs):
            return md
    return None

def mddev_get_disks(mddev):
    reg = re.compile(r"(sd[a-z]+)\[[0-9]+\]")
    cmd = "cat /proc/mdstat |grep %s 2>/dev/null" % (os.path.basename(mddev))
    sts,out = commands.getstatusoutput(cmd)
    if sts != 0:
        return []
    disks = reg.findall(out)
    rdisks = ["/dev/" + x for x in disks]

    return rdisks

def md_get_disks(mdname):
    mddev = get_mddev(mdname)
    if mddev == None:
        return []
    return mddev_get_disks(mddev)

def md_stop(mddev):
    cmd = "mdadm -S %s >/dev/null 2>&1" % mddev
    sts, out = commands.getstatusoutput(cmd)
    return sts

def md_create(mdname, level, chunk, slots):
    #create raid
    mddev = md_find_free_mddev()
    if mddev == None:
        return False,"没有空闲的RAID槽位"
    devs,failed = disks_from_slot(slots)
    if len(devs) == 0:
        return False, "没有磁盘"
    dev_list = " ".join(devs)
    cmd = " >/dev/null 2>&1 mdadm -CR %s -l %s -c %s -n %u %s --homehost=%s -f" % (mddev, level, chunk, len(devs), dev_list, mdname)
    if level in ('3', '4', '5', '6', '10', '50', '60'):
        cmd += " --bitmap=internal"
    sts,out = commands.getstatusoutput(cmd)
    disk_slot_update(slots)
    if sts != 0 :
        return False, "创建卷组失败"
    return True, "创建卷组成功"

def md_del(mdname):
    mddev = md_get_mddev(mdname)
    if (mddev == None):
        return "Can't find %s" % mdname
    disks = mddev_get_disks(mddev)
    sts = md_stop(mddev)
    if sts != 0:
        return False,"停止%s失败" % mdname
    res = set_disks_free(disks)
    if res != "":
        return False,"清除磁盘信息失败，请手动清除"
    return True,"删除卷组成功"

def md_info_mddevs(mddevs=None):
    if (mddevs == None):
        mddevs = md_list_mddevs()
    md_no = len(mddevs)
    md_attrs = [];
    for mddev in mddevs:
        attr = mddev_get_attr(mddev)
        if (attr):
            md_attrs.append(attr)
    return {"total": md_no, "rows": md_attrs}

def md_info(mdname=None):
    if (mdname == None):
        mddevs = None;
    else:
        mddevs = [md_get_mddev(mdname)];
    return md_info_mddevs(mddevs);

if __name__ == "__main__":
    #test
    import sys
    if len(sys.argv) >= 2:
        md_name = sys.argv[1]
    else:
        md_name = "debianx"

    print "Test none:"
    print md_info(None)
    print md_info("ddd")
    print md_info(md_name)
