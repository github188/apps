#include "web-iface.h"
#include "common.h"

int python_cmd_main(int argc, char *argv[])
{
	int i;
	char cmd[1024];

	strcpy(cmd, argv[0]);
	for (i=1; i<argc; i++)
	{
		strcat(cmd, " ");
		strcat(cmd, argv[i]);
	}

	return system(cmd);
}
