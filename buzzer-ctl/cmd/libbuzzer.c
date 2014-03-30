#include <stdio.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <errno.h>
#include <string.h>

#include "libbuzzer.h"
#include "../daemon/common.h"


static shm_t *addr = (shm_t *)-1;
static int initalized;
int semid;

#define BUZZER_CHECK_INIT()	do {			\
		int ret = buzzer_init();		\
		if (ret == -1)				\
			return -1;			\
	} while (0)

#ifdef ONLY_INTERFACE
int buzzer_init(void)
{
	return 0;
}

void buzzer_release(void)
{
	return ;
}

int buzzer_get(enum BUZZER_STATUS *sts)
{
	return 0;
}

int buzzer_set(enum BUZZER_STATUS sts)
{
	return 0;
}

int buzzer_get(int *count)
{
	return 0;
}

int buzzer_get_count(void)
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

int b_p(int semid)
{
	struct sembuf sem_p;
	sem_p.sem_num = 0;
	sem_p.sem_op = -1;
	if (semop(semid, &sem_p, 1) == -1) {
		return -1;
	}
	return 0;
}

int b_v(int semid) 
{
	struct sembuf sem_v;
	sem_v.sem_num = 0;
	sem_v.sem_op = 1;
	if (semop(semid, &sem_v, 1) == -1){
		return -1;
	}

	return 0;
}

int buzzer_init(void)
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

void buzzer_release(void)
{
	if (initalized)
		addr = (shm_t *)-1;
}

int buzzer_set(enum BUZZER_STATUS mode)
{

	BUZZER_CHECK_INIT();
	b_p(semid);
	
		if (mode == BUZZER_ON) {
			addr->task.mode = MODE_ON;
			addr->task.count++;
		}
		if (mode == BUZZER_OFF) {
			addr->task.count--;
			if (addr->task.count <= 0) {
				addr->task.count = 0;
				addr->task.mode = MODE_OFF;
			}
		}
		if (mode == BUZZER_FORCE_OFF) {
			addr->task.mode = MODE_FORCE_OFF;
		}

	b_v(semid);
	return 0;
}

int buzzer_get(enum BUZZER_STATUS *sts)
{
	BUZZER_CHECK_INIT();
	b_p(semid);
	if (addr->task.mode & MODE_ON) 
		*sts = BUZZER_ON;
	else if (addr->task.mode & MODE_OFF)
		*sts = BUZZER_OFF;
	else if (addr->task.mode & MODE_FORCE_OFF)
		*sts = BUZZER_FORCE_OFF;
	else {
		b_v(semid);
		return -1;
	}
	b_v(semid);
	return 0;
}

int buzzer_get_count(void)
{
	BUZZER_CHECK_INIT();
	return addr->task.count;
}
#endif
