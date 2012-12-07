#!/usr/bin/env sh

clean="$1"

VERSION_TEMP="version-template.c"
VERSION_FILE="version.c"

get_hostname()
{
	echo "$(hostname | tr '\n' '\0')"
}

get_ipaddr()
{
	echo "$(sudo ifconfig eth0 | grep 'inet addr' | awk -F':' '{print $2}' | awk '{print $1}' | tr '\n' '\0')"
}

get_git_branch()
{
	echo "$(git branch | grep '*' | awk '{print $NF}' | tr '\n' '\0')"
}

get_git_commid()
{
	echo "$(git log | col -b | head -n 1 | awk '{print $NF}' | tr '\n' '\0')"
}

get_datetime()
{
	echo "$(date | tr '\n' '\0')"
}

check_key()
{
	local key="$1"

	[ -z "$key" ] && echo "nonexist" && return

	if `grep "$key" "$VERSION_TEMP" > /dev/null`; then
		echo "exist"
	else
		echo "nonexist"
	fi
}

update_key()
{
	local key="$1"
	local value="$2"

	[ -z "$key" ] && echo "key not set!" && exit 1
	[ -z "$value" ] && echo "value not set!" && exit 1

	if [ -f "$VERSION_FILE" ]; then
		sed "s/#define $key/#define $key \"$value\"/" $VERSION_FILE > .tmp_version_file
		mv .tmp_version_file $VERSION_FILE
	elif [ -f "$VERSION_TEMP" ]; then
		sed "s/#define $key/#define $key \"$value\"/" $VERSION_TEMP > $VERSION_FILE
	else
		echo "$VERSION_TEMP AND $VERSION_FILE  not exist!"
		exit 1
	fi

}

error_exit()
{
	msg="$1"
	echo "$msg key not exist check $VERSION_TEMP"
	exit 1
}

[ "$clean" = "clean" ] && rm -f "$VERSION_FILE" && exit 0

if [ ! -f "$VERSION_TEMP" ]; then
	echo "FAIL, $VERSION_TEMP not found!"
	exit 1
fi

[ $(check_key "HOST") != "exist" ] && error_exist "HOST"
[ $(check_key "IPADDR") != "exist" ] && error_exist "IPADDR"
[ $(check_key "GIT_BRANCH") != "exist" ] && error_exist "GIT_BRANCH"
[ $(check_key "GIT_COMMID") != "exist" ] && error_exist "GIT_COMMID"
[ $(check_key "DATETIME") != "exist" ] && error_exist "DATETIME"

rm -f "$VERSION_FILE"

update_key "HOST" "$(get_hostname)"
update_key "IPADDR" "$(get_ipaddr)"
update_key "GIT_BRANCH" "$(get_git_branch)"
update_key "GIT_COMMID" "$(get_git_commid)"
update_key "DATETIME" "$(get_datetime)"

