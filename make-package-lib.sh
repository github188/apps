#!/usr/bin/env bash
set -e

make clean
make

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

TMP_DIR_LED=$TMP_DIR/jw-lib/led
rm -fr $TMP_DIR_LED
mkdir -p $TMP_DIR_LED
cp led/cmd/libled.[has]* led/cmd/libdiskpw.[has]* led/cmd/led-ctl.c led/cmd/disk_reset.c \
 led/daemon/led-ctl-daemon led/readme.txt $TMP_DIR_LED/

TMP_DIR_BUZZER=$TMP_DIR/jw-lib/buzzer
rm -fr $TMP_DIR_BUZZER
mkdir -p $TMP_DIR_BUZZER
cp buzzer/cmd/libbuzzer.[has]* buzzer/cmd/buzzer-ctl.c buzzer/daemon/buzzer-ctl-daemon \
buzzer/readme.txt $TMP_DIR_BUZZER/

TMP_DIR_WATCHDOG=$TMP_DIR/jw-lib/watchdog
rm -fr $TMP_DIR_WATCHDOG
mkdir -p $TMP_DIR_WATCHDOG
cp watchdog/libwatchdog.[has]* watchdog/watchdog.c watchdog/readme.txt $TMP_DIR_WATCHDOG/

cd $TMP_DIR
tar jcf $PKG ./*
cd - >/dev/null
rm -rf $TMP_DIR

echo ""
echo -e "\033[0;35;1mPackaged completed successfully.\033[0m"
echo ""

