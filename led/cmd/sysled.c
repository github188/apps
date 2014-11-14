/*
 *更新时间: < 修改人[liyunteng] 2014/10/21 11:15:13 >
 */
#include <stdio.h>
#include <unistd.h>
#include <error.h>
#include <string.h>

#include "../daemon/sysled.h"

#define ARGIVALID -1


void print_help(void)
{
	fprintf(stderr, "Usage: sas_sysled <on|off>\n");
}

int main(int argc, char *argv[])
{
	if (argc != 2) {
		print_help();
		return ARGIVALID;
	}
	if (!strcmp(argv[1],"on")) {
		return sb_gpio28_set(true);
	}

	if (!strcmp(argv[1], "off")) {
		return sb_gpio28_set(false);
	}

	return ARGIVALID;
}





