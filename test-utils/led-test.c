#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "../monitor/sys-utils.h"
#include "../pic_ctl/pic_ctl.h"

int expried = 0;

void _usage(const char *msg)
{
	fprintf(stderr, "%s\n\n", msg);
	fprintf(stderr, "led-test <--sysled|--diskled> <on|off|blink> [--exprie <seconds>]\n\n");
	exit(-1);
}

void sysled_off()
{
	printf("sysled off\n");
	sb_gpio28_set(false);
}

void sysled_on()
{
	printf("sysled on\n");
	sb_gpio28_set(true);
	if (expried)
	{
		sleep(expried);
		sysled_off();
	}
}

void sysled_blink()
{
	do {
		sb_gpio28_set(false);
		sb_gpio28_set(true);
		sleep(1);
		sb_gpio28_set(false);
	} while(expried--);
}

void diskled_off()
{
	int i;

	printf("disk led off\n");

	for (i=0;i<16;i++)
		pic_set_led(i, PIC_LED_OFF, 0);
}

void diskled_on()
{
	int i;

	printf("disk led on\n");

	for (i=0;i<16;i++)
		pic_set_led(i, PIC_LED_ON, 0);

	if (expried)
	{
		sleep(expried);
		diskled_off();
	}
}

void diskled_blink()
{
	int i;

	printf("disk led blink\n");

	for (i=0;i<16;i++)
		pic_set_led(i, PIC_LED_BLINK, PIC_LED_FREQ_FAST);

	if (expried)
		sleep(expried);

	diskled_off();
}

int main(int argc, char *argv[])
{
	bool sysled, diskled;

	sysled = false;
	diskled = false;

	if (argc < 3)
		_usage("args not enough!\n");

	if ((argc >= 5) && (!strcmp(argv[3], "--expried")))
		expried = atoi(argv[4]);

	if (!strcmp(argv[1], "--sysled"))
		sysled = true;
	else if (!strcmp(argv[1], "--diskled"))
		diskled = true;
	else
		_usage("set --diskled or --sysled");

	if (sysled)
	{
		if (!strcmp(argv[2], "on"))
			sysled_on();
		else if (!strcmp(argv[2], "off"))
			sysled_off();
		else if (!strcmp(argv[2], "blink"))
			sysled_blink();
		else
			_usage("set on,off,blink!");
	}
	else if (diskled)
	{
		if (!strcmp(argv[2], "on"))
			diskled_on();
		else if (!strcmp(argv[2], "off"))
			diskled_off();
		else if (!strcmp(argv[2], "blink"))
			diskled_blink();
		else
			_usage("set on,off,blink!");
	}

	return 0;
}
