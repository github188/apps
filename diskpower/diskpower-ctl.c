#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include <string.h>
#include "diskpower.h"


static int id;
static int mode;
static int time;
char *const short_options = "i:m:r:h";
struct option long_options[] = {
	{"id", 1, NULL, 'i'},
	{"mode", 1, NULL, 'm'},
	{"reset", 1, NULL, 'r'},
	{"help", 0, NULL, 'h'},
	{0, 0, 0, 0},
};

void print_help(void)
{
	fprintf(stderr, "diskpower-ctl:\n");
	fprintf(stderr, "\t--id|-i <1-16> --mode|-m on|off\n");
	fprintf(stderr, "\t--id|-i <1-16> --reset|-r <delayTimer>\n");
	fprintf(stderr, "\t--help|-h\n");
}
int parse_args(int argc, char **argv)
{
	int c;

	while ((c = getopt_long(argc, (char *const *)argv,  short_options,
				long_options, NULL)) != -1) {
		switch (c) {
		case 'i':
			id = atoi(optarg);
			break;
		case 'm':
			if (!strcmp(optarg, "on")) {
				mode = I2C_DISKPW_ON;
			} else if (!strcmp(optarg, "off")) {
				mode = I2C_DISKPW_OFF;
			} else {
				fprintf(stderr, "mode invalid.\n");
				return -1;
			}
			break;
		case 'r':
			time = atoi(optarg);
			break;
		case 'h':
			print_help();
			return -1;
		default:
			print_help();
			return -1;
		}
	}
	return 0;
}
	

int main(int argc, char *argv[])
{
	int old = 0;
	int new = 0;

	if (argc < 2)  {
		print_help();
		return -1;
	}
	
	if (parse_args(argc, argv) < 0) {
		return -1;
	}	
	if (id <= 0 || id > 16 ) {
		print_help();
		return -1;
	}

	if (i2c_init_diskpw() < 0) {
		fprintf(stderr, "i2c init failed.\n");
		return -1;
	}

	old = i2c_read_diskpw();
	if (old < 0) {
		fprintf(stderr, "i2c read failed.\n");
		return -1;
	}

	if (mode == I2C_DISKPW_ON)
		new = old | (1 << (id-1));
	else
		new = old & ~(1 << (id-1));

	if (i2c_write_diskpw(new) < 0) {
		fprintf(stderr, "i2c write failed.\n");
		return -1;
	}
	
	if (time) {
		new = old & ~(1 << (id-1));
		if (i2c_write_diskpw(new) < 0) {
			fprintf(stderr, "i2c reset failed.\n");
			return -1;
		}
		sleep(time);
		if (i2c_write_diskpw(old) < 0) {
			fprintf(stderr, "i2c reset failed.\n");
			return -1;
		}
	}
	return 0;
	
}
