#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <syslog.h>
#include <getopt.h>
#include <string.h>
#include "common.h"
#include "buzzer_shm.h"
#include "buzzer_worker.h"

char *const short_options = "ch";
struct option long_options[] = {
	{"clean", 0, NULL, 'c'},
	{"help", 0, NULL, 'h'},
	{0, 0, 0, 0}
};


void print_help(void)
{
	printf("buzzer-ctl-daemonls:\n");
	printf("\t[--clean]\n");
	printf("\t[--help|-h]\n");
}

int main(int argc, char *argv[])
{
	int c, fd;
	int shmid, semid;
	struct flock lock;
	lock.l_type = F_WRLCK;
	lock.l_start = 0;
	lock.l_whence = SEEK_SET;
	lock.l_len = 0;
	lock.l_pid = getpid();

	openlog("buzzer-ctl-daemon", LOG_NDELAY|LOG_PID|LOG_CONS|LOG_PERROR, LOG_DAEMON);
	if ((fd = open(LOCK_FILE, O_RDWR|O_CREAT, 0644)) < 0) {
		syslog(LOG_INFO, "create lock file failed.\n");
		return -1;
	}

	if ((fcntl(fd, F_SETLK, &lock)) < 0) {
		syslog(LOG_ERR, "get file lock failed. exitting...\n");
		//fprintf(stderr, "get file lock failed. exitting...\n");
		return -1;
	}
	if (open(SHMKEY, O_RDWR|O_CREAT, 0644) < 0) {
		syslog(LOG_ERR, "create shmkey file %s failed.\n", SHMKEY);
		return -1;
	}
	while ((c = getopt_long(argc, (char *const*)argv, short_options,
				long_options, NULL)) != -1) {
		switch (c){
		case 'c':
			goto clean;
		case 'h':
			print_help();
			return 0;
		default:
			return -1;
		}
	}
	semid = sem_init();
	if (semid < 0) 
		return -1;
	shmid = shm_init();
	if (shmid < 0)
		return -1;
	syslog(LOG_INFO, "init done.\n");
	worker_init();

clean:	
	shm_release();
	lock.l_type = F_UNLCK;
	fcntl(fd, F_SETLK, &lock);
	unlink(LOCK_FILE);
	syslog(LOG_INFO, "exited.\n");
	return 0;
}
