#include <stdio.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <errno.h>
#include <string.h>

#include "../daemon/common.h"
#include "../daemon/i2c_dev.h"

shm_t * get_systype(void)
{
	int shmid;
	key_t shmkey;
	shm_t *addr;

	shmkey = ftok(SHMKEY, 0);
	shmid = shmget(shmkey, 0, 0666);
	if (shmid == -1) {
		return (shm_t *)-1;
	}

	addr = (shm_t *)shmat(shmid, 0, 0);
	if (addr == (shm_t *)-1) {
		return (shm_t *)-1;
	}
	return addr;
}
int diskled_on(int disk_id)
{
	shm_t *addr;

	addr = get_systype();
	if (addr == (shm_t *)-1)
		return -1;
	if (addr->sys & SYS_3U) {
		if (pic_set_led(disk_id-1, PIC_LED_ON, 0) < 0) {
			return -1;
		}
		return 0;
	} 
	if (addr->sys & SYS_2U) {
		if (disk_id > DISK_NUM_2U)
			return -1;
	}
	if (addr->sys & SYS_S3U) {
		if (disk_id > DISK_NUM_3U)
			return -1;
	}
	addr->task[disk_id].mode = MODE_ON;
	return 0;
}

int diskled_off(int disk_id)
{
	shm_t *addr;

	addr = get_systype();
	if (addr == (shm_t *)-1)
		return -1;

	if (addr->sys & SYS_3U) {
		if (pic_set_led(disk_id-1, PIC_LED_OFF, 0) < 0) {
			return -1;
		}
		return 0;
	}
	if (addr->sys & SYS_2U) {
		if (disk_id > DISK_NUM_2U)
			return -1;

	}
	if (addr->sys & SYS_S3U) {
		if (disk_id > DISK_NUM_3U)
			return -1;
	}
	addr->task[disk_id].mode = MODE_OFF;
	return 0;
}

int diskled_blink1s4(int disk_id)
{
	shm_t *addr;

	addr = get_systype();
	if (addr == (shm_t *)-1)
		return -1;
	if (addr->sys & SYS_3U) {
		if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_FAST) < 0) {
			return -1;
		}
		return 0;
	}
	if (addr->sys & SYS_2U) {
		if (disk_id > DISK_NUM_2U)
			return -1;
	}
	if (addr->sys & SYS_S3U) {
		if (disk_id > DISK_NUM_3U)
			return -1;
	}
	addr->task[disk_id].mode = MODE_BLINK;
	addr->task[disk_id].freq = FREQ_FAST;
	addr->task[disk_id].count = COUNT_FAST;
	return 0;
}

int diskled_blink1s1(int disk_id)
{
	shm_t *addr;

	addr = get_systype();
	if (addr == (shm_t *)-1)
		return -1;
	if (addr->sys & SYS_3U) {
		if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_NORMAL) < 0) {
			return -1;
		}
		return 0;
	}
	if (addr->sys & SYS_2U) {
		if (disk_id > DISK_NUM_2U)
			return -1;
	}
	if (addr->sys & SYS_S3U) {
		if (disk_id > DISK_NUM_3U)
			return -1;
	}
	addr->task[disk_id].mode = MODE_BLINK;
	addr->task[disk_id].freq = FREQ_NORMAL;
	addr->task[disk_id].count = COUNT_NORMAL;
	return 0;
}

int diskled_blink2s1(int disk_id)
{
	shm_t *addr;

	addr = get_systype();
	if (addr == (shm_t *)-1)
		return -1;
	if (addr->sys & SYS_3U) {
		if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_SLOW) < 0) {
			return -1;
		}
		return 0;
	}
	if (addr->sys & SYS_2U) {
		if (disk_id > DISK_NUM_2U)
			return -1;
	}
	if (addr->sys & SYS_S3U) {
		if (disk_id > DISK_NUM_3U)
			return -1;
	}
	addr->task[disk_id].mode = MODE_BLINK;
	addr->task[disk_id].freq = FREQ_SLOW;
	addr->task[disk_id].count = COUNT_SLOW;
	return 0;
}

int sysled_on (void)
{
	return sb_gpio28_set(1);
}

int sysled_off(void)
{
	return sb_gpio28_set(0);
}
