#include <stdio.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <errno.h>
#include <string.h>

#include "libled.h"
#include "../daemon/common.h"
#include "../daemon/sysled.h"
#include "../../pic_ctl/pic_ctl.h"

static shm_t *addr = (shm_t *)-1;
static initalized;

#define LED_CHECK_INIT()	do {			\
		int ret = led_init();			\
		if (ret == -1)				\
			return -1;			\
	} while (0)

int led_init(void)
{
	if (initalized)
		return 0;
	
	int shmid;
	key_t shmkey;

	shmkey = ftok(SHMKEY, 0);
	shmid = shmget(shmkey, 0, 0666);
	if (shmid == -1) {
		return -1;
	}
	
	addr = (shm_t *)shmat(shmid, 0, 0);
	if (addr == (shm_t *)-1) {
		return -1;
	}
	
	if (addr->shm_head.magic != MAGIC) {
		return -1;
	}

	initalized = 1;
	return 0;
}

void led_release(void)
{
	if (initalized)
		addr = (shm_t *)-1;
}

int _diskled_set(int disk_id, int mode)
{
	if (addr->sys & SYS_3U) {
		if (disk_id > DISK_NUM_3U)
			return -1;
		switch (mode) {
		case LED_ON:
			addr->task[disk_id].mode = MODE_ON;
			if (pic_set_led(disk_id-1, PIC_LED_ON, 0) < 0)
				return -1;
			return 0;
		case LED_OFF:
			addr->task[disk_id].mode = MODE_OFF;
			if (pic_set_led(disk_id-1, PIC_LED_OFF, 0) < 0)
				return -1;
			return 0;
		case LED_BLINK_FAST:
			addr->task[disk_id].mode = MODE_BLINK;
			addr->task[disk_id].freq = FREQ_FAST;
			addr->task[disk_id].count = COUNT_FAST;
			if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_FAST) < 0)
				return -1;
			return 0;
		case LED_BLINK_NORMAL:
			addr->task[disk_id].mode = MODE_BLINK;
			addr->task[disk_id].freq = FREQ_NORMAL;
			addr->task[disk_id].count = COUNT_NORMAL;
			if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_NORMAL) < 0)
				return -1;
			return 0;
		case LED_BLINK_SLOW:
			addr->task[disk_id].mode = MODE_BLINK;
			addr->task[disk_id].freq = FREQ_SLOW;
			addr->task[disk_id].count = COUNT_SLOW;
			if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_SLOW) < 0)
				return -1;
			return 0;
		default:
			return -1;
		}
	}
	if (addr->sys & SYS_2U) {
		if (disk_id > DISK_NUM_2U)
			return -1;
	}
	if (addr->sys & SYS_S3U) {
		if (disk_id > DISK_NUM_3U)
			return -1;
	}
	switch (mode) {
	case LED_ON:
		addr->task[disk_id].mode = MODE_ON;
		return 0;
	case LED_OFF:
		addr->task[disk_id].mode = MODE_OFF;
		return 0;
	case LED_BLINK_FAST:
		addr->task[disk_id].mode = MODE_BLINK;
		addr->task[disk_id].freq = FREQ_FAST;
		addr->task[disk_id].count = COUNT_FAST;
		return 0;
	case LED_BLINK_NORMAL:
		addr->task[disk_id].mode = MODE_BLINK;
		addr->task[disk_id].freq = FREQ_NORMAL;
		addr->task[disk_id].count = COUNT_NORMAL;
		return 0;
	case LED_BLINK_SLOW:
		addr->task[disk_id].mode = MODE_BLINK;
		addr->task[disk_id].freq = FREQ_SLOW;
		addr->task[disk_id].count = COUNT_SLOW;
		return 0;
	default:
		return -1;
	}
}

int diskled_set(int disk_id, int mode)
{
	LED_CHECK_INIT();
	
	if (disk_id == 0) {
		int i;
		for (i=1; i <= addr->shm_head.disk_num; i++) {
			if (_diskled_set(i, mode) < 0)
				return -1;
		}
		return 0;
	}

	return _diskled_set(disk_id, mode);
}

int diskled_get_num(void)
{
	LED_CHECK_INIT();
	return addr->shm_head.disk_num;
}

int diskled_get_all(int *arr, int size)
{
	if (!arr)
		return -1;
	LED_CHECK_INIT();
	if (size < addr->shm_head.disk_num)
		return -1;

	int i;
	for(i=1; i <= addr->shm_head.disk_num; i++) {
		if (diskled_get(i, &arr[i-1]) < 0)
			return -1;
	}
	return 0;
}

int diskled_get(int disk_id,  int *sts)
{
	if (!sts)
		return -1;

	LED_CHECK_INIT();
	if (disk_id > addr->shm_head.disk_num)
		return -1;
	
	switch (addr->task[disk_id].mode) {
	case MODE_ON:
		*sts = LED_ON;
		return 0;
	case MODE_OFF:
		*sts = LED_OFF;
		return 0;
	case MODE_BLINK:
		switch (addr->task[disk_id].freq) {
		case FREQ_FAST:
			*sts = LED_BLINK_FAST;
			return 0;
		case FREQ_NORMAL:
			*sts = LED_BLINK_NORMAL;
			return 0;
		case FREQ_SLOW:
			*sts = LED_BLINK_SLOW;
			return 0;
		default:
			return -1;
		}
	default:
		return -1;
	}
	
}

int sysled_set(int mode)
{
	LED_CHECK_INIT();
	
	if (mode == LED_ON) {
		addr->task[0].mode = MODE_ON;
		return sb_gpio28_set(true);
	}
	else if (mode == LED_OFF) {
		addr->task[0].mode = MODE_OFF;
		return sb_gpio28_set(false);
	}

	return -1;
}

int sysled_get(int *sts)
{
	LED_CHECK_INIT();

	if (addr->task[0].mode & MODE_ON) 
		*sts = LED_ON;
	else if (addr->task[0].mode & MODE_OFF)
		*sts = LED_OFF;
	else
		return -1;

	return 0;
}

