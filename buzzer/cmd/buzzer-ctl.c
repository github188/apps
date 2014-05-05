#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <errno.h>

#include "libbuzzer.h"


char *const short_options = "s:gh";
enum BUZZER_STATUS systask;
int getflag=0;
struct option long_options[] = {
	{"set", 1, NULL, 's'},
	{"get", 0, NULL, 'g'},
	{"help", 0, NULL, 'h'},
	{0, 0, 0, 0}
};

void print_help(void)
{
	printf("buzzer-ctl:\n");
	printf("\t[--set|-s on|off|foff]\n");
	printf("\t[--get|-g]\n");
	printf("\t[--help|-h]\n");
}

int buzzer_getopt(int argc, char **argv)
{
	int c;

	while ((c = getopt_long(argc, (char *const*)argv, short_options,
				long_options, NULL)) != -1) {
		switch (c) {
		case 's':
			if (!strcmp(optarg, "on")) {
				systask = BUZZER_ON;
			} else if (!strcmp(optarg, "off")) {
				systask = BUZZER_OFF;
			} else if (!strcmp(optarg, "foff")){
				systask = BUZZER_FORCE_OFF;
			} else {
				fprintf(stderr, "ivalid mode\n");
				exit (-1);
			}
			break;
		case 'g':
			getflag = 1;
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

	if (buzzer_getopt(argc, argv))
		return -1;

	ret = buzzer_init();
	if (ret == -1) {
		fprintf(stderr, "init buzzer failed.\n");
		return -1;
	}
	buzzer_set(systask);
	/* if (systask.mode & BUZZER_ON) */
	/* 	buzzer_set(BUZZER_ON); */
	/* else if (systask.mode & BUZZER_OFF) */
	/* 	buzzer_set(BUZZER_OFF); */
	/* else if (systask.mode & BUZZER_FORCE_OFF) */
	/* 	buzzer_set(BUZZER_FORCE_OFF); */

	if (getflag) {
		enum BUZZER_STATUS sts;
		int count;
		ret = buzzer_get(&sts);
		count = buzzer_get_count();
		if (ret < 0) {
			fprintf(stderr, "get buzzer status failed.\n");
			return -1;
		}

		switch (sts) {
		case BUZZER_ON:
			printf("buzzer status: on\ncount: %d\n", count);
			break;
		case BUZZER_OFF:
			printf("buzzer status: off\ncount: %d\n", count);
			break;
		case BUZZER_FORCE_OFF:
			printf("buzzer status: force off\ncount: %d\n", count);
			break;
		default:
			printf("buzzer status: unknown\n");
			break;
		}

	}

	return 0;
}
