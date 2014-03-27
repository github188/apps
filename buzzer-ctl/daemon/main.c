#include <stdio.h>
#include <syslog.h>
#include <getopt.h>
#include <string.h>
#include "common.h"
#include "buzzer_shm.h"
#include "buzzer_worker.h"

char *l_opt_arg;
char *const short_options = "c:h";
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
	int c;
	int shmid;

	while ((c = getopt_long(argc, (char *const*)argv, short_options,
				long_options, NULL)) != -1) {
		switch (c){
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
	worker_init();



clean:	
	shm_release();
	return 0;
}
