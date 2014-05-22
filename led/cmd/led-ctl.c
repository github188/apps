#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <errno.h>

#include "libled.h"

char *const short_options = "s:gi:d:f:e:h";

enum LED_STATUS task;
enum LED_STATUS systask;
static int time;
static int disk_id = -1;
static int flags = 0; 		/* 检查是否为设置系统灯 */
static int getflag = 0;
struct option long_options[] = {
	{"sysled", 1, NULL, 's'},
	{"get", 0, NULL, 'g'},
	{"id", 1, NULL, 'i'},
	{"diskled", 1, NULL, 'd'},
	{"freq", 1, NULL, 'f'},
	{"expire", 1, NULL , 'e'},
	{"help", 0, NULL, 'h'},
	{0, 0, 0, 0}
};

void print_help(void)
{
	printf("led-ctl\n");
	printf("\t[--sysled|-s on|off|foff]\n");
	printf("\t[--get|-g]\n");
	printf("\t[--diskled|-d on|off|[blink --freq|-f fast|normal|slow] [--id|-i <disk_id>|<all>]]\n");
	printf("\t[--expire|-e <seconds>]\n");
	printf("\t[--help|-h]\n");
}

int led_getopt(int argc, char **argv)
{
	int c;

	while ((c = getopt_long(argc, (char *const*)argv, short_options,
					long_options, NULL)) != -1) {
		switch (c) {
			case 's':
				flags = 1;
				if (!strcmp(optarg, "on")) {
					systask = LED_ON;
					break;
				} else if (!strcmp(optarg, "off")) {
					systask = LED_OFF;
					break;
				} else if (!strcmp(optarg, "foff")) {
					systask = LED_FORCE_OFF;
					break;
				} else {
					fprintf(stderr, "sysled mode invalid.\n");
					return -1;
				}
			case 'g':
				getflag = 1;
				break;
			case 'i':
				if (!strcmp(optarg, "all")) {
					disk_id = -2;
				} else 
					disk_id = atoi(optarg);
				break;
			case 'd':
				if (!strcmp(optarg, "on")) {
					task = LED_ON;
					break;
				} else if (!strcmp(optarg, "off")) {
					task = LED_OFF;
					break;
				} else if (!strcmp(optarg, "blink")) {
					task = 0;
					break;
				}

				fprintf(stderr, "diskled mode invalid.\n");
				print_help();
				return -1;
			case 'f':
				if (!strcmp(optarg, "fast")) {
					task = LED_BLINK_FAST;
					break;
				} else if (!strcmp(optarg, "normal")) {
					task = LED_BLINK_NORMAL;
					break;
				} else if (!strcmp(optarg, "slow")) {
					task = LED_BLINK_SLOW;
					break;
				}
				fprintf(stderr, "freq arg invalid.\n");
				return -1;
			case 'e':
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

int parse_args(void)
{
	if (task != -1 && disk_id == -1) {
		fprintf(stderr, "diskid is null.\n");
		return -1;
	}
	if (task == 0) {
		fprintf(stderr, "blink freq invalid.\n");
		return -1;
	}
	return 0;
}



void do_get_work(int id)
{
	int i, j, count;
	enum LED_STATUS *sts;
	if (id == 0) {
		j = diskled_get_num();
	} else {
		j = 1;
	}
	sts = (enum LED_STATUS *)malloc(sizeof(enum LED_STATUS) * j);

	if (sts == NULL) {
		fprintf(stderr, "get status malloc failed.\n");
		return;
	}
	if (sysled_get(sts) < 0) {
		fprintf(stderr, "get sysled status failed.\n");
		return ;
	}
	count = sysled_get_count();
	if (sts[0] == LED_ON) {
		printf("sysled mode: on\ncount: %d\n", count);
	} else if(sts[0] == LED_OFF) {
		printf("sysled mode: off\ncount: %d\n", count);
	} else if (sts[0] == LED_FORCE_OFF) {
		printf("sysled mode: force off\ncount: %d\n", count);
	}else {
		printf("sysled mode:unknown\ncount: %d\n", count);
	}

	if (id == 0) {
		if (diskled_get_all(sts, j) < 0) {
			fprintf(stderr, "get diskled all status failed.\n");
			return;
		}
	} else {
		if (diskled_get(id, sts) < 0) {
			fprintf(stderr, "get diskled %d status failed.\n", id);
			return;
		}
	}

	for (i=0; i < j; i++) {
		switch (sts[i]) {
			case LED_ON:
				printf("diskled %d mode: on\n", i+1);
				break;
			case LED_OFF:
				printf("diskled %d mode: off\n", i+1);
				break;
			case LED_BLINK_FAST:
				printf("diskled %d mode: blink fast\n", i+1);
				break;
			case LED_BLINK_NORMAL:
				printf("diskled %d mode: blink normal\n", i+1);
				break;
			case LED_BLINK_SLOW:
				printf("diskled %d mode: blink slow\n", i+1);
				break;
			default:
				printf("diskled %d mode: unknown\n", i+1);
				break;
		}
	}

}

int main(int argc, char *argv[])
{
	int ret;

	if (argc < 2) {
		print_help();
		return -1;
	}
	task = -1;
	time = 0;

	if (led_getopt(argc, argv))
		return -1;
	if (parse_args() < 0)
		return -1;

	ret = led_init();
	if (ret == -1) {
		fprintf(stderr, "init led failed.\n");
		return -1;
	}

	if (flags) {
		if (sysled_set(systask) < 0) {
			fprintf(stderr, "set sysled failed.\n");
		}
	}

	if (task != -1) {
		if (disk_id == -2)  {
			diskled_set(0, task);
		} else if (disk_id != -1){
			diskled_set(disk_id, task);
		}
	}
	if (getflag) {
		do_get_work(0);
	}

	if (time == 0)
		return 0;
	else {
		sleep(time);
		if (flags) {
			sysled_set(LED_OFF);
		} 
		if (disk_id == -2) {
			diskled_set(0, LED_OFF);
		} else
			diskled_set(disk_id, LED_OFF);
	}

	return 0;
}
