#ifndef COMMON__H__
#define COMMON__H__

#define SHMKEY		"/var/run/led.shmkey"
#define LOCK_FILE       "/var/run/led-ctl-daemon.lock"

#define DISK_NUM_3U	16
#define DISK_NUM_2U	8

#define SYS_NONE	0
#define SYS_3U		1
#define SYS_2U		2
#define SYS_A2U		4
#define SYS_S3U		8

#define DISK_ID_NONE	-1
#define DISK_ID_ALL	-2

#define MODE_OFF	1
#define MODE_ON		2
#define MODE_BLINK	4
#define MODE_FORCE_OFF  8

#define FREQ_NONE	0
#define FREQ_FAST	8
#define FREQ_NORMAL	2
#define FREQ_SLOW	1

#define COUNT_FAST	1
#define COUNT_NORMAL	4
#define COUNT_SLOW	8

#define POWER_OFF 	0
#define POWER_ON 	1
#define POWER_RESET 	2
#define POWER_NOSET 	4

#define TIME_FOREVER	-200

#define VERSION	0x101
#define MAGIC   0x01234567

typedef struct hw_style {
	int (*init)(void);
	int (*set)(int);
	void (*release) (void);
}hw_t;

typedef struct power_status power_status_t;
struct power_status {
	int mode;
	long time;
};
typedef struct led_task led_task_t;
struct led_task {
	int mode;
	long time;
	int freq;
	int count;
	power_status_t power;
};

typedef struct shm_head shm_head_t;
struct shm_head {
	unsigned int version;
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
