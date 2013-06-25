#include <stdio.h>
#include <unistd.h>
#include "../pic_ctl.h"

#define ARRAY_SIZE(a) (sizeof(a) / sizeof(a[0]))
int main(int argc, char *argv[])
{
	int i, j, k, f;
	uint32_t v;
	int ret;

	static int sts[] = {
		PIC_LED_ON, PIC_LED_B2, PIC_LED_BLINK, PIC_LED_BLINK, PIC_LED_BLINK,
		PIC_LED_OFF,
	};

	static int freq[] = {
		PIC_LED_FREQ_SLOW, PIC_LED_FREQ_NORMAL,	PIC_LED_FREQ_FAST,
	};

	static char* item[] = {
		"disk led on", "disk led blink fast 2 times interval 2s", "disk led blink slow",
		"disk led blink normal", "disk led blink fast", "disk led off",
	};

	ret = pic_get_version(&v);
	if (ret < 0)
		fprintf(stderr, "get pic version return %d\n", ret);
	else
		printf("pic version: %04x\n", v);

	for (i=0, j=0; i<sizeof(sts)/sizeof(sts[0]); i++) {
		printf("%s\n", item[i]);
		f = 0;
		if (sts[i] == PIC_LED_BLINK)
			f = freq[j++];
		for (k=0; k<PIC_LED_NUMBER; k++) {
			ret = pic_set_led(k, sts[i], f);
			if (ret < 0)
				fprintf(stderr, "set disk led return: %d, slot: %d, "
						"mode: %d, extra: %d\n", ret, k+1, i, f);
		}
		if (sts[i] != PIC_LED_OFF)
			sleep(8);
	}

	return 0;
}
