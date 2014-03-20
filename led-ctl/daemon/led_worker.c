#include <stdio.h>
#include <sys/time.h>
#include <unistd.h>
#include <signal.h>
#include "common.h"
#include "led_worker.h"
#include "i2c_dev.h"
#include "sysled.h"


extern shm_t *addr;
extern int disk_max_num;
extern int (*pic_write_disk_gen)(int, int);
static int sts[DISK_NUM_3U + 1];
static volatile int go=0;

static void timer_cb(int signo)
{
	if (signo != SIGALRM)
		return ;
	go = 1;
}

void do_work(void)
{
	led_task_t *taskp = NULL;
	int i;

	taskp = &addr->task[0];
#ifdef _DEBUG
	printf("sysled mode: %d\n", taskp->mode);
#endif // _DEBUG
	/* 检查系统灯 */
	if (taskp->mode & MODE_ON) {
		sb_gpio28_set(true);
	} else if (taskp->mode & MODE_OFF) {
		sb_gpio28_set(false);
	}
	for (i=0; i < disk_max_num; i++) {
		taskp = &addr->task[i+1];
#ifdef _DEBUG
		printf("led: %d mode: %d freq: %d  time: %d count: %d",
		       i+1, taskp->mode, taskp->freq, taskp->time, taskp->count);
#endif // _DEBUG
		if (taskp->mode & MODE_ON) {
			if (pic_write_disk_gen(i, I2C_LED_ON) != 0) {
				fprintf(stderr, "led on disk %d failed.\n", i);
			}
		} else if (taskp->mode & MODE_OFF) {
			if (pic_write_disk_gen(i, I2C_LED_OFF) != 0) {
				fprintf(stderr, "led off disk %d failed.\n", i);
			} 
		} else if (taskp->mode & MODE_BLINK) {
			if (taskp->freq == FREQ_NONE) {
				fprintf(stderr, "disk %d freq not set.\n", i);
				continue;
			} 
			if (taskp->count == 0) {
				if (pic_write_disk_gen(i, sts[i+1]) != 0) {
					fprintf(stderr, "blink disk %d failed.\n", i);
				}
				sts[i+1] = (sts[i+1] + 1) % 2;
				if (taskp->freq  & FREQ_FAST) {
					taskp->count = COUNT_FAST;
				} else if (taskp->freq & FREQ_NORMAL) {
					taskp->count = COUNT_NORMAL;
				} else if (taskp->freq & FREQ_SLOW) {
					taskp->count = COUNT_SLOW;
				}
			}
			if (taskp->count > 0) 
				taskp->count--;
		}
		if (taskp->time != TIME_FOREVER) {
			taskp->time = taskp->time - WORKER_TIMER;
			if (taskp->time <= 0) {
				taskp->mode = MODE_OFF;
				pic_write_disk_gen(i, I2C_LED_OFF);
			}
		}
	}
	go = 0;
}

int worker_init(void)
{
	struct itimerval value;
	value.it_value.tv_sec = 0;
	value.it_value.tv_usec = WORKER_TIMER;
	value.it_interval.tv_sec = 0;
	value.it_interval.tv_usec = WORKER_TIMER;

	if (setitimer(ITIMER_REAL, &value, NULL) < 0) {
		fprintf(stderr, "Setitimer failed.\n");
		return -1;
	}
	signal(SIGALRM, timer_cb);
	while (1) {
		pause();
		do_work();
	}
}

void worker_release(void)
{
	signal(SIGALRM, SIG_DFL);
}
