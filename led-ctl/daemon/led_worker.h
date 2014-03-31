#ifndef LED_WORKER__H__
#define LED_WORKER__H__

#include "common.h"
#define WORKER_TIMER 125000
typedef struct {
	unsigned int mode: 4;
	unsigned int now_mode :4;
}sts_t;

int worker_init(void);
void worker_release(void);


#endif // LED_WORKER__H__
