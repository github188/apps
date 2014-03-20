#include <stdio.h>
#include <getopt.h>
#include <string.h>
#include "common.h"
#include "led_shm.h"
#include "led_worker.h"
#include "i2c_dev.h"

char *l_opt_arg;
char *const short_options = "t:c:h";
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
	if (worker_init() < 0)
		return -1;

	worker_release();
clean:	
	shm_release();
	return 0;
}
