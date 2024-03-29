#include <stdio.h>
#include <syslog.h>
#include <string.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include "common.h"
#include "led_shm.h"

extern int systype;
int disk_max_num;
shm_t *addr;

int sem_init()
{
	int semid;
	key_t semkey;

	semkey = ftok(SHMKEY, 0);
	if ((semid = semget(semkey, 0, 0666)) >= 0) {
		return semid;
	}

	semid = semget(semkey, 1, 0666|IPC_CREAT);
	if (semid == -1) {
		syslog(LOG_ERR, "create sem failed.\n");
		return -1;
	}

	union semum {
		int val;
		struct semid_ds *buf;
		ushort *array;
	}sem_u;

	sem_u.val = 1;
	semctl(semid, 0, SETVAL, sem_u);
	return semid;
}

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
	
	if ((shmid = shmget(shmkey, 0,  0666)) >= 0) {
		addr = (shm_t *)shmat(shmid, 0, 0);
		if (addr == (shm_t*)-1) {
			syslog(LOG_ERR, "shmat failed.\n");
			return -1;
		}
		int j;
		for (j=0; j<=disk_max_num; j++) {
			addr->task[j].power.mode = POWER_ON;
			if (j <= 4)
				addr->task[j].power.time = 1000000;
			else if (j <= 8)
				addr->task[j].power.time = 2000000;
			else if (j <= 12)
				addr->task[j].power.time = 3000000;
			else if (j <= 16)
				addr->task[j].power.time = 4000000;
				
		}

		return shmid;
	}

	size = (sizeof(led_task_t) * (disk_max_num + 1) + 
		sizeof(shm_head_t) + 
		sizeof(int));
	shmid = shmget(shmkey, size, 0666|IPC_CREAT);
	if (shmid == -1) {
		syslog(LOG_ERR, "create shm failed.\n");
		return -1;
	}
	addr = (shm_t *)shmat(shmid, 0, 0);
	if (addr == (shm_t*)-1) {
		syslog(LOG_ERR, "shmat failed.\n");
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
		addr->task[i].power.mode = POWER_ON;
		if (i <= 4)
			addr->task[i].power.time = 1000000;
		else if (i <= 8)
			addr->task[i].power.time = 2000000;
		else if (i <= 12)
			addr->task[i].power.time = 3000000;
		else if (i <= 16)
			addr->task[i].power.time = 4000000;
	}
	
	return shmid;
}

void shm_release(void)
{
	int ret = -1;
	int shmid, semid;
	key_t shmkey;

	shmkey = ftok(SHMKEY, 0);
	semid = semget(shmkey, 0, 0666);
	shmid = shmget(shmkey, 0, 0666);
	ret = shmctl(shmid, IPC_RMID, NULL);
	if (ret < 0) {
		syslog(LOG_NOTICE, "release shm failed.\n");
	} else {
		syslog(LOG_NOTICE, "release shm successed.\n");
	}
	ret = semctl(semid, 0, IPC_RMID);
	if (ret < 0) {
		syslog(LOG_NOTICE, "release sem failed.\n");
	} else {
		syslog(LOG_NOTICE, "release sem successed.\n");
	} 
}
