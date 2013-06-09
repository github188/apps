#include "web-iface.h"
#include "common.h"

extern int g_debug;

int exec_new_cmd(int argc, char *argv[])
{
	int i;

	if (g_debug) {
		for (i=0;i<argc;i++)
			printf("argv[%d]: %s\n", i, argv[i]);
	}
	
	execvp(argv[0], &argv[0]);
	return -1;
}
