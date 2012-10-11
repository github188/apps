#!/usr/bin/env sh

dev="$1"
filesystem="$2"

# set default filesystem to ext4
[ -z "$filesystem" ] && filesystem="ext4"

mkfs."$filesystem" $dev | tr-simple

