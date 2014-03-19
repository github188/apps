#include <stdio.h>
#include <getopt.h>
#include <string.h>
#include "common.h"
#include "led_shm.h"
#include "led_worker.h"
#include "i2c_dev.h"

char *l_opt_arg;
char *const short_options = "c:t:h";
struct option long_options[] = {
	{"clean", 0, NULL, 'c'},
	{"type", 1, NULL, 't'},
	{"help", 0, NULL, 'h'},
	{0, 0, 0, 0}
};

int disk_max_num;
int flag = 0;
int (*pic_write_disk_gen)(int, int);

void print_help(void)
{
	printf("led_server:\n");
	printf("\t[--type|-t 2U|S3U|3U]\n");
	printf("\t[--clean]\n");
	printf("\t[--help|-h]\n");
}

int main(int argc, char *argv[])
{
	int c;
	int shmid;

	if (argc < 2) {
		print_help();
		return -1;
	}
	
	while ((c = getopt_long(argc, (char *const*)argv, short_options,
				long_options, NULL)) != -1) {
		switch (c){
		case 't':
			if (!strcmp(optarg, "S3U")){
				disk_max_num = DISK_NUM_3U;
				pic_write_disk_gen = i2c_write_disk_3U;
				break;
			} else if (!strcmp(optarg, "2U")) {
				disk_max_num = DISK_NUM_2U;
				pic_write_disk_gen = i2c_write_disk_2U;
				break;
			} else if (!strcmp(optarg, "3U")) {
				disk_max_num = DISK_NUM_3U;
				flag = 1;
				shmid = shm_init();
				if (shmid < 0)
					return -1;
				return 0;
			} else {
				fprintf(stderr, "invalid type %s\n", optarg);
				print_help();
				return -1;
			}
			break;
		case 'c':
			goto clean;
		default:
			print_help();
			return -1;
		}
	}
	
	shmid = shm_init();
	if (shmid < 0)
		return -1;
	worker_init();

	worker_release();
clean:	
	shm_release();
	return 0;
}
