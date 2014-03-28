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
int (*pic_write_disk_gen)(int, int);

void print_help(void)
{
	printf("led-ctl-daemonls:\n");
	printf("\t[--type|-t 2U8-STANDARD|2U8-ATOM|3U16-STANDARD|3U16-SIMPLE]\n");
	printf("\t[--clean]\n");
	printf("\t[--help|-h]\n");
}

int main(int argc, char *argv[])
{
	int c, fd;
	int shmid;
	struct flock lock;
	lock.l_type = F_WRLCK;
	lock.l_start = 0;
	lock.l_whence = SEEK_SET;
	lock.l_len = 0;
	lock.l_pid = getpid();
		
	if (argc < 2) {
		print_help();
		return -1;
	}
	if ((fd=open(LOCK_FILE, O_RDWR|O_CREAT, 0644)) < 0) {
		syslog(LOG_INFO, "create lock file failed.\n");
		return -1;
	}
	

	if ((fcntl(fd, F_SETLK, &lock)) < 0) {
		syslog(LOG_ERR, "get file lock failed. eixting...\n");
		fprintf(stderr, "get file lock failed. exiting...\n");
		return -1;
	}

	while ((c = getopt_long(argc, (char *const*)argv, short_options,
				long_options, NULL)) != -1) {
		switch (c){
		case 't':
			if (!strcmp(optarg, "3U16-SIMPLE")){
				systype = SYS_S3U;
				pic_write_disk_gen = i2c_write_disk_3U;
				break;
			} else if (!strcmp(optarg, "2U8-STANDARD")) {
				systype = SYS_2U;
				pic_write_disk_gen = i2c_write_disk_2U;
				break;
			} else if (!strcmp(optarg, "2U8-ATOM")) {
				systype = SYS_A2U;
				pic_write_disk_gen = i2c_write_disk_2U;
				break;
			} else if (!strcmp(optarg, "3U16-STANDARD")) {
				systype = SYS_3U;
				break;
			} else {
				syslog(LOG_ERR, "led_ctl: invalid type %s\n", optarg);
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
	
	shmid = shm_init();
	if (shmid < 0)
		return -1;
	if (systype == SYS_3U)
		return 0;
	if (worker_init() < 0)
		return -1;

	worker_release();
clean:
	shm_release();
	lock.l_type = F_UNLCK;
	fcntl(fd, F_SETLK, &lock);
	unlink(LOCK_FILE);
	return 0;
}
