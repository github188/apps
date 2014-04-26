#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/sem.h>
#include <getopt.h>
#include <string.h>
#include "diskpower.h"

#define SEM_FILE "/usr/local/bin/diskpower-ctl"

static int id;
static int mode;
static int time;
static int flag = 0;
char *const short_options = "i:m:r:h";
struct option long_options[] = {
	{"id", 1, NULL, 'i'},
	{"mode", 1, NULL, 'm'},
	{"reset", 1, NULL, 'r'},
	{"help", 0, NULL, 'h'},
	{0, 0, 0, 0},
};

int d_p(int semid)
{
	struct sembuf sem_p;
	sem_p.sem_num = 0;
	sem_p.sem_op = -1;
	if (semop(semid, &sem_p, 1) == -1) {
		fprintf(stderr, "p failed.\n");
		return -1;
	}
	return 0;
}

int d_v(int semid)
{
	struct sembuf sem_v;
	sem_v.sem_num = 0;
	sem_v.sem_op = 1;
	if (semop(semid, &sem_v, 1) == -1) {
		fprintf(stderr, "v failed.\n");
		return -1;
	}
	return 0;
}

void print_help(void)
{
	fprintf(stderr, "diskpower-ctl:\n");
	fprintf(stderr, "\t--id|-i <1-16> --mode|-m on|off\n");
	fprintf(stderr, "\t--id|-i <1-16> --reset|-r <delayTimer>\n");
	fprintf(stderr, "\t--help|-h\n");
}
int parse_args(int argc, char **argv)
{
	int c;

	while ((c = getopt_long(argc, (char *const *)argv,  short_options,
					long_options, NULL)) != -1) {
		switch (c) {
			case 'i':
				id = atoi(optarg);
				break;
			case 'm':
				flag = 1;
				if (!strcmp(optarg, "on")) {
					mode = I2C_DISKPW_ON;
				} else if (!strcmp(optarg, "off")) {
					mode = I2C_DISKPW_OFF;
				} else {
					fprintf(stderr, "mode invalid.\n");
					return -1;
				}
				break;
			case 'r':
				time = atoi(optarg);
				break;
			case 'h':
				print_help();
				return -1;
			default:
				print_help();
				return -1;
		}
	}
	return 0;
}

int main(int argc, char *argv[])
{
	int old = 0;
	int new = 0;
	int stats = 0;
	static int semid;
	key_t semkey;

	if (argc != 5) {
		print_help();
		return -1;
	}

	if (parse_args(argc, argv) < 0) {
		return -1;
	}	
	if (id <= 0 || id > 16 ) {
		print_help();
		return -1;
	}

	if (fopen(SEM_FILE, "w+") < 0) {
		fprintf(stderr, "create sem_file %s failed.\n", SEM_FILE);
		return -1;
	}
	semkey = ftok(SEM_FILE, 0);
	semid = semget(semkey, 0, 0666);
	if (semid < 0) {
		semid = semget(semkey, 1, 0666|IPC_CREAT);
		if (semid == -1) {
			fprintf(stderr, "create sem failed.\n");
			return -1;
		}
		union semnu {
			int val;
			struct semid_ds *buf;
			ushort *array;
		}sem_u;

		sem_u.val = 1;
		semctl(semid, 0, SETVAL, sem_u);
	}
	
	d_p(semid);
	if (i2c_init_diskpw() < 0) {
		fprintf(stderr, "i2c init failed.\n");
		d_v(semid);
		return -1;
	}
	d_v(semid);

	if (flag) {
		d_p(semid);
		old = i2c_read_diskpw();
		if (old < 0) {
			fprintf(stderr, "i2c read failed.\n");
			d_v(semid);
			return -1;
		}

		if (mode == I2C_DISKPW_ON)
			new = old | (1 << (id-1));
		else
			new = old & ~(1 << (id-1));

		if (i2c_write_diskpw(new) < 0) {
			fprintf(stderr, "i2c write failed.\n");
			d_v(semid);
			return -1;
		}
		d_v(semid);
		return 0;
	}
	if (time) {
		d_p(semid);
		old = i2c_read_diskpw();
		if (old < 0) {
			fprintf(stderr, "i2c read failed.\n");
			d_v(semid);
			return -1;
		}
	
		stats = (old & (1 << (id-1))) == 0 ? I2C_DISKPW_OFF :
			I2C_DISKPW_ON;
		new = old & ~(1 << (id-1));
		
		if (i2c_write_diskpw(new) < 0) {
			fprintf(stderr, "i2c reset failed.\n");
			d_v(semid);
			return -1;
		}
		d_v(semid);

		usleep(time*1000000);

		d_p(semid);
		old = i2c_read_diskpw();
		if (old < 0) {
			fprintf(stderr, "i2c read failed.\n");
			d_v(semid);
			return -1;
		}
		
		if (stats == I2C_DISKPW_ON)
			new = old | (1 << (id-1));
		else
			new = old & ~(1 << (id-1));
		
		if (i2c_write_diskpw(new) < 0) {
			fprintf(stderr, "i2c reset failed.\n");
			d_v(semid);
			return -1;
		}
		d_v(semid);
		return 0;
	}

}
