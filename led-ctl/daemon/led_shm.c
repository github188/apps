#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include "common.h"
#include "led_shm.h"

extern int systype;
int disk_max_num;
shm_t *addr;

int shm_init()
{
	int shmid;
	key_t shmkey;
	size_t size;

	
	shmkey = ftok(SHMKEY, 0);

	switch(systype) {
	case SYS_3U: case SYS_S3U:
		disk_max_num = DISK_NUM_3U;
		break;
	case SYS_2U: case SYS_A2U:
		disk_max_num = DISK_NUM_2U;
		break;
	default:
		return -1;
	}
	
	size = (sizeof(led_task_t) * (disk_max_num + 1) + sizeof(shm_head_t) + sizeof(int));
	shmid = shmget(shmkey, size,  0666|IPC_CREAT);
	if (shmid == -1) {
		fprintf(stderr, "create shm failed.\n");
		return -1;
	}
	addr = (shm_t *)shmat(shmid, 0, 0);
	if (addr == (shm_t*)-1) {
		fprintf(stderr, "shmat failed.\n");
		return -1;
	}
	
	switch(systype) {
	case SYS_3U:
		addr->sys = SYS_3U;
		break;
	case SYS_S3U:
		addr->sys = SYS_S3U;
		break;
	case SYS_2U:
		addr->sys = SYS_2U;
		break;
	case SYS_A2U:
		addr->sys = SYS_A2U;
		break;
	default:
		return -1;
	}
	
	addr->shm_head.version = VERSION;
	addr->shm_head.magic = MAGIC;
	addr->shm_head.disk_num = disk_max_num;

	int i;
	for (i=0; i <= disk_max_num; i++) {
		addr->task[i].mode = MODE_OFF;
		addr->task[i].freq = FREQ_NONE;
		addr->task[i].count = 0;
		addr->task[i].time = TIME_FOREVER;
	}
	
	return shmid;
}

void shm_release(void)
{
	int ret = -1;
	int shmid;
	key_t shmkey;

	shmkey = ftok(SHMKEY, 0);
	shmid = shmget(shmkey, 0, 0666);
	ret = shmctl(shmid, IPC_RMID, NULL);
	if (ret == -1) {
		fprintf(stderr, "release shm failed.\n");
		return;
	}
}
