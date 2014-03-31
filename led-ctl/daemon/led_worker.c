#include <stdio.h>
#include <syslog.h>
#include <stdint.h>
#include <sys/time.h>
#include <unistd.h>
#include <signal.h>
#include "common.h"
#include "led_worker.h"
#include "i2c_dev.h"
#include "sysled.h"

extern shm_t *addr;
extern int disk_max_num;
extern hw_t hw;
static sts_t sts[DISK_NUM_3U + 1];
static int count[DISK_NUM_3U +1];
static volatile int go = 0;
static volatile int quit = 0;
static volatile int j = 0;
static int mode;

static void timer_cb(int signo)
{
	if (signo == SIGALRM) {
		go = 1;
	}
}

static void sig_quit(int signo)
{
	if (signo == SIGTERM || signo == SIGINT) {
		quit = 1;
	}
}

void do_work(void)
{
	led_task_t *taskp = NULL;
	int i;
	int n = 0;
	int flag = 0;

	for (i=0; i < disk_max_num; i++) {
		taskp = &addr->task[i+1];
		if (taskp->mode & MODE_ON) {
			if (sts[i+1].mode & MODE_ON)
				continue;
			else {
				flag = 1;
				mode = mode & ~(1 << i);
			}
		} else if (taskp->mode & MODE_OFF) {
			if (sts[i+1].mode & MODE_OFF)
				continue;
			else {
				flag = 1;
				mode = mode | (1 << i);
				count[i+1] = 0;
			}
		} else if (taskp->mode & MODE_BLINK) {
			if (taskp->freq > n)
				n = taskp->freq;
			if (taskp->freq == FREQ_NONE) {
				syslog(LOG_ERR, "led_ctl: disk %d freq not set.\n", i+1);
				continue;
			}
			if (count[i+1] > 0)  {
				if (j)
					count[i+1] = count[i+1] - 8/j;
				else
					count[i+1] = count[i+1] - 8;
			}
			if (count[i+1] <= 0) {
				if (sts[i+1].mode & MODE_ON) {
					sts[i+1].mode = MODE_OFF;
					flag = 1;
					mode = mode | (1 << i);
				} else {
					sts[i+1].mode = MODE_ON;
					flag = 1;
					mode = mode & ~(1 << i);
				}
				count[i+1]=taskp->count;
			} 
#ifdef _DEBUG			
			printf("led: %d mode: %d freq: %d  time: %ld count: %d\n",
			       i+1, taskp->mode, taskp->freq, taskp->time, count[i+1]);
#endif
		}

		if (taskp->time != TIME_FOREVER) {
			if (j)
				taskp->time = taskp->time - WORKER_TIMER * (8/j);
			else
				taskp->time = taskp->time - WORKER_TIMER * 8;
			if (taskp->time <= 0) {
				sts[i+1].mode = MODE_OFF;
				flag = 1;
				mode = mode | (1 << i);
			}
		}
		    
	}
	if (flag) {
		if (hw.set(mode) < 0) {
			syslog(LOG_ERR, "led_ctl: set mode failed'\n");
			quit = 1;
		}
	}
	go = 0;
	j = n;
}

int worker_init(void)
{
	struct itimerval value;
	int freq=0;
	value.it_value.tv_sec = 1;
	value.it_value.tv_usec = 0;
	value.it_interval.tv_sec = 1;
	value.it_interval.tv_usec = 0 ;

	if (setitimer(ITIMER_REAL, &value, NULL) < 0) {
		syslog(LOG_ERR, "led_ctl: Setitimer failed.\n");
		return -1;
	}
	signal(SIGALRM, timer_cb);
	signal(SIGINT, sig_quit);
	signal(SIGTERM, sig_quit);
	syslog(LOG_INFO, "led_ctl:init done.\n");
	while (1) {
		pause();
		if (go) {
			do_work();
			if (freq != j) {
				value.it_value.tv_sec = 0;
				value.it_value.tv_usec = 0;
				value.it_interval.tv_usec = 0;
				value.it_interval.tv_sec = 0;
				if (setitimer(ITIMER_REAL, &value, NULL) < 0) {
					syslog(LOG_ERR, "led_ctl:clean timer failed.\n");
					return -1;
				}

				switch (j) {
				case FREQ_NORMAL:
					value.it_value.tv_usec = WORKER_TIMER * 4;
					value.it_interval.tv_usec = WORKER_TIMER * 4;
					break;
				case FREQ_NONE: 
				case FREQ_SLOW: 
					value.it_value.tv_sec = 1;
					value.it_interval.tv_sec = 1;
					break;
				default:
					value.it_value.tv_usec = WORKER_TIMER;
					value.it_interval.tv_usec = WORKER_TIMER;
					break;
				}
				if (setitimer(ITIMER_REAL, &value, NULL) < 0) {
					syslog(LOG_ERR, "led_ctl: reset setitimer failed.\n");
					return -1;
				}

				freq = j;
			}
#ifdef _DEBUG
			printf("now timer tv_sec: %d tv_usec: %d freq: %d\n", (int)value.it_interval.tv_sec,
			       (int)value.it_interval.tv_usec, freq);
#endif		
		}
		if (quit) {
			if (hw.set(0xffff) != 0) {
				syslog(LOG_ERR, "led_ctl: exitting led off  disk failed.\n");
			}
			return 0;
		}
	}
}

void worker_release(void)
{
	signal(SIGALRM, SIG_DFL);
}

