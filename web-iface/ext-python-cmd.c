#include "web-iface.h"
#include "common.h"

extern int g_debug;

int python_cmd_main(int argc, char *argv[])
{
	int i;
	char cmd[1024];

	if (g_debug)
	{
		for (i=0;i<argc;i++)
			printf("argv[%d]: %s\n", i, argv[i]);
	}

	strcpy(cmd, argv[0]);
	for (i=1; i<argc; i++)
	{
		strcat(cmd, " ");
		strcat(cmd, argv[i]);
	}

	return system(cmd);
}
