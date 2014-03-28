#!/usr/bin/env bash
set -e

cd led-ctl
make clean
make only-interface=1
cd - >/dev/null

cd buzzer-ctl
make clean
make only-interface=1
cd - >/dev/null

if [ `arch` = "x86_64" ]; then
	ARCH="64bit"
else
	ARCH="32bit"
fi

PKG="/tmp/jw-lib-${ARCH}.tar.bz2"
rm -fr $PKG_

TMP_DIR=/tmp/.jw-lib
rm -fr $TMP_DIR
mkdir -p $TMP_DIR

TMP_DIR_LED=$TMP_DIR/jw-lib/led-ctl
rm -fr $TMP_DIR_LED
mkdir -p $TMP_DIR_LED
cp led-ctl/cmd/libled.h led-ctl/cmd/libled.a $TMP_DIR_LED/

TMP_DIR_BUZZER=$TMP_DIR/jw-lib/buzzer-ctl
rm -fr $TMP_DIR_BUZZER
mkdir -p $TMP_DIR_BUZZER
cp buzzer-ctl/cmd/libbuzzer.h buzzer-ctl/cmd/libbuzzer.a $TMP_DIR_BUZZER/

cd $TMP_DIR
tar jcf $PKG ./*
cd - >/dev/null
rm -rf $TMP_DIR

echo ""
echo -e "\033[0;35;1mPackaged completed successfully.\033[0m"
echo ""