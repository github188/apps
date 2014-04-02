#ifndef COMMON__H__
#define COMMON__H__

#define SHMKEY		"/usr/local"
#define LOCK_FILE       "/tmp/.buzzer-ctl-daemon.lock"

#define MODE_ON		1
#define MODE_OFF	2
#define MODE_FORCE_OFF  4

#define VERSION		0x101
#define MAGIC		0x123

typedef struct buzzer_task buzzer_task_t;
struct buzzer_task {
	int mode;
	int count;
};

typedef struct shm_head shm_head_t;
struct shm_head {
	unsigned int version;
	unsigned int magic;
};

typedef struct shm_struct shm_t;
struct shm_struct {
	shm_head_t shm_head;
	buzzer_task_t task;
};
#endif // COMMON__H__
