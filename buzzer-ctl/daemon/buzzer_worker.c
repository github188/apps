#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "common.h"
#include "AlarmSW.h"


extern shm_t *addr;

void worker_init(void)
{
	buzzer_task_t *taskp = &addr->task;
	unsigned int freq_alert[]={  
		489,410,0
	};  
	unsigned int time_alert[]={  
		20,40  
	};
	while (1) {
		if (taskp->mode & MODE_ON) {
			if (taskp->time == TIME_FOREVER) {
				play(freq_alert, time_alert);
			} else {
				int i;
				for (i=0; i < taskp->time; i++)
					play(freq_alert, time_alert);
				taskp->time = 0;
				Stop();
			}
		} else if (taskp->mode & MODE_OFF) {
			Stop();
		} else if (taskp->mode & MODE_FORCE_OFF) {
			Stop();
		}
		usleep(10000);
	}
}

