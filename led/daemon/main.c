#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <syslog.h>
#include <getopt.h>
#include <string.h>
#include "common.h"
#include "led_shm.h"
#include "led_worker.h"
#include "i2c_dev.h"


char *l_opt_arg;
char *const short_options = "t:ch";
struct option long_options[] = {
	{"type", 1, NULL, 't'},
	{"clean", 0, NULL, 'c'},
	{"help", 0, NULL, 'h'},
	{0, 0, 0, 0}
};

int systype;
hw_t hw_op;

void print_help(void)
{
	printf("led-ctl-daemonls:\n");
	printf("\t[--type|-t 2U8-STANDARD|2U8-ATOM|3U16-STANDARD|3U16-SIMPLE]\n");
	printf("\t[--clean|-c]\n");
	printf("\t[--help|-h]\n");
}

int main(int argc, char *argv[])
{
	int c, fd;
	int shmid, semid;
	struct flock lock;
	int diskpw_flag = 0;
	lock.l_type = F_WRLCK;
	lock.l_start = 0;
	lock.l_whence = SEEK_SET;
	lock.l_len = 0;
	lock.l_pid = getpid();
		
	if (argc < 2) {
		print_help();
		return -1;
	}
	openlog("led-ctl-daemon", LOG_NDELAY|LOG_PID|LOG_CONS|LOG_PERROR, LOG_DAEMON);
	if ((fd=open(LOCK_FILE, O_RDWR|O_CREAT, 0644)) < 0) {
		syslog(LOG_INFO, "create lock file failed.\n");
		return -1;
	}
	

	if ((fcntl(fd, F_SETLK, &lock)) < 0) {
		syslog(LOG_ERR, "get file lock failed. eixting...\n");
		return -1;
	}
	if (open(SHMKEY, O_RDWR|O_CREAT, 0644) < 0) {
		syslog(LOG_ERR, "create shmkey file %s failed.\n", SHMKEY);
		return -1;
	}
	while ((c = getopt_long(argc, (char *const*)argv, short_options,
				long_options, NULL)) != -1) {
		switch (c){
		case 't':
			if (!strcmp(optarg, "3U16-SIMPLE")){
				systype = SYS_S3U;
				hw_op.init = i2c_init_3U;
				hw_op.set = i2c_write_disk_3U;
				hw_op.release = i2c_release_3U;
				diskpw_flag = 1;
				break;
			} else if (!strcmp(optarg, "2U8-STANDARD")) {
				systype = SYS_2U;
				hw_op.init = i2c_init_2U;
				hw_op.set = i2c_write_disk_2U;
				hw_op.release = i2c_release_2U;
				break;
			} else if (!strcmp(optarg, "2U8-ATOM")) {
				systype = SYS_A2U;
				hw_op.init = i2c_init_2U;
				hw_op.set = i2c_write_disk_2U;
				hw_op.release = i2c_release_2U;
				break;
			} else if (!strcmp(optarg, "3U16-STANDARD")) {
				systype = SYS_3U;
				hw_op.init = NULL;
				hw_op.set = NULL;
				hw_op.release = NULL;
				break;
			} else {
				syslog(LOG_ERR, "invalid type %s\n", optarg);
				print_help();
				return -1;
			}
			break;
		case 'c':
			goto clean;
		case 'h':
			print_help();
			return 0;
		default:
			print_help();
			return -1;
		}
	}
	
	semid = sem_init();
	if (semid < 0)
		goto quit;
	shmid = shm_init();
	if (shmid < 0)
		goto quit;
	if (systype == SYS_3U)
		return 0;
	if (hw_op.init() < 0) {
		goto quit;
	}
	if (diskpw_flag) {
		if (i2c_init_diskpw() < 0)
			goto quit;
	}	
	if (worker_init() < 0)
		goto quit;
	worker_release();

	
clean:
	shm_release();
	if (hw_op.release)
		hw_op.release();
	lock.l_type = F_UNLCK;
	fcntl(fd, F_SETLK, &lock);
	unlink(LOCK_FILE);
	syslog(LOG_INFO, "exited.\n");
	return 0;
quit:
	shm_release();
	if (hw_op.release)
		hw_op.release();
	lock.l_type = F_UNLCK;
	fcntl(fd, F_SETLK, &lock);
	unlink(LOCK_FILE);
	syslog(LOG_INFO, "error quit.\n");
	return -1;
}
