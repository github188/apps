#include "web-iface.h"
#include "common.h"

int external_main(int argc, char *argv[])
{
	int i;
	char tmp[32], *p;
	char cmd[1024];

	strcpy(cmd, "sys-manager-py");
	for (i=0; i<argc; i++)
	{
		if (!strncmp(argv[i], "--disk=", 7))
		{
			p = strtok(argv[i], "--disk=");
			strcpy(tmp, " --disk=\'");
			strcat(tmp, p);
			strcat(tmp, "\'");
		}
		else
			sprintf(tmp, " %s", argv[i]);
		strcat(cmd, tmp);
	}

	return system(cmd);
}
