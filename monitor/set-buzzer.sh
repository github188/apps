#!/usr/bin/env sh

ALARM_DIR="/tmp/jw/alarm"
BUZZER_BIN="/usr/local/bin/buzzer"

case "$1" in
	"on")
		ps au | grep buzzer | grep -v grep >/dev/null
		if [ $? -ne 0 ]; then
			$BUZZER_BIN &
			touch $ALARM_DIR/buzzer
		fi
		;;
	"off")
		$BUZZER_BIN 0
		killall $(basename $BUZZER_BIN) >/dev/null
		[ $? -ne 0 ] && exit 1
		rm -f $ALARM_DIR/buzzer
		;;
	*)
		echo "$(basename $0) <on|off>" && exit 1
		;;
esac

exit 0
