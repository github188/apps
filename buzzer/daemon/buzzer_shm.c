#include <stdio.h>
#include <syslog.h>
#include <string.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include "common.h"
#include "buzzer_shm.h"

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
		syslog(LOG_ERR, "buzzer-ctl: create sem failed.\n");
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

	if((shmid = shmget(shmkey, 0, 0666)) >= 0) {
		addr = (shm_t *)shmat(shmid, 0, 0);
		if (addr == (shm_t *)-1) {
			syslog(LOG_ERR, "buzzer-ctl: shmat failed.\n");
			return -1;
		}
		return shmid;
	}
	
	size = sizeof(shm_t);
	shmid = shmget(shmkey, size,  0666|IPC_CREAT);
	if (shmid == -1) {
		syslog(LOG_ERR, "buzzer-ctl: create shm failed.\n");
		return -1;
	}
	addr = (shm_t *)shmat(shmid, 0, 0);
	if (addr == (shm_t*)-1) {
		syslog(LOG_ERR, "buzzer-ctl: shmat failed.\n");
		return -1;
	}
	
	addr->shm_head.version = VERSION;
	addr->shm_head.magic = MAGIC;
		
	addr->task.mode = MODE_OFF;
	addr->task.count = 0;

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
	if (ret == -1) {
		syslog(LOG_NOTICE, "buzzer_ctl: release shm failed.\n");
		return;
	}
	ret = semctl(semid, 0, IPC_RMID);
	if (ret == -1) {
		syslog(LOG_NOTICE, "buzzer_ctl: release sem failed.\n");
		return;
	}
}
