#include <stdio.h>
#include <signal.h>
#include <stdlib.h>
#include <unistd.h>
#include "common.h"
#include "AlarmSW.h"


extern shm_t *addr;
static volatile int quit = 0;
static volatile int flag = 0;

static void sig_quit(int signo)
{
	if (signo == SIGTERM || signo == SIGINT) {
		quit = 1;
	}
}

void worker_init(void)
{
	buzzer_task_t *taskp = &addr->task;
	unsigned int freq_alert[]={  
		489,410,0
	};  
	unsigned int time_alert[]={  
		20,40  
	};

	signal(SIGINT, sig_quit);
	signal(SIGTERM, sig_quit);

	while (1) {
		if (quit) {
			Stop();
			return ;
		}
		if (taskp->mode & MODE_ON) {
			flag = 1;
			play(freq_alert, time_alert);
		} else if (taskp->mode & MODE_OFF) {
			if (flag) {
				Stop();
				flag = 0;
			} else {
				sleep(1);
			}

		} else if (taskp->mode & MODE_FORCE_OFF) {
			if (flag) {
				Stop();
				flag = 0;
			} else {
				sleep(1);
			}
		}
		usleep(10000);
	}
}

