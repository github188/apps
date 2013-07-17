#!/usr/bin/env sh

dev="$1"
filesystem="$2"

# set default filesystem to ext4
[ -z "$filesystem" ] && filesystem="ext4"

if [ "$filesystem" = "xfs" ]; then
	option="-f"
fi

ret_file="/tmp/format_ret.`basename $dev`"
{ mkfs."$filesystem" $option $dev 2>/dev/null; echo $? >$ret_file; } | tr-simple
ret=`cat $ret_file 2>/dev/null`
rm -f $ret_file
if [ "$ret" != "0" ]; then
	exit 1
fi
exit 0
