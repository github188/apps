#!/usr/bin/env python
# -*- coding: utf-8 -*-

def usage():
	print """
iscsi --target --list [<target_name>]
               --modify --attribute <key> --value <value>
	       --add <target_name>
	       --remove <target_name>

      --volume --list [<iscs_volume_name>]
               --add --udv <udv_name> --block-size <size> --read-only <enable|disable> --nv-cache <enable|disable>
	       --remove <iscsi_volume_name>

      --lun --list [--target <name>]
            --map --target <target_name> --volume <volume_name> --lun-id <id> --read-only <enable|disable>
	    --unmapp <lun_id>

      --session --list [<session_id>]
                --force-close <session_id>
"""

def iscsi_main():
	return

if __name__ == "__main__":
	usage()
