#include <stdbool.h>
#include <syslog.h>

#ifndef __SYS_GLOBAL_H__
#define __SYS_GLOBAL_H__

#define SYS_MON_CONF "/opt/jw-conf/system/sysmon-conf.xml"

#define _LOG_OPT (LOG_CONS)
#define log_init() openlog("sys-mon", _LOG_OPT, LOG_DAEMON)
#define log_release() closelog()


typedef struct _sys_global sys_global_t;
struct _sys_global {
	bool tmpfs;
	struct {
		int info, warning, error;
	} recent;
};

void sys_mon_conf_check();
void sys_mon_load_conf();

#endif/*__SYS_GLOBAL_H__*/
