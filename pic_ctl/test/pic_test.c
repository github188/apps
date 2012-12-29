#include <stdio.h>
#include "../pic_ctl.h"

#define ARRAY_SIZE(a) (sizeof(a) / sizeof(a[0]))
int main(int argc, char *argv[])
{
	int i, j;
	uint32_t v;
	int ret;

	static int sts[] = {
		PIC_LED_ON, PIC_LED_OFF, PIC_LED_BLINK,
	};

	static int freq[] = {
		PIC_LED_FREQ_SLOW, PIC_LED_FREQ_NORMAL,
		PIC_LED_FREQ_FAST,
	};

	ret = pic_get_version(&v);
	if (ret < 0)
		fprintf(stderr, "PIC: get version return %d\n", ret);
	else
		printf("PIC: Get version: %04x\n", v);

	for (i = 0, j = 0; i < PIC_LED_NUMBER; i++) {
		int idx = i % ARRAY_SIZE(sts);
		int f = 0;

		if (sts[idx] == PIC_LED_BLINK) {
			j = (j + 1) % ARRAY_SIZE(freq);
			f = freq[j];
		}

		ret = pic_set_led(i, sts[idx], f);
		if (ret < 0)
			fprintf(stderr, "Set led return: %d\n", ret);
	}

	return 0;
}
