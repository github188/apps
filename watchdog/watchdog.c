#include <unistd.h>
#include "watchdog_lib.h"

#define WATCHDOG_FEED_INTERVAL	10
int main(void)
{
	while (1) {
		if (watchdog_enable() < 0) {
			sleep(3);
			continue;
		}

		while (watchdog_feed() >= 0) 
			sleep(WATCHDOG_FEED_INTERVAL);
	}
	return 0;
}
