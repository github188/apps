#include "web-iface.h"
#include "common.h"

int iscsi_main(int argc, char *argv[])
{
	int i;
	char cmd[1024];

	strcpy(cmd, "iscsi");
	for (i=1; i<argc; i++)
	{
		strcat(cmd, " ");
		strcat(cmd, argv[i]);
	}

	return system(cmd);
}
