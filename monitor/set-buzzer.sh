#!/bin/bash

ALARM_DIR="/tmp/.sys-mon/alarm"
BUZZER_BIN="/usr/local/bin/buzzer"

case "$1" in
	"on")
		if [ -f "$ALARM_DIR"/buzzer ]; then
			exit 0
		fi
		$BUZZER_BIN &
		mkdir -p "$ALARM_DIR" >/dev/null 2>&1
		touch "$ALARM_DIR"/buzzer >/dev/null 2>&1
		;;
	"off")
		>/dev/null 2>&1 killall $(basename $BUZZER_BIN)
		$BUZZER_BIN 0
		rm -fr "$ALARM_DIR"/buzzer >/dev/null 2>&1
		;;
	*)
		echo "$(basename $0) <on|off>" && exit 1
		;;
esac

exit 0
