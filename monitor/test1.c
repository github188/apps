#include "sys-global.h"

int main(int argc, char *argv[])
{
	if (argc<2)
		return 0;
	/*
	printf("remove oldest file: %s\n",
		tmpfs_msg_remove_oldest(argv[1]));
	*/
	tmpfs_msg_sorted_unlink(tmpfs_msg_remove_oldest(argv[1]));
	return 0;
}
