#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <signal.h>
#include <time.h>
#include <getopt.h>

#include "libdiskpw.h"

struct option longopts[] = {
	{"index",		1, NULL, 'i'},
	{"mode", 		1, NULL, 'm'},
	{"delay",		1, NULL, 'd'},
	{0,0,0,0}
};

int idx = 0;
int delay = 0;
int mode = POWER_RESET;
void usage()
{
	fprintf(stderr, "disk_reset --index|-i <idx> [--delay|-d <seconds>]\n"
		"disk_reset --help\n");
	exit(-1);
}

int parser(int argc, char *argv[])
{
	int c, freq = 0;
	while((c=getopt_long(argc, argv, "i:d:m:h", longopts, NULL))!=-1) {
		switch (c) {
		case 'i':
		if (optarg)
			idx = atoi(optarg);
		case 'd':
		if (optarg)
			delay = atoi(optarg);
		break;
		case 'm':
			if (!strcmp(optarg, "on")) {
				mode = POWER_ON;
			} else if (!strcmp(optarg, "off")) {
				mode = POWER_OFF;
			} else {
				fprintf(stderr, "mode invalid.\n");
				return -1;
			}
		break;
		case 'h':
		case -1:
		case '?':
			return -1;
		}
	}
	
	return 0;
}

int main(int argc, char *argv[])
{
	int i;

	if (parser(argc, argv) < 0) {
		usage();
		return -1;
	}
	
	if (idx > 16 || idx < 1) {
		fprintf(stderr, "input idx error.\n");
		return -1;
	}
	
	if (diskpw_init() < 0) {
		fprintf(stderr, "disk power init failed.\n");
		return -1;
	}

	if (delay > 16) {
		fprintf(stderr, "delay more than 16.\n");
		return -1;
	}

	if (diskpw_set(idx, mode, delay) < 0) {
		fprintf(stderr, "disk power set failed.\n");
		return -1;
	}
	return 0;
}
