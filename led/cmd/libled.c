#include <stdio.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <errno.h>
#include <string.h>

#include "libled.h"
#include "../daemon/common.h"
#include "../daemon/sysled.h"
#include "../../pic_ctl/pic_ctl.h"

static shm_t *addr = (shm_t *)-1;
static int initalized;
int semid;

#define LED_CHECK_INIT()	do {			\
		int ret = led_init();			\
		if (ret == -1)				\
			return -1;			\
	} while (0)

#ifdef ONLY_INTERFACE
int led_init(void)
{
	return 0;
}

void led_release(void)
{
	return ;
}

int diskled_get_num(void)
{
	return 0;
}

int diskled_set(int disk_id, enum LED_STATUS sts)
{
	return 0;
}

int diskled_get(int disk_id, enum LED_STATUS *sts)
{
	return 0;
}

int diskled_get_all(enum LED_STATUS *sts_array, int size)
{
	return 0;
}

int sysled_set(enum LED_STATUS sts)
{
	return 0;
}

int sysled_get(enum LED_STATUS *sts)
{
	return 0;
}

int sysled_get_count(void)
{
	return 0;
}

#else

union semum 
{
	int val;
	struct semid_ds *buf;
	ushort *array;
}sem_u;

int p(int semid)
{
	struct sembuf sem_p;
	sem_p.sem_num = 0;
	sem_p.sem_op = -1;
	if (semop(semid, &sem_p, 1) == -1) {
		return -1;
	}
	return 0;
}

int v(int semid) 
{
	struct sembuf sem_v;
	sem_v.sem_num = 0;
	sem_v.sem_op = 1;
	if (semop(semid, &sem_v, 1) == -1){
		return -1;
	}

	return 0;
}

int led_init(void)
{
	if (initalized)
		return 0;
	
	int shmid;
	key_t shmkey;
	struct shmid_ds ds;

	shmkey = ftok(SHMKEY, 0);

	semid = semget(shmkey, 0, 0666);
	if (semid == -1) {
		return -1;
	}
	shmid = shmget(shmkey, 0, 0666);
	if (shmid == -1) {
		return -1;
	}
	
	sem_u.val = 1;
	semctl(semid, 0, SETVAL, sem_u);

	addr = (shm_t *)shmat(shmid, 0, 0);
	if (addr == (shm_t *)-1) {
		return -1;
	}
	
	if (shmctl(shmid, IPC_STAT, &ds) < 0) {
		return -1;
	}
	
	if (ds.shm_nattch <= 1) {
		return -1;
	}

	if (addr->shm_head.magic != MAGIC) {
		return -1;
	}

	initalized = 1;
	return 0;
}

int _diskled_set(int disk_id, enum LED_STATUS mode)
{
	p(semid);

	if (addr->sys & SYS_3U) {
		if (disk_id > DISK_NUM_3U)
			goto error;
		switch (mode) {
		case LED_ON:
			addr->task[disk_id].mode = MODE_ON;
			if (pic_set_led(disk_id-1, PIC_LED_ON, 0) < 0)
				goto error;
			goto quit;
		case LED_OFF:
			addr->task[disk_id].mode = MODE_OFF;
			if (pic_set_led(disk_id-1, PIC_LED_OFF, 0) < 0)
				goto error;
			goto quit;
		case LED_BLINK_FAST:
			addr->task[disk_id].mode = MODE_BLINK;
			addr->task[disk_id].freq = FREQ_FAST;
			addr->task[disk_id].count = COUNT_FAST;
			if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_FAST) < 0)
				goto error;
			goto quit;
		case LED_BLINK_NORMAL:
			addr->task[disk_id].mode = MODE_BLINK;
			addr->task[disk_id].freq = FREQ_NORMAL;
			addr->task[disk_id].count = COUNT_NORMAL;
			if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_NORMAL) < 0)
				goto error;
			goto quit;
		case LED_BLINK_SLOW:
			addr->task[disk_id].mode = MODE_BLINK;
			addr->task[disk_id].freq = FREQ_SLOW;
			addr->task[disk_id].count = COUNT_SLOW;
			if (pic_set_led(disk_id-1, PIC_LED_BLINK, PIC_LED_FREQ_SLOW) < 0)
				goto error;
			goto quit;
		default:
			goto error;
		}
	}
	if (addr->sys & SYS_2U || addr->sys & SYS_A2U) {
		if (disk_id > DISK_NUM_2U)
			goto error;
	}
	if (addr->sys & SYS_S3U) {
		if (disk_id > DISK_NUM_3U)
			goto error;
	}
	switch (mode) {
	case LED_ON:
		addr->task[disk_id].mode = MODE_ON;
		addr->task[disk_id].count = 0;
		goto quit;
	case LED_OFF:
		addr->task[disk_id].mode = MODE_OFF;
		addr->task[disk_id].count = 0;
		goto quit;
	case LED_BLINK_FAST:
		addr->task[disk_id].mode = MODE_BLINK;
		addr->task[disk_id].freq = FREQ_FAST;
		addr->task[disk_id].count = COUNT_FAST;
		goto quit;
	case LED_BLINK_NORMAL:
		addr->task[disk_id].mode = MODE_BLINK;
		addr->task[disk_id].freq = FREQ_NORMAL;
		addr->task[disk_id].count = COUNT_NORMAL;
		goto quit;
	case LED_BLINK_SLOW:
		addr->task[disk_id].mode = MODE_BLINK;
		addr->task[disk_id].freq = FREQ_SLOW;
		addr->task[disk_id].count = COUNT_SLOW;
		goto quit;
	default:
		goto error;
	}
quit:
	v(semid);
	return 0;
error:
	v(semid);
	return -1;
}

int diskled_set(int disk_id, enum LED_STATUS mode)
{
	LED_CHECK_INIT();
	
	if (disk_id == 0) {
		int i;
		for (i=1; i <= addr->shm_head.disk_num; i++) {
			if (_diskled_set(i, mode) < 0) {
				return -1;
			}
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

int diskled_get_all(enum LED_STATUS *arr, int size)
{

	if (!arr)
		return -1;
	LED_CHECK_INIT();
	if (size < addr->shm_head.disk_num)
		return -1;

	int i;
	for(i=1; i <= addr->shm_head.disk_num; i++) {
		if (diskled_get(i, &arr[i-1]) < 0) {
			return -1;
		}
	}
	return 0;
}

int diskled_get(int disk_id, enum LED_STATUS *sts)
{
	if (!sts)
		return -1;

	LED_CHECK_INIT();
	
	if (disk_id > addr->shm_head.disk_num)
		return -1;
	
	p(semid);
	switch (addr->task[disk_id].mode) {
	case MODE_ON:
		*sts = LED_ON;
		goto quit;
	case MODE_OFF:
		*sts = LED_OFF;
		goto quit;
	case MODE_BLINK:
		switch (addr->task[disk_id].freq) {
		case FREQ_FAST:
			*sts = LED_BLINK_FAST;
			goto quit;
		case FREQ_NORMAL:
			*sts = LED_BLINK_NORMAL;
			goto quit;
		case FREQ_SLOW:
			*sts = LED_BLINK_SLOW;
			goto quit;
		default:
			goto error;
		}
	default:
		goto error;
	}
quit:
	v(semid);
	return 0;
error:
	v(semid);
	return -1;
	
}

int sysled_set(enum LED_STATUS mode)
{
	int ret;

	LED_CHECK_INIT();
	p(semid);
	if (addr->sys & SYS_A2U) {
		if (mode == LED_ON) {
			addr->task[0].mode = MODE_ON;
			addr->task[0].count++;
			ret = sb_gpio28_set_atom(true);
			if (ret < 0)
				goto error;
		}
		if (mode == LED_OFF) {
			addr->task[0].count--;
			if (addr->task[0].count <= 0) {
				addr->task[0].count = 0;
				addr->task[0].mode = MODE_OFF;
				ret = sb_gpio28_set_atom(false);
				if (ret < 0)
					goto error;
			}
		}
		if (mode == LED_FORCE_OFF) {
			addr->task[0].mode = MODE_FORCE_OFF;
			ret = sb_gpio28_set_atom(false);
			if (ret < 0)
				goto error;
		}	
	} else {
		if (mode == LED_ON) {
			addr->task[0].mode = MODE_ON;
			addr->task[0].count++;
			ret = sb_gpio28_set(true);
			if (ret < 0)
				goto error;
		}
		if (mode == LED_OFF) {
			addr->task[0].count--;
			if (addr->task[0].count <= 0) {
				addr->task[0].count = 0;
				addr->task[0].mode = MODE_OFF;
				ret = sb_gpio28_set(false);
				if (ret < 0)
					goto error;
			}
		}
		if (mode == LED_FORCE_OFF) {
			addr->task[0].mode = MODE_FORCE_OFF;
			ret = sb_gpio28_set(false);
			if (ret < 0)
				goto error;
		}
	}
	v(semid);
	return 0;
error:
	v(semid);
	return -1;
}

int sysled_get(enum LED_STATUS *sts)
{
	LED_CHECK_INIT();
	
	p(semid);
	if (addr->task[0].mode & MODE_ON) 
		*sts = LED_ON;
	else if (addr->task[0].mode & MODE_OFF)
		*sts = LED_OFF;
	else if (addr->task[0].mode & MODE_FORCE_OFF)
		*sts = LED_FORCE_OFF;
	else {
		v(semid);
		return -1;
	}
	v(semid);
	return 0;
}

int sysled_get_count(void)
{
	LED_CHECK_INIT();
	return addr->task[0].count;
}
#endif
