#include <stdio.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <errno.h>
#include <string.h>

#include "libdiskpw.h"
#include "../daemon/common.h"
#include "../../pic_ctl/pic_ctl.h"

#define  SECONDS_MAX 15

static shm_t *addr = (shm_t *)-1;
static int initalized;
static int semid;

#define POWER_CHECK_INIT()	do {			\
		int ret = diskpw_init();		\
		if (ret == -1)				\
			return -1;			\
	} while (0)
#ifdef ONLY_INTERFACE
int diskpw_init(void)
{
	return 0;
}

void diskpw_release(void)
{
	return 0;
}

int diskpw_set(int id, enum DISKPW_STATUS mode, int seconds)
{
	return 0;
}
#else


int p(int semid)
{
	struct sembuf sem_p;
	sem_p.sem_num = 0;
	sem_p.sem_op = -1;
	sem_p.sem_flg = SEM_UNDO;
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
	sem_v.sem_flg = SEM_UNDO;
	if (semop(semid, &sem_v, 1) == -1){
		return -1;
	}

	return 0;
}



int diskpw_init(void)
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

	addr = (shm_t *)shmat(shmid, 0, 0);
	if (addr == (shm_t *)-1) {
		return -1;
	}

	if (shmctl(shmid, IPC_STAT, &ds) < 0) {
		return -1;
	}


	if (addr->shm_head.magic != MAGIC) {
		return -1;
	}

	initalized = 1;
	return 0;
}

void diskpw_release(void)
{
	if (initalized) {
		shmdt(addr);
		addr = (shm_t *)-1;
		initalized = 0;
	}
}

int diskpw_get_num(void)
{
	POWER_CHECK_INIT();
	return addr->shm_head.disk_num;
}

int diskpw_set(int id, enum DISKPW_STATUS mode, int seconds)
{
	if (id <= 0 || id > diskpw_get_num() || seconds < 0)
		return -1;

	if (seconds > SECONDS_MAX)
		seconds = SECONDS_MAX;

	POWER_CHECK_INIT();
	if (addr->sys & SYS_S3U) {
		p(semid);
		if (mode == POWER_ON) {
			addr->task[id].power.mode = POWER_ON;
			addr->task[id].power.time = 0;
		} else if (mode == POWER_OFF) {
			addr->task[id].power.mode = POWER_OFF;
			addr->task[id].power.time = 0;
		} else if (mode == POWER_RESET) {
			addr->task[id].power.mode = POWER_RESET;
			addr->task[id].power.time = seconds * 1000000;
		}
		v(semid);
		return 0;
	} else if (addr->sys & SYS_3U) {
		p(semid);

		if (seconds > 0)
			pic_reset_timer(seconds);
		pic_reset_hd(id - 1);

		v(semid);
		return 0;
	} else {
		return -1;
	}
}
#endif
