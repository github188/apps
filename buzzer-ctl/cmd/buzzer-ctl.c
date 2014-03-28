#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <errno.h>

#include "../daemon/common.h"
#include "libbuzzer.h"


char *const short_options = "b:h";
buzzer_task_t systask;
struct option long_options[] = {
	{"buzzer", 1, NULL, 'b'},
	{"help", 0, NULL, 'h'},
	{0, 0, 0, 0}
};

void print_help(void)
{
	printf("buzzer-ctl:\n");
	printf("\t[--buzzer|-b on|off|foff]\n");
	printf("\t[--help|-h]\n");
}

int buzzer_getopt(int argc, char **argv)
{
	int c;

	while ((c = getopt_long(argc, (char *const*)argv, short_options,
					long_options, NULL)) != -1) {
		switch (c) {
			case 'b':
				if (!strcmp(optarg, "on")) {
					systask.mode = MODE_ON;
				} else if (!strcmp(optarg, "off")) {
					systask.mode = MODE_OFF;
				} else if (!strcmp(optarg, "foff")){
					systask.mode = MODE_FORCE_OFF;
				} else {
					systask.mode = MODE_OFF;
				}
				break;
			case 'h':
				print_help();
				return -1;
			default:
				return -1;
		}
	}
	return 0;
}

int main(int argc, char *argv[])
{
	int ret;

	if (argc < 2) {
		print_help();
		return -1;
	}
	systask.mode = MODE_OFF;
	
	if (buzzer_getopt(argc, argv))
		return -1;

	ret = buzzer_init();
	if (ret == -1) {
		fprintf(stderr, "init buzzer failed.\n");
		return -1;
	}

		if (systask.mode & MODE_ON)
			buzzer_set(BUZZER_ON);
		else if (systask.mode & MODE_OFF)
			buzzer_set(BUZZER_OFF);
		else if (systask.mode & MODE_FORCE_OFF)
			buzzer_set(BUZZER_FORCE_OFF);

	return 0;
}
