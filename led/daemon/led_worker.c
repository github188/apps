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
extern hw_t hw_op;
static sts_t sts[DISK_NUM_3U + 1];
static int count[DISK_NUM_3U +1];
static volatile int go = 0;
static volatile int quit = 0;
static volatile int j = 0;
static int mode;
static unsigned int power_old = 0;

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
			if (sts[i+1].mode & MODE_ON) {
				count[i+1] = 0;
				continue;
			}
			else {
				flag = 1;
				mode = mode & ~(1 << i);
				sts[i+1].mode = MODE_ON;
				sts[i+1].now_mode = MODE_OFF;
				count[i+1] = 0;
			}
		} else if (taskp->mode & MODE_OFF) {
			if (sts[i+1].mode & MODE_OFF) {
				count[i+1] = 0;
				continue;
			} else {
				flag = 1;
				mode = mode | (1 << i);
				sts[i+1].mode = MODE_OFF;
				sts[i+1].now_mode = MODE_OFF;
				count[i+1] = 0;
			}
		} else if (taskp->mode & MODE_BLINK) {
			if (taskp->freq > n)
				n = taskp->freq;
			if (taskp->freq == FREQ_NONE) {
				syslog(LOG_ERR, "disk %d freq not set.\n", i+1);
				continue;
			}
			sts[i+1].mode = MODE_BLINK;
			if (count[i+1] > 0)  {
				if (j)
					count[i+1] = count[i+1] - 8/j;
				else
					count[i+1] = count[i+1] - 8;
			}
			if (count[i+1] <= 0) {
				if (sts[i+1].now_mode & MODE_ON) {
					sts[i+1].now_mode = MODE_OFF;
					flag = 1;
					mode = mode | (1 << i);
				} else {
					sts[i+1].now_mode = MODE_ON;
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
				sts[i+1].now_mode = MODE_OFF;
				count[i+1] = 0;
				flag = 1;
				mode = mode | (1 << i);
			}
		}

	}
	if (flag) {
		if (hw_op.set(mode) < 0) {
			syslog(LOG_ERR, "set mode failed'\n");
			quit = 1;
		}
	}

	/*简易3U磁盘上下电功能*/
	if (addr->sys & SYS_S3U) {
		power_status_t *ppower=NULL;
		int new;
		
		new = power_old;
		for(i=0; i<DISK_NUM_3U; i++) {
			ppower = &addr->task[i+1].power;
			
			if (ppower->mode == POWER_NOSET) {
				continue;
			} else if (ppower->mode == POWER_ON) {
				if (ppower->time > 0) {
					if (j)
						ppower->time -= WORKER_TIMER * (8/j);
					else
						ppower->time -= WORKER_TIMER * 8;

				} else {
					new = new | (1 << i);
					ppower->time = 0;
				}
			} else if (ppower->mode == POWER_OFF) {
				new = new & ~(1 << i);
			} else if (ppower->mode == POWER_RESET) {
						
				if (ppower->time > 0) {
					new = new & ~(1 << i);
						if (j)
							ppower->time -= WORKER_TIMER * (8/j);
						else
							ppower->time -= WORKER_TIMER * 8;

				} else {
					new = new | (1 << i);
					ppower->mode = POWER_ON;
					ppower->time = 0;
				}
			}
		}
		if (new != power_old) {
			if (i2c_write_diskpw(new) < 0) {
				syslog(LOG_ERR, "set disk power failed.\n");
				quit = 1;
			}
			power_old = new;	
		}
#ifdef _DEBUG
		printf("old: %d\t new: %d\n", power_old, new);
#endif
	}

#ifdef _DEBUG
	printf("sys:%d\n\nversion:%d\nmagic:%d\ndisknum:%d\n\n",addr->sys,addr->shm_head.version,
		addr->shm_head.magic, addr->shm_head.disk_num);
	for (i=0; i <= disk_max_num; i++) {
		printf("%d mode:%d\ttime:%ld\tfreq:%d\tcount:%d\n",i, addr->task[i].mode, addr->task[i].time,
			addr->task[i].freq, addr->task[i].count);
	}
	printf("\n");
	for (i=1; i <= disk_max_num; i++) {
		printf("%d mode:%d\ttime:%ld\n", i, addr->task[i].power.mode, addr->task[i].power.time);
	}
#endif
 
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
		syslog(LOG_ERR, "Setitimer failed.\n");
		return -1;
	}
	signal(SIGALRM, timer_cb);
	signal(SIGINT, sig_quit);
	signal(SIGTERM, sig_quit);
	syslog(LOG_INFO, "init done.\n");
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
					syslog(LOG_ERR, "clean timer failed.\n");
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
					syslog(LOG_ERR, "reset setitimer failed.\n");
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
			if (hw_op.set(0xffff) != 0) {
				syslog(LOG_ERR, "exitting led off  disk failed.\n");
			}
			return 0;
		}
	}
}

void worker_release(void)
{
	signal(SIGALRM, SIG_DFL);
}

