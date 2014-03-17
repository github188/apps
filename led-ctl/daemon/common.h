#ifndef COMMON__H__
#define COMMON__H__

#define SHMKEY		"/usr/local/bin"

#define DISK_NUM_NONE	0
#define DISK_NUM_3U	16
#define DISK_NUM_2U	8

#define SYS_NONE	0
#define SYS_3U		1
#define SYS_2U		2
#define SYS_S3U		4

#define DISK_ID_NONE	-1
#define DISK_ID_ALL	-2

#define MODE_NONE       0
#define MODE_ON		1
#define MODE_OFF	2
#define MODE_BLINK	4

#define FREQ_NONE	0
#define FREQ_FAST	1
#define FREQ_NORMAL	2
#define FREQ_SLOW	4

#define COUNT_FAST	1
#define COUNT_NORMAL	4
#define COUNT_SLOW	8

#define TIME_FOREVER	-200

#define VERSION	"0.0.1"
#define MAGIC   0x01234567

typedef struct led_task led_task_t;
struct led_task {
	int mode;
	long time;
	int freq;
	int count;
};

typedef struct shm_head shm_head_t;
struct shm_head {
	char version[8];
	unsigned int magic;
	int disk_num;
};

typedef struct shm_struct shm_t;
struct shm_struct {
	int sys;
	shm_head_t shm_head;
	led_task_t task[0];
};
#endif // COMMON__H__
