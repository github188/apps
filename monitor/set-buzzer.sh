#!/usr/bin/env sh

BUZZER_FILE="/tmp/jw/alarm/buzzer"
BUZZER_BIN="/usr/local/bin/buzzer"

case "$1" in
	"on")
		if [ ! -f $BUZZER_FILE ]; then
			$BUZZER_BIN &
			touch $BUZZER_FILE
		fi
		;;
	"off")
		$BUZZER_BIN 0
		>/dev/null 2>&1 killall $(basename $BUZZER_BIN)
		[ $? -ne 0 ] && exit 1
		rm -f $BUZZER_FILE
		;;
	*)
		echo "$(basename $0) <on|off>" && exit 1
		;;
esac

exit 0
