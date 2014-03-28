#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <errno.h>

#include "../daemon/common.h"
#include "libled.h"



char *const short_options = "s:i:d:f:e:h";
led_task_t task;
led_task_t systask;
static int disk_id = DISK_ID_NONE;
static int flags = 0; 		/* 检查是否为设置系统灯 */
struct option long_options[] = {
	{"sysled", 1, NULL, 's'},
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
	printf("\t[--sysled|-s on|off]\n");
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
					systask.mode = MODE_ON;
				} else if (!strcmp(optarg, "off")) {
					systask.mode = MODE_OFF;
				} else {
					systask.mode = MODE_OFF;
				}
				break;
			case 'i':
				if (!strcmp(optarg, "all")) {
					disk_id = DISK_ID_ALL;
				} else 
					disk_id = atoi(optarg);
				break;
			case 'd':
				if (!strcmp(optarg, "on")) {
					task.mode = MODE_ON;
					break;
				}
				if (!strcmp(optarg, "off")) {
					task.mode = MODE_OFF;
					break;
				}
				if (!strcmp(optarg, "blink")) {
					task.mode = MODE_BLINK;
					break;
				}

				fprintf(stderr, "diskled invalid.\n");
				print_help();
				return -1;
			case 'f':
				if (!strcmp(optarg, "fast")) {
					task.freq = FREQ_FAST;
					break;
				}
				if (!strcmp(optarg, "normal")) {
					task.freq = FREQ_NORMAL;
					break;
				}
				if (!strcmp(optarg, "slow")) {
					task.freq = FREQ_SLOW;
					break;
				}
				fprintf(stderr, "freq arg invalid.\n");
				return -1;
			case 'e':
				task.time = atol(optarg) * 1000;
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
	if (flags == 0 && disk_id == DISK_ID_NONE) {
		fprintf(stderr, "please input disk id.\n");
		return -1;
	}
	if (task.mode == MODE_BLINK) {
		if (task.freq != FREQ_FAST && task.freq != FREQ_NORMAL
				&& task.freq != FREQ_SLOW) {
			fprintf(stderr, "blink freq invalid.\n");
			return -1;
		}
	}
#ifdef _DEBUG	
	printf("disk_id:%d, mode:%d, time:%ld, freq:%d, count:%d\n",
			disk_id, task.mode, task.time, task.freq, task.count);
#endif
	return 0;

}
void do_work(int i)
{
	if (task.mode & MODE_ON) {
		if (diskled_set(i, LED_ON) < 0) {
			fprintf(stderr, "led %d on failed.\n", i);
		}
	} else if (task.mode & MODE_OFF) {
		if (diskled_set(i, LED_OFF) < 0) {
			fprintf(stderr, "led %d off failed.\n", i);
		}
	} else if (task.mode & MODE_BLINK) {
		if (task.freq & FREQ_FAST) {
			if (diskled_set(i, LED_BLINK_FAST) < 0) {
				fprintf(stderr, "led %d blink failed.\n", i);
			}
		} else if (task.freq & FREQ_NORMAL) {
			if (diskled_set(i, LED_BLINK_NORMAL) < 0) {
				fprintf(stderr, "led %d blink failed.\n", i);
			}
		} else if (task.freq & FREQ_SLOW) {
			if (diskled_set(i, LED_BLINK_SLOW) < 0) {
				fprintf(stderr, "led %d blink failed.\n", i);
			}
		}
	}

}


int main(int argc, char *argv[])
{
	int ret;

	if (argc < 3) {
		print_help();
		return -1;
	}
	systask.mode = MODE_OFF;
	task.freq = FREQ_NONE;
	task.mode = MODE_OFF;
	task.time = TIME_FOREVER;

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
		if (systask.mode & MODE_ON)
			sysled_set(LED_ON);
		else if (systask.mode & MODE_OFF)
			sysled_set(LED_OFF);
	}
	if (disk_id == DISK_ID_NONE )
		return 0;

	if (disk_id == DISK_ID_ALL) 
		do_work(0);
	else
		do_work(disk_id);


	if (task.time == TIME_FOREVER)
		return 0;
	else {
		sleep(task.time/1000);
		if (disk_id == DISK_ID_ALL) {
			diskled_set(0, LED_OFF);
		} else
			diskled_set(disk_id, LED_OFF);
	}

	return 0;
}
