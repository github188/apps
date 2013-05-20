#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <signal.h>
#include <time.h>
#include <getopt.h>

#include "../monitor/sys-utils.h"
#include "../pic_ctl/pic_ctl.h"

struct option longopts[] = {
	{"sysled",		1, NULL, 's'},
	{"diskled",		1, NULL, 'd'},
	{"freq",		1, NULL, 'f'},
	{"expire",		1, NULL, 'e'},
	{0,0,0,0}};

int sysled = 0;
int diskled = 0;
int expired = 0;
int sysled_op = PIC_LED_OFF;
int diskled_op = PIC_LED_OFF;
int diskled_blink_freq = PIC_LED_FREQ_NORMAL;

void usage()
{
	fprintf(stderr, "tools_test_led [--sysled|-s on|off]\n"
		"\t[--diskled|-d on|off|[blink --freq fast|normal|slow]]\n"
		"\t[--expire <seconds>]\n\n"
		"tools_test_led --help\n");
	exit(-1);
}

int parser(int argc, char *argv[])
{
	int c, freq = 0;
	while((c=getopt_long(argc, argv, "s:d:f:e:h", longopts, NULL))!=-1) {
		switch (c) {
		case 's':
		sysled = 1;
		if (optarg) {
			if (strcmp(optarg, "on") == 0)
				sysled_op = PIC_LED_ON;
			else if (strcmp(optarg, "off") == 0)
				sysled_op = PIC_LED_OFF;
			else {
				fprintf(stderr, "invalid param %s\n", optarg);
				return -1;
			}
		}
		break;
		case 'd':
		diskled = 1;
		if (optarg) {
			if (strcmp(optarg, "on") == 0)
				diskled_op = PIC_LED_ON;
			else if (strcmp(optarg, "off") == 0)
				diskled_op = PIC_LED_OFF;
			else if (strcmp(optarg, "blink") == 0)
				diskled_op = PIC_LED_BLINK;
			else {
				fprintf(stderr, "invalid param %s\n", optarg);
				return -1;
			}
		}
		break;
		case 'f':
		freq = 1;
		if (optarg) {
			if (strcmp(optarg, "slow") == 0)
				diskled_blink_freq = PIC_LED_FREQ_SLOW;
			else if (strcmp(optarg, "normal") == 0)
				diskled_blink_freq = PIC_LED_FREQ_NORMAL;
			else if (strcmp(optarg, "fast") == 0)
				diskled_blink_freq = PIC_LED_FREQ_FAST;
			else {
				fprintf(stderr, "invalid param %s\n", optarg);
				return -1;
			}
		}
		break;
		case 'e':
		if (optarg)
			expired = atoi(optarg);
		break;
		case 'h':
		case -1:
		case '?':
			return -1;
		}
	}

	if (PIC_LED_BLINK == diskled_op && 0 == freq) {
		fprintf(stderr, "miss --freq option when test disk led blink\n");
		return -1;
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

	if (sysled) {
		printf("sysled %s\n", PIC_LED_ON == sysled_op ? "on" : "off");
		sb_gpio28_set(PIC_LED_ON == sysled_op ? true : false);
	}
	
	if (diskled) {
		if (PIC_LED_BLINK == diskled_op)
			printf("disk led blink %s\n", 
				diskled_blink_freq == PIC_LED_FREQ_SLOW ? "slow" : 
				diskled_blink_freq == PIC_LED_FREQ_FAST ? "fast" : "normal");
		else
			printf("disk led %s\n", PIC_LED_ON == diskled_op ? "on" : "off");

		for (i=0;i<16;i++)
			pic_set_led(i, diskled_op, diskled_blink_freq);
	}

	if (expired && (sysled || diskled)) {
		sleep(expired);

		if (diskled_op != PIC_LED_OFF) {
			for (i=0;i<16;i++)
				pic_set_led(i, PIC_LED_OFF, 0);
			printf("disk led off\n");
		}

		if (sysled_op != PIC_LED_OFF) {
			sb_gpio28_set(false);
			printf("sys led off\n");
		}
	}

	return 0;
}
