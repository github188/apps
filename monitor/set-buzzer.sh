#!/usr/bin/env sh

ALARM_DIR="/tmp/jw/alarm"
BUZZER_BIN="/usr/local/bin/buzzer"

case "$1" in
	"on")
		$BUZZER_BIN &
		touch $ALARM_DIR/buzzer
		;;
	"off")
		$BUZZER_BIN 0
		killall $(basename $BUZZER_BIN)
		[ $? -ne 0 ] && exit 1
		rm -f $ALARM_DIR/buzzer
		;;
	*)
		echo "$(basename $0) <on|off>" && exit 1
		;;
esac

exit 0
