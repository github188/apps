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



char *const short_options = "s:gi:d:f:e:h";
led_task_t task;
led_task_t systask;
static int disk_id = DISK_ID_NONE;
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
				systask.mode = MODE_ON;
			} else if (!strcmp(optarg, "off")) {
				systask.mode = MODE_OFF;
			} else if (!strcmp(optarg, "foff")) {
				systask.mode = MODE_FORCE_OFF;
			} else {
				fprintf(stderr, "sysled mode invalid.\n");
			}
			break;
		case 'g':
			getflag = 1;
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

			fprintf(stderr, "diskled mode invalid.\n");
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
	if (task.mode != -1 && disk_id == DISK_ID_NONE) {
		fprintf(stderr, "diskid is null.\n");
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
	task.mode = -1;
	task.freq = FREQ_NONE;
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
		else if (systask.mode & MODE_FORCE_OFF)
			sysled_set(LED_FORCE_OFF);
	}
	

	if (disk_id == DISK_ID_ALL)  {
		do_work(0);
	} else if (disk_id != DISK_ID_NONE){
		do_work(disk_id);
	}
	if (getflag) {
		do_get_work(0);
	}

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
