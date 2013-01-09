#include "sys-global.h"

/*extern*/ sys_global_t gconf;

void sys_global_init()
{
	gconf.tmpfs = false;
	gconf.info_size = 10;
	gconf.warning_size = 10;
	gconf.error_size = 10;
}

void dump_sys_global()
{
	puts("--------- global ---------");
	if (gconf.tmpfs)
		puts("tmpfs: true");
	else
		puts("tmpfs: false");
	puts("msg_buff_size:");
	printf("  info: %d\n", gconf.info_size);
	printf("  warning: %d\n", gconf.warning_size);
	printf("  error: %d\n", gconf.error_size);
}
