#include <stdio.h>
#include "../pic_ctl/pic_ctl.h"

struct pic_ver
{
	uint32_t minor:8;
	uint32_t major:8;
	uint32_t rev:16;
};

int main()
{
	uint32_t version;

	if (!pic_get_version(&version))
	{
		struct pic_ver *p = (struct pic_ver*)&version;
		printf("Version: %d.%d\n", p->major, p->minor);
		return 0;
	}

	printf("Can't get version!\n");
	return -1;
}
