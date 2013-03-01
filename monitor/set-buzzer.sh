#!/bin/bash

BUZZER_BIN="/usr/local/bin/buzzer"

case "$1" in
	"on")
		$BUZZER_BIN &
		;;
	"off")
		>/dev/null 2>&1 killall $(basename $BUZZER_BIN)
		$BUZZER_BIN 0
		;;
	*)
		echo "$(basename $0) <on|off>" && exit 1
		;;
esac

exit 0
