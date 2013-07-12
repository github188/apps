#!/usr/bin/env sh

dev="$1"
filesystem="$2"

# set default filesystem to ext4
[ -z "$filesystem" ] && filesystem="ext4"

if [ "$filesystem" = "xfs" ]; then
	option="-f"
fi

ret=1
error_log_file="/tmp/format_errlog.`basename $dev`"
mkfs."$filesystem" $option $dev 2>$error_log_file | tr-simple
sed -i /"mke2fs"/d $error_log_file
if [ ! -s $error_log_file ]; then
	ret=0
fi
rm -rf $error_log_file
exit $ret
