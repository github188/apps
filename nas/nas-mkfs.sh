#!/usr/bin/env sh

dev="$1"
filesystem="$2"

# set default filesystem to ext4
[ -z "$filesystem" ] && filesystem="ext4"

if [ "$filesystem" = "xfs" ]; then
	option="-f"
fi

2>/dev/null mkfs."$filesystem" $option $dev | tr-simple

