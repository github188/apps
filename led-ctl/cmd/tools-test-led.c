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



char *l_opt_arg;
char *const short_options = "i:s:d:h";
led_task_t task;
led_task_t systask;
static int disk_id = DISK_ID_NONE;
static int expire = TIME_FOREVER;
static int flags = 0; 		/* 检查是否为设置系统灯 */
struct option long_options[] = {
	{"sysled", 1, NULL, 's'},
	{"id", 1, NULL, 'i'},
	{"diskled", 1, NULL, 'd'},
	{"freq", 1, NULL, 0},
	{"expire", 1,&expire , 1},
	{"help", 1, NULL, 'h'},
	{0, 0, 0, 0}
};

void print_help(void)
{
	printf("tools-test-led:\n");
	printf("\t[--sysled|-s on|off]\n");
	printf("\t[--diskled|-d on|off|[blink --freq fast|normal|slow] [--id|-i <disk_id>|<all>]]\n");
	printf("\t[--expire <seconds>]\n");
	printf("\t[--help|-h]\n");
}

int my_getopt(int argc, char **argv)
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
				systask.mode = MODE_NONE;
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
		case 'h':
			print_help();
			return -1;
		case 0:
			if (expire != TIME_FOREVER) {
				task.time = atol(optarg) * 1000;
				break;
			} else {
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
			}
			print_help();
			return -1;
		default:
			break;
		}
	}
	return 0;
}

int parse_args(void)
{
	if (task.mode != MODE_NONE && disk_id == DISK_ID_NONE) {
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
	printf("disk_id:%d, mode:%d, time:%ld, freq:%d, count:%d\n",
	       disk_id, task.mode, task.time, task.freq, task.count);

	return 0;
	
}
void do_work(int i)
{
	if (task.mode & MODE_ON) {
		if (diskled_on(i) < 0) {
			fprintf(stderr, "led %d on failed.\n", i);
		}
	} else if (task.mode & MODE_OFF) {
		if (diskled_off(i) < 0) {
			fprintf(stderr, "led %d off failed.\n", i);
		}
	} else if (task.mode & MODE_BLINK) {
		if (task.freq & FREQ_FAST) {
			if (diskled_blink1s4(i) < 0) {
				fprintf(stderr, "led %d blink failed.\n", i);
			}
		} else if (task.freq & FREQ_NORMAL) {
			if (diskled_blink1s1(i) < 0) {
				fprintf(stderr, "led %d blink failed.\n", i);
			}
		} else if (task.freq & FREQ_SLOW) {
			if (diskled_blink2s1(i) < 0) {
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
	systask.mode = MODE_NONE;
	task.freq = FREQ_NONE;
	task.mode = MODE_NONE;
	task.time = TIME_FOREVER;
	
	if (my_getopt(argc, argv))
		return -1;
	if (parse_args() < 0)
		return -1;

	ret = led_init();
	if (ret == -1) {
		fprintf(stderr, "init led failed.\n");
		return -1;
	}

	ret = diskled_get_disknum();
	if (ret == -1) {
		fprintf(stderr, "get disknum failed.\n");
		return -1;
	}
	
	if (systask.mode != MODE_NONE) {
		if (systask.mode & MODE_ON)
			sysled_on();
		else if (systask.mode & MODE_OFF)
			sysled_off();
	}
	if (disk_id == DISK_ID_NONE )
		return 0;
	
	if (disk_id == DISK_ID_ALL) {
		int i;
		for (i=0; i<= ret; i++)
			do_work(i);
	} else
		do_work(disk_id);

	
	if (task.time == TIME_FOREVER)
		return 0;
	else {
		sleep(task.time);
		if (disk_id == DISK_ID_ALL) {
			int i;
			for (i=0; i <= ret; i++)
				diskled_off(i);
		} else
			diskled_off(disk_id);
	}
	
	return 0;
}
