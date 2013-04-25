#include <stdio.h>
#include "sys-global.h"

sys_global_t gconf;

void sys_global_init()
{
	gconf.tmpfs = false;
	gconf.info_size = 10;
	gconf.warning_size = 10;
	gconf.error_size = 10;
	gconf.power_cnt = 1;
}

void dump_sys_global()
{
	puts("-------------- dump global ---------------");
	if (gconf.tmpfs)
		puts("tmpfs: true");
	else
		puts("tmpfs: false");
	puts("msg_buff_size:");
	printf("\tinfo: %d\n", gconf.info_size);
	printf("\twarning: %d\n", gconf.warning_size);
	printf("\terror: %d\n", gconf.error_size);
	printf("power_cnt: %d\n", gconf.power_cnt);
}
